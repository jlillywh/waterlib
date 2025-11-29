"""
Demand component for waterlib.

This module provides the Demand component which simulates water extraction
with municipal or agricultural modes.
"""

from typing import Dict, Any, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError


class DemandConfig(BaseModel):
    """Pydantic configuration model for Demand component.

    Validates parameters for municipal or agricultural water demand modes.
    """
    mode: Literal['municipal', 'agricultural'] = Field(
        ...,
        description="Demand calculation mode: 'municipal' or 'agricultural'"
    )

    # Municipal mode parameters
    population: Optional[float] = Field(
        None,
        ge=0,
        description="Population count for municipal mode"
    )
    per_capita_demand_lpd: Optional[float] = Field(
        None,
        ge=0,
        description="Per capita water demand in L/person/day (municipal mode)"
    )
    indoor_demand: Optional[float] = Field(
        None,
        ge=0,
        description="Deprecated alias for per_capita_demand_lpd"
    )
    outdoor_area: float = Field(
        default=0.0,
        ge=0,
        description="Outdoor irrigated area in hectares (municipal mode)"
    )
    outdoor_coefficient: float = Field(
        default=0.8,
        ge=0,
        description="Landscape coefficient for outdoor irrigation (municipal mode)"
    )

    # Agricultural mode parameters
    irrigated_area: Optional[float] = Field(
        None,
        ge=0,
        description="Irrigated area in hectares (agricultural mode)"
    )
    crop_coefficient: Optional[float] = Field(
        None,
        ge=0,
        description="Crop coefficient (Kc) for agricultural mode"
    )

    @field_validator('mode', mode='before')
    @classmethod
    def normalize_mode(cls, v: str) -> str:
        """Normalize mode to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v

    @model_validator(mode='after')
    def validate_mode_specific_params(self):
        """Validate that required parameters are present for each mode."""
        if self.mode == 'municipal':
            # Require population
            if self.population is None:
                raise ValueError("municipal mode requires 'population' parameter")

            # Require either per_capita_demand_lpd or indoor_demand
            if self.per_capita_demand_lpd is None and self.indoor_demand is None:
                raise ValueError("municipal mode requires 'per_capita_demand_lpd' parameter")

            # Sync deprecated indoor_demand with per_capita_demand_lpd
            if self.per_capita_demand_lpd is None and self.indoor_demand is not None:
                self.per_capita_demand_lpd = self.indoor_demand
            elif self.indoor_demand is None and self.per_capita_demand_lpd is not None:
                self.indoor_demand = self.per_capita_demand_lpd

        elif self.mode == 'agricultural':
            # Require irrigated_area and crop_coefficient
            if self.irrigated_area is None:
                raise ValueError("agricultural mode requires 'irrigated_area' parameter")
            if self.crop_coefficient is None:
                raise ValueError("agricultural mode requires 'crop_coefficient' parameter")

        return self


class Demand(Component):
    """Water extraction component with municipal or agricultural modes.

    The Demand component calculates water demand based on the selected mode
    and tracks supply/deficit. It accepts available supply as input and
    outputs the calculated demand, actual supply delivered, and any deficit.

    Modes:
    1. Municipal: Population-based demand with indoor and outdoor components
       - Indoor demand = population × per_capita_demand_lpd (L/person/day) / 1000 (m³/day)
       - Outdoor demand = outdoor_area (ha) × outdoor_coefficient × ET0 (mm/day) × 10 (m³/day)
       - Total demand = indoor_demand + outdoor_demand

    2. Agricultural: Irrigated area and crop coefficient based
       - Demand = irrigated_area (ha) × crop_coefficient × ET0 (mm/day) × 10 (m³/day)

    Parameters:
        mode: 'municipal' or 'agricultural' (required)

        Municipal mode parameters:
            population: Population count (required)
            per_capita_demand_lpd: Average per capita water demand in L/person/day (required)
                                   Note: 'indoor_demand' is accepted for backward compatibility
            outdoor_area: Average irrigated area per household in hectares (optional, default=0)
            outdoor_coefficient: Landscape coefficient for outdoor irrigation (optional, default=0.8)

        Agricultural mode parameters:
            irrigated_area: Irrigated area in hectares (required)
            crop_coefficient: Crop coefficient (Kc) (required)

    Inputs (from connections):
        available_supply: Available water supply in m³/day

    Inputs (from global_data):
        et0: Reference evapotranspiration in mm/day (from Hargreaves-Samani)
             Used for outdoor demand in municipal mode and all demand in agricultural mode

    Outputs:
        demand: Total calculated water demand in m³/day
        supplied: Actually supplied water in m³/day
        deficit: Unmet demand in m³/day (demand - supplied)
        indoor_demand: Indoor demand component in m³/day (municipal mode only)
        outdoor_demand: Outdoor demand component in m³/day (municipal mode only)

    Example YAML (Municipal mode with indoor only):
        city_demand:
          type: Demand
          params:
            mode: 'municipal'
            population: 50000
            per_capita_demand_lpd: 150  # L/person/day

    Example YAML (Municipal mode with indoor and outdoor):
        city_demand:
          type: Demand
          params:
            mode: 'municipal'
            population: 50000
            per_capita_demand_lpd: 150  # L/person/day
            outdoor_area: 25  # hectares of parks, lawns, etc.
            outdoor_coefficient: 0.8  # landscape coefficient

    Example YAML (Agricultural mode):
        farm_demand:
          type: Demand
          params:
            mode: 'agricultural'
            irrigated_area: 500  # hectares
            crop_coefficient: 0.8
    """

    def __init__(self, name: str, **params):
        """Initialize Demand component.

        Args:
            name: Unique component identifier
            **params: Component parameters

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        super().__init__(name, **params)

        # Validate parameters with Pydantic
        try:
            config = DemandConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"Demand '{name}' configuration error: {str(e)}"
            )

        # Store validated configuration
        self.mode = config.mode

        # Municipal mode attributes
        self.population = config.population
        self.per_capita_demand_lpd = config.per_capita_demand_lpd
        self.indoor_demand = config.indoor_demand  # Backward compatibility alias
        self.outdoor_area = config.outdoor_area
        self.outdoor_coefficient = config.outdoor_coefficient

        # Agricultural mode attributes
        self.irrigated_area = config.irrigated_area
        self.crop_coefficient = config.crop_coefficient

        # Initialize outputs
        self.outputs['demand'] = 0.0
        self.outputs['supplied'] = 0.0
        self.outputs['deficit'] = 0.0

    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep of demand calculation.

        This method:
        1. Calculates demand based on mode and parameters
        2. Gets available supply from inputs
        3. Determines actual supply (min of demand and available)
        4. Calculates deficit (demand - supplied)
        5. Returns outputs

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data

        Returns:
            Dictionary of output values for this timestep
        """
        # Calculate demand based on mode
        if self.mode == 'municipal':
            # Indoor demand: population × per_capita_demand_lpd (L/person/day) / 1000 → m³/day
            indoor = (self.population * self.per_capita_demand_lpd) / 1000.0

            # Outdoor demand: outdoor_area (ha) × outdoor_coefficient × ET0 (mm/day) × 10 → m³/day
            # Conversion: 1 ha = 10,000 m², 1 mm = 0.001 m
            # So: ha × mm = 10,000 m² × 0.001 m = 10 m³
            et0 = float(global_data.get('et0', 0.0))
            outdoor = self.outdoor_area * self.outdoor_coefficient * et0 * 10.0

            demand = indoor + outdoor

            # Store components for output
            self.outputs['indoor_demand'] = indoor
            self.outputs['outdoor_demand'] = outdoor

        elif self.mode == 'agricultural':
            # Agricultural: irrigated_area (ha) × crop_coefficient × ET0 (mm/day) × 10 → m³/day
            # Conversion: 1 ha = 10,000 m², 1 mm = 0.001 m
            # So: ha × mm = 10,000 m² × 0.001 m = 10 m³
            et0 = float(global_data.get('et0', 0.0))
            demand = self.irrigated_area * self.crop_coefficient * et0 * 10.0

        # Ensure demand is non-negative
        demand = max(0.0, demand)

        # Get available supply from inputs
        available_supply = float(self.inputs.get('available_supply', 0.0))
        available_supply = max(0.0, available_supply)

        # Determine actual supply (cannot exceed demand or available supply)
        supplied = min(demand, available_supply)

        # Calculate deficit
        deficit = demand - supplied

        # Update outputs
        self.outputs['demand'] = demand
        self.outputs['supplied'] = supplied
        self.outputs['deficit'] = deficit

        return self.outputs.copy()
