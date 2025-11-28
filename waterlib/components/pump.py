"""
Pump component for waterlib.

This module provides the Pump (or Valve) component which models feedback-controlled
flow based on monitoring a process variable (typically reservoir level).
"""

from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError


class PumpConfig(BaseModel):
    """Pydantic configuration model for Pump component.

    This model handles automatic validation and type coercion for all
    pump parameters, replacing manual validation in __init__.
    """
    control_mode: str = Field(
        ...,
        description="Control mode: 'deadband' or 'proportional'"
    )
    capacity: float = Field(
        ...,
        ge=0,
        description="Maximum flow rate in m³/day"
    )
    process_variable: str = Field(
        ...,
        description="Component output to monitor (format: 'component.output')"
    )
    target: Union[float, Dict[int, float]] = Field(
        ...,
        description="Constant target value or dict mapping day-of-year to target values"
    )
    deadband: Optional[float] = Field(
        None,
        ge=0,
        description="Deadband threshold (required for deadband mode)"
    )
    kp: Optional[float] = Field(
        None,
        ge=0,
        description="Proportional gain coefficient (required for proportional mode)"
    )

    @field_validator('control_mode')
    @classmethod
    def validate_control_mode(cls, v):
        """Ensure control mode is valid."""
        v_lower = v.lower()
        if v_lower not in ['deadband', 'proportional']:
            raise ValueError(
                f"control_mode must be 'deadband' or 'proportional', got '{v}'"
            )
        return v_lower

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate target schedule if dictionary."""
        if isinstance(v, dict):
            for key, value in v.items():
                day = int(key)
                if day < 1 or day > 366:
                    raise ValueError(
                        f"day-of-year must be between 1 and 366, got {day}"
                    )
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"target value must be numeric, got {type(value)}"
                    )
        return v

    @model_validator(mode='after')
    def validate_mode_specific_params(self):
        """Ensure mode-specific parameters are provided."""
        if self.control_mode == 'deadband':
            if self.deadband is None:
                raise ValueError(
                    "deadband mode requires 'deadband' parameter"
                )
        elif self.control_mode == 'proportional':
            if self.kp is None:
                raise ValueError(
                    "proportional mode requires 'kp' parameter"
                )
        return self


class Pump(Component):
    """Feedback-controlled flow component with deadband or proportional control.

    The Pump component monitors a process variable (typically reservoir depth/elevation)
    and adjusts flow to maintain a target value. The target can vary seasonally via
    a lookup table with linear interpolation.

    Control Modes:
    1. Deadband (ON/OFF): Pump operates at full capacity when error exceeds deadband
    2. Proportional: Flow is proportional to error (Flow = Kp × error)

    Parameters:
        control_mode: 'deadband' or 'proportional' (required)
        capacity: Maximum flow rate in m³/day (required)
        process_variable: Name of component output to monitor, format "component.output" (required)
        target: Fixed target value or lookup table for seasonal targets (required)
                - Float for constant target
                - Dict mapping day-of-year to target values for seasonal operation
        deadband: Deadband threshold (required for deadband mode)
        kp: Proportional gain coefficient (required for proportional mode)

    Inputs (from connections):
        process_variable: Monitored value (e.g., reservoir.storage or reservoir.elevation)

    Outputs:
        pumped_flow: Controlled flow in m³/day
        error: Control error (target - current) for diagnostics
        target_value: Current target value for diagnostics

    Example YAML (Deadband mode with constant target):
        pump_1:
          type: Pump
          params:
            control_mode: 'deadband'
            capacity: 50000
            process_variable: 'main_reservoir.elevation'
            target: 100.0
            deadband: 2.0

    Example YAML (Proportional mode with seasonal target):
        pump_2:
          type: Pump
          params:
            control_mode: 'proportional'
            capacity: 50000
            process_variable: 'main_reservoir.storage'
            target:
              1: 1000000    # Jan 1: 1,000,000 m³
              182: 1500000  # Jul 1: 1,500,000 m³
              365: 1000000  # Dec 31: 1,000,000 m³
            kp: 0.1
    """

    def __init__(self, name: str, **params):
        """Initialize Pump component.

        Args:
            name: Unique component identifier
            **params: Component parameters (automatically validated by PumpConfig)

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        super().__init__(name, **params)

        # Validate all parameters using Pydantic model
        try:
            config = PumpConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"Pump '{name}' configuration error: {e}"
            )

        # Store validated parameters
        self.control_mode = config.control_mode
        self.capacity = config.capacity
        self.process_variable = config.process_variable
        self.deadband = config.deadband
        self.kp = config.kp

        # Parse target (constant or schedule)
        if isinstance(config.target, dict):
            self.target_constant = None
            self.target_schedule = self._parse_target_schedule(config.target, name)
        else:
            self.target_constant = float(config.target)
            self.target_schedule = None

        # Initialize outputs
        self.outputs['pumped_flow'] = 0.0
        self.outputs['error'] = 0.0
        self.outputs['target_value'] = 0.0

    def _parse_target_schedule(self, schedule: dict, name: str) -> List[Tuple[int, float]]:
        """Parse and validate target schedule.

        Args:
            schedule: Dictionary mapping day-of-year to target values
            name: Component name for error messages

        Returns:
            Sorted list of (day_of_year, target_value) tuples
        """
        # Convert to list of tuples and sort (validation already done by Pydantic)
        parsed = [(int(day), float(value)) for day, value in schedule.items()]
        parsed.sort(key=lambda x: x[0])
        return parsed

    def _get_target_value(self, date: datetime) -> float:
        """Get target value for current date.

        Args:
            date: Current simulation date

        Returns:
            Target value (interpolated if using schedule)
        """
        if self.target_constant is not None:
            return self.target_constant

        # Get day of year (1-366)
        day_of_year = date.timetuple().tm_yday

        # Linear interpolation from schedule
        # Handle wrap-around for seasonal schedules
        days = [d for d, _ in self.target_schedule]
        values = [v for _, v in self.target_schedule]

        # If only one point, return that value
        if len(days) == 1:
            return values[0]

        # Find surrounding points
        if day_of_year <= days[0]:
            # Before first point - interpolate from last to first (wrap around)
            # Adjust last day to be negative for interpolation
            x = [days[-1] - 366, days[0]]
            y = [values[-1], values[0]]
            target = np.interp(day_of_year, x, y)
        elif day_of_year >= days[-1]:
            # After last point - interpolate from last to first (wrap around)
            # Adjust first day to be beyond 366 for interpolation
            x = [days[-1], days[0] + 366]
            y = [values[-1], values[0]]
            target = np.interp(day_of_year, x, y)
        else:
            # Between points - normal interpolation
            target = np.interp(day_of_year, days, values)

        return float(target)

    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep of pump operation.

        This method:
        1. Gets current process variable value
        2. Determines target value (constant or interpolated from schedule)
        3. Calculates control error (target - current)
        4. Determines pumped flow based on control mode
        5. Returns outputs

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data

        Returns:
            Dictionary of output values for this timestep
        """
        # Get current process variable value
        current_value = float(self.inputs.get(self.process_variable, 0.0))

        # Get target value for this date
        target_value = self._get_target_value(date)

        # Calculate control error (target - current)
        error = target_value - current_value

        # Determine pumped flow based on control mode
        if self.control_mode == 'deadband':
            # Deadband control: ON/OFF based on error magnitude
            if error > self.deadband:
                # Error exceeds deadband - pump at full capacity
                pumped_flow = self.capacity
            else:
                # Within deadband or negative error - pump off
                pumped_flow = 0.0

        elif self.control_mode == 'proportional':
            # Proportional control: Flow = Kp × error
            pumped_flow = self.kp * error
            # Clamp to [0, capacity]
            pumped_flow = max(0.0, min(pumped_flow, self.capacity))

        # Update outputs
        self.outputs['pumped_flow'] = pumped_flow
        self.outputs['error'] = error
        self.outputs['target_value'] = target_value

        return self.outputs
