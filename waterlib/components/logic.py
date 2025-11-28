"""
Logic components module for waterlib.

This module contains components that perform control and information processing
rather than physical water calculations. Logic components enable advanced modeling
patterns like feedback loops, conditional logic, and iterative control systems.

Components:
    LaggedValue: Provides values from the previous timestep to break circular dependencies
"""

import copy
from typing import Any, Dict
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError


class LaggedValueConfig(BaseModel):
    """Configuration validator for LaggedValue component.

    Attributes:
        source: Dot-notation reference to value source (e.g., "reservoir.elevation")
        initial_value: Seed value for timestep t=0
    """
    source: str = Field(
        ...,
        min_length=1,
        description="Dot-notation reference to the value source (e.g., 'reservoir.elevation')"
    )
    initial_value: Any = Field(
        ...,
        description="Seed value for timestep t=0 when no previous timestep exists"
    )

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate that source is not empty after stripping whitespace."""
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("source cannot be empty or whitespace-only")
        return v_stripped


class LaggedValue(Component):
    """Logic component that provides lagged values from the previous timestep.

    This component breaks circular dependencies in the model graph by storing a value
    from timestep t-1 and returning it at timestep t. This enables feedback loops where
    a component's output influences its own input through a chain of dependencies.

    The LaggedValue component works with waterlib's two-pass execution model:
    - During update(): Returns the stored value from the previous timestep
    - During finalize(): Captures the current value from the source for use in the next timestep

    This ensures that all components see consistent values during each timestep, preventing
    race conditions and maintaining mathematical correctness.

    Example Use Cases:
        - Pump control based on downstream reservoir levels
        - Treatment plant recycle streams
        - Iterative control rules that adjust based on system state

    Parameters:
        source (str): Dot-notation reference to the value source (e.g., "reservoir.elevation").
                     Format: "component_name.output_name" or "component_name" (uses first output).
        initial_value (any): Seed value for timestep t=0 when no previous timestep exists.
                            Must be provided to initialize the feedback loop.

    Outputs:
        value: The lagged value from the previous timestep

    Example YAML Configuration:
        ```yaml
        components:
          downstream_level:
            type: Reservoir
            # ... reservoir config ...

          lagged_level:
            type: LaggedValue
            source: downstream_level.elevation
            initial_value: 10.0

          pump:
            type: Weir
            control_source: lagged_level  # Uses lagged value to avoid circular dependency
            # ... pump config ...
        ```

    Notes:
        - Supports any picklable Python data type (float, bool, str, dict, list)
        - Automatically deep copies mutable types (list, dict, set) to prevent reference mutation
        - The source component reference is resolved by the loader after graph construction
        - Creates a "weak edge" in the dependency graph that is excluded from topological sorting
    """

    def __init__(self, name: str, source: str, initial_value: Any,
                 meta: Dict[str, Any] = None, **kwargs):
        """Initialize the LaggedValue component.

        Args:
            name: Unique component identifier
            source: Dot-notation reference to value source (e.g., "reservoir.elevation")
            initial_value: Seed value for timestep t=0
            meta: Optional metadata dictionary
            **kwargs: Additional parameters (ignored)

        Raises:
            ConfigurationError: If configuration validation fails
        """
        super().__init__(name, meta, **kwargs)

        # Validate configuration with Pydantic
        try:
            config = LaggedValueConfig(
                source=source,
                initial_value=initial_value
            )
        except Exception as e:
            raise ConfigurationError(f"Component '{name}' configuration error: {e}")

        # Store source string for later resolution by loader
        self._source_string = config.source

        # Deep copy initial_value if it's mutable to prevent reference mutation
        if isinstance(config.initial_value, (list, dict, set)):
            self._initial_value = copy.deepcopy(config.initial_value)
        else:
            self._initial_value = config.initial_value

        # Current value to return during this timestep's step()
        # Deep copy for mutable types
        if isinstance(self._initial_value, (list, dict, set)):
            self._current_value = copy.deepcopy(self._initial_value)
            self._previous_value = copy.deepcopy(self._initial_value)
        else:
            self._current_value = self._initial_value
            self._previous_value = self._initial_value

        # Source component reference (resolved later by loader)
        self._source_component = None
        self._source_output = None

        self.logger.info(f"Initialized {name} with initial_value={initial_value}")

    def step(self, date: datetime, global_data: dict) -> dict:
        """Return the stored value from the previous timestep and capture current value.

        This method returns the value from the previous timestep (or initial_value at t=0),
        then captures the current value from the source for use in the next timestep.

        Args:
            date: Current simulation date
            global_data: Global data dictionary (not used)

        Returns:
            Dictionary with 'value' key containing the lagged value
        """
        # Return the previous timestep's value
        # Deep copy mutable types to prevent external mutation of internal state
        if isinstance(self._previous_value, (list, dict, set)):
            self.outputs = {'value': copy.deepcopy(self._previous_value)}
        else:
            self.outputs = {'value': self._previous_value}

        # Capture current value from source for next timestep
        if self._source_component is not None:
            # Read value from source component
            if self._source_output is None:
                # No specific output specified, use first available output
                if not self._source_component.outputs:
                    value = self._initial_value
                else:
                    # Get first output value
                    first_output_key = next(iter(self._source_component.outputs))
                    value = self._source_component.outputs[first_output_key]
            else:
                # Get specific output
                value = self._source_component.outputs.get(self._source_output, self._initial_value)

            # Deep copy mutable types to prevent reference mutation
            if isinstance(value, (list, dict, set)):
                self._current_value = copy.deepcopy(value)
            else:
                self._current_value = value
        else:
            # Source not resolved yet, use initial value
            self._current_value = self._initial_value

        # Store current value for next timestep
        self._previous_value = self._current_value

        return self.outputs
