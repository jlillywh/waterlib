"""
Reservoir component for waterlib.

This module provides the Reservoir component which models water storage with
mass balance tracking and integrated spillway logic.

The component supports two modes:
1. Simple mode: Constant surface area, no elevation tracking
2. EAV mode: Elevation-Area-Volume table for realistic reservoir geometry
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError
from waterlib.utils.interpolation import (
    interpolate_elevation_from_volume,
    interpolate_area_from_volume
)
from waterlib.kernels.hydraulics.weir import (
    spillway_discharge,
    WeirParams,
    WeirInputs
)


class ReservoirConfig(BaseModel):
    """Pydantic configuration model for Reservoir component.

    This model handles automatic validation and type coercion for all
    reservoir parameters, replacing manual validation in __init__.
    """
    initial_storage: float = Field(
        ...,
        ge=0,
        description="Starting storage in cubic meters"
    )
    max_storage: float = Field(
        ...,
        gt=0,
        description="Maximum reservoir capacity in cubic meters"
    )
    surface_area: Optional[float] = Field(
        None,
        ge=0,
        description="Water surface area in square meters (simple mode)"
    )
    spillway_elevation: Optional[float] = Field(
        None,
        description="Spillway crest elevation in meters"
    )
    spillway_width: float = Field(
        10.0,
        gt=0,
        description="Spillway width in meters"
    )
    spillway_coefficient: float = Field(
        1.7,
        gt=0,
        description="Spillway discharge coefficient"
    )
    eav_table: Optional[str] = Field(
        None,
        description="Path to EAV table CSV file (elevation, area, volume)"
    )

    @model_validator(mode='after')
    def validate_storage_constraint(self):
        """Ensure initial storage doesn't exceed max storage."""
        if self.initial_storage > self.max_storage:
            raise ValueError(
                f"initial_storage ({self.initial_storage}) cannot exceed "
                f"max_storage ({self.max_storage})"
            )
        return self

    @model_validator(mode='after')
    def validate_spillway_requires_eav(self):
        """Spillway elevation requires EAV table for elevation tracking."""
        if self.spillway_elevation is not None and self.eav_table is None:
            raise ValueError(
                "spillway_elevation requires eav_table for elevation tracking. "
                "Simple mode with spillway_elevation is not supported."
            )
        return self


class Reservoir(Component):
    """Storage component with integrated spillway logic.

    The Reservoir component maintains water storage using mass balance,
    with automatic spillway overflow when storage exceeds maximum capacity.
    Evaporation losses are optional and calculated based on surface area.

    Two modes are supported:
    1. Simple mode: Constant surface_area parameter
    2. EAV mode: Elevation-Area-Volume table from CSV file

    Parameters:
        initial_storage: Starting storage in cubic meters (required)
        max_storage: Maximum reservoir capacity in cubic meters (required)
        surface_area: Water surface area in square meters (optional, for simple mode)
        spillway_elevation: Spillway crest elevation in meters (optional)
        spillway_width: Spillway width in meters (optional, default=10.0)
        spillway_coefficient: Spillway discharge coefficient (optional, default=1.7)
        eav_table: Path to EAV table CSV file (optional, for EAV mode)
                   CSV must have columns: elevation, area, volume

    Inputs (from connections or global_data):
        inflow: Incoming flow in m³/day
        release: Controlled release in m³/day
        evaporation: Evaporation rate in mm/day (optional, from global_data)

    Outputs:
        storage: Current storage in m³
        outflow: Total outflow (release + spill) in m³/day
        spill: Spillway overflow in m³/day
        evaporation_loss: Evaporation loss in m³/day (if surface_area or eav_table)
        elevation: Water surface elevation in m (only in EAV mode)
        area: Water surface area in m² (only in EAV mode)

    Example YAML (Simple mode):
        main_reservoir:
          type: Reservoir
          params:
            initial_storage: 1000000
            max_storage: 5000000
            surface_area: 500000
            spillway_elevation: 100
            spillway_width: 15.0
            spillway_coefficient: 1.7

    Example YAML (EAV mode):
        main_reservoir:
          type: Reservoir
          params:
            initial_storage: 1000000
            max_storage: 5000000
            eav_table: data/reservoir_eav.csv
            spillway_elevation: 100
            spillway_width: 15.0
            spillway_coefficient: 1.7
    """

    def __init__(self, name: str, **params):
        """Initialize Reservoir component.

        Args:
            name: Unique component identifier
            **params: Component parameters (automatically validated by ReservoirConfig)

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        super().__init__(name, **params)

        # Extract _yaml_dir before validation (meta-parameter for path resolution)
        yaml_dir = params.pop('_yaml_dir', None)

        # Validate all parameters using Pydantic model
        try:
            config = ReservoirConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"Reservoir '{name}' configuration error: {e}"
            )

        # Store validated parameters
        self.initial_storage = config.initial_storage
        self.max_storage = config.max_storage
        self.surface_area = config.surface_area
        self.spillway_elevation = config.spillway_elevation

        # Load EAV table if provided
        self.eav_table: Optional[pd.DataFrame] = None
        self.use_eav_mode = config.eav_table is not None

        if self.use_eav_mode:
            # Resolve relative path if yaml_dir is provided
            eav_path = Path(config.eav_table)
            if not eav_path.is_absolute() and yaml_dir is not None:
                eav_path = (yaml_dir / eav_path).resolve()

            # Load EAV table from CSV
            try:
                self.eav_table = pd.read_csv(eav_path)
            except FileNotFoundError:
                raise ConfigurationError(
                    f"Reservoir '{name}' cannot find EAV table file: {config.eav_table}"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Reservoir '{name}' error loading EAV table '{config.eav_table}': {e}"
                )

            # Validate EAV table has required columns
            required_columns = ['elevation', 'area', 'volume']
            missing_columns = [col for col in required_columns
                             if col not in self.eav_table.columns]
            if missing_columns:
                raise ConfigurationError(
                    f"Reservoir '{name}' EAV table missing required columns: {missing_columns}. "
                    f"Available columns: {list(self.eav_table.columns)}"
                )

            # Sort EAV table by volume to ensure interpolation works correctly
            self.eav_table = self.eav_table.sort_values('volume').reset_index(drop=True)

            # Initialize current area and elevation from EAV table
            self.current_area = interpolate_area_from_volume(
                self.eav_table,
                self.initial_storage
            )
            self.current_elevation = interpolate_elevation_from_volume(
                self.eav_table,
                self.initial_storage
            )
        else:
            # Simple mode: Use constant surface_area if provided
            self.current_area = self.surface_area
            self.current_elevation = None

        # Configure spillway parameters using weir kernel
        self.spillway_params: Optional[WeirParams] = None
        if self.spillway_elevation is not None:
            self.spillway_params = WeirParams(
                coefficient=config.spillway_coefficient,
                width_m=config.spillway_width,
                crest_elevation_m=self.spillway_elevation
            )

        # Initialize state
        self.storage = self.initial_storage

        # Initialize outputs
        self.outputs['storage'] = self.storage
        self.outputs['outflow'] = 0.0
        self.outputs['spill'] = 0.0

        # Add elevation and area outputs in EAV mode
        if self.use_eav_mode:
            self.outputs['elevation'] = self.current_elevation
            self.outputs['area'] = self.current_area

        # Add evaporation_loss output if we can calculate evaporation
        if self.current_area is not None:
            self.outputs['evaporation_loss'] = 0.0

    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep of reservoir simulation.

        This method:
        1. Gets inflow and release from inputs
        2. Calculates evaporation loss (if surface_area specified)
        3. Updates storage using mass balance
        4. Calculates spillway overflow if storage exceeds max_storage
        5. Returns outputs

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data

        Returns:
            Dictionary of output values for this timestep
        """
        # Get inflows (sum all indexed inflows: inflow_1, inflow_2, etc.)
        inflow = 0.0
        for key, value in self.inputs.items():
            if key.startswith('inflow_'):
                inflow += float(value)

        # Also check for legacy 'inflow' key for backward compatibility
        if 'inflow' in self.inputs:
            inflow += float(self.inputs['inflow'])

        # Get release from inputs
        release = float(self.inputs.get('release', 0.0))

        # Ensure non-negative inputs
        inflow = max(0.0, inflow)
        release = max(0.0, release)

        # Calculate evaporation loss if we have area information
        # Use current area (from previous timestep or initialization)
        evaporation_loss = 0.0
        if self.current_area is not None:
            # Get evaporation rate from global_data (mm/day)
            evap_rate_mm = float(global_data.get('evaporation', 0.0))
            # Convert to volume: mm/day * m² / 1000 = m³/day
            evaporation_loss = (evap_rate_mm * self.current_area) / 1000.0
            evaporation_loss = max(0.0, evaporation_loss)

        # Mass balance: new_storage = current_storage + inflow - release - evaporation
        new_storage = self.storage + inflow - release - evaporation_loss

        # Ensure storage doesn't go negative
        if new_storage < 0:
            # Not enough water to meet release + evaporation
            # Reduce actual release to what's available
            available = self.storage + inflow
            actual_release = max(0.0, available - evaporation_loss)
            if actual_release < 0:
                actual_release = 0.0
                evaporation_loss = available
            new_storage = 0.0
            release = actual_release

        # Calculate spillway discharge using weir kernel if configured
        spill = 0.0

        if self.spillway_params is not None and self.use_eav_mode:
            # Calculate elevation for current storage (before spillway)
            temp_elevation = interpolate_elevation_from_volume(
                self.eav_table,
                new_storage
            )

            # Use weir kernel to calculate spillway discharge
            weir_inputs = WeirInputs(water_elevation_m=temp_elevation)
            weir_outputs = spillway_discharge(weir_inputs, self.spillway_params)

            # Spillway discharge is in m³/day
            spill = weir_outputs.discharge_m3d

            # Reduce storage by spillway discharge
            new_storage = new_storage - spill

            # Ensure storage doesn't go negative due to spillway
            if new_storage < 0:
                spill = spill + new_storage  # Reduce spill by the deficit
                new_storage = 0.0
        else:
            # Fallback to simple overflow logic when no spillway configured
            # or when not using EAV mode
            if new_storage > self.max_storage:
                spill = new_storage - self.max_storage
                new_storage = self.max_storage

        # Update state
        self.storage = new_storage

        # Update elevation and area if using EAV mode (after storage update)
        if self.use_eav_mode:
            self.current_elevation = interpolate_elevation_from_volume(
                self.eav_table,
                self.storage
            )
            self.current_area = interpolate_area_from_volume(
                self.eav_table,
                self.storage
            )

        # Calculate total outflow
        outflow = release + spill

        # Update outputs
        self.outputs['storage'] = self.storage
        self.outputs['outflow'] = outflow
        self.outputs['spill'] = spill

        # Update EAV-specific outputs
        if self.use_eav_mode:
            self.outputs['elevation'] = self.current_elevation
            self.outputs['area'] = self.current_area

        # Update evaporation loss if applicable
        if self.current_area is not None:
            self.outputs['evaporation_loss'] = evaporation_loss

        return self.outputs.copy()
