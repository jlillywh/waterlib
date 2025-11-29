"""
Junction component for waterlib.

This module provides the Junction component which aggregates multiple inflows
into a single outflow point.
"""

from typing import Dict, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError


class JunctionConfig(BaseModel):
    """Pydantic configuration model for Junction component.

    Junction is a pure aggregation component with no required parameters.
    This config validates that only expected parameters are provided.
    """
    model_config = ConfigDict(extra='forbid')  # Disallow unexpected parameters


class Junction(Component):
    """Flow aggregation component.

    The Junction component represents a confluence point where multiple flows
    combine (e.g., tributary confluence, pipe junction). It sums all input
    flows to produce a single output flow.

    This is a stateless component that simply aggregates flows at each timestep.

    Parameters:
        None (pure aggregation component)

    Inputs (from connections):
        Multiple inflow inputs dynamically named (e.g., inflow_1, inflow_2, ...)
        All inputs are expected to be in m³/day

    Outputs:
        outflow: Combined flow in m³/day

    Example YAML:
        confluence:
          type: Junction

    Example connections:
        connections:
          - from: tributary_a.runoff
            to: confluence.inflow_1
          - from: tributary_b.runoff
            to: confluence.inflow_2
          - from: tributary_c.runoff
            to: confluence.inflow_3
    """

    def __init__(self, name: str, meta: Dict[str, Any] = None, **params):
        """Initialize Junction component.

        Args:
            name: Unique component identifier
            meta: Optional metadata dictionary for visualization
            **params: Component parameters (none required for Junction)

        Raises:
            ConfigurationError: If unexpected parameters are provided

        Note:
            Junction accepts any number of inputs dynamically through the
            connection system. No parameters are required.
        """
        super().__init__(name, meta=meta, **params)

        # Validate parameters with Pydantic (should have no params)
        try:
            config = JunctionConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"Junction '{name}' configuration error: {str(e)}"
            )

        # Initialize outputs
        self.outputs['outflow'] = 0.0

    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep of flow aggregation.

        This method:
        1. Sums all input flows from self.inputs
        2. Stores the total as outflow
        3. Returns outputs

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data

        Returns:
            Dictionary of output values for this timestep
        """
        # Sum all input flows
        total_flow = 0.0

        for input_name, input_value in self.inputs.items():
            # Convert to float and add to total
            flow = float(input_value)
            total_flow += flow

        # Update outputs
        self.outputs['outflow'] = total_flow

        return self.outputs.copy()
