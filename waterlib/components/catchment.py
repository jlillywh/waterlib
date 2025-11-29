"""
Catchment component for waterlib.

This module provides the Catchment component which integrates Snow17 and AWBM
to simulate rainfall-runoff with snow accumulation and melt processes.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError
from waterlib.kernels.hydrology.snow17 import (
    snow17_step, Snow17Params, Snow17State, Snow17Inputs, Snow17Outputs
)
from waterlib.kernels.hydrology.awbm import (
    awbm_step, AWBMParams, AWBMState, AWBMInputs, AWBMOutputs
)


class Snow17ParamsConfig(BaseModel):
    """Pydantic model for Snow17 parameters."""
    mfmax: float = Field(1.6, gt=0, description="Maximum melt factor")
    mfmin: float = Field(0.6, gt=0, description="Minimum melt factor")
    mbase: float = Field(0.0, description="Base temperature for melt")
    pxtemp1: float = Field(0.0, description="Lower temperature threshold for rain/snow")
    pxtemp2: float = Field(1.0, description="Upper temperature threshold for rain/snow")
    scf: float = Field(1.0, gt=0, description="Snow correction factor")
    nmf: float = Field(0.15, ge=0, description="Negative melt factor")
    plwhc: float = Field(0.04, ge=0, le=1, description="Percent liquid water holding capacity")
    uadj: float = Field(0.05, ge=0, description="Wind function adjustment")
    tipm: float = Field(0.15, ge=0, le=1, description="Temperature index parameter")
    lapse_rate: float = Field(0.006, ge=0, description="Temperature lapse rate (°C/m)")
    ref_elevation: Optional[float] = Field(None, description="Reference elevation for temperature adjustment (if different from site)")
    initial_swe: float = Field(0.0, ge=0, description="Initial snow water equivalent")


class AWBMParamsConfig(BaseModel):
    """Pydantic model for AWBM parameters."""
    c_vec: List[float] = Field(..., min_length=3, max_length=3, description="Capacity values [C1, C2, C3] in mm")
    bfi: float = Field(0.35, ge=0, le=1, description="Baseflow index")
    ks: float = Field(0.35, ge=0, le=1, description="Surface recession constant")
    kb: float = Field(0.95, ge=0, le=1, description="Baseflow recession constant")
    a1: float = Field(0.134, ge=0, le=1, description="Partial area fraction 1")
    a2: float = Field(0.433, ge=0, le=1, description="Partial area fraction 2")
    initial_stores: Optional[Union[List[float], Dict[str, float]]] = Field(
        None,
        description="Initial state: list [ss1, ss2, ss3, s_surf, b_base] or dict"
    )

    @field_validator('c_vec')
    @classmethod
    def validate_c_vec_positive(cls, v):
        """Ensure all capacity values are positive."""
        if any(c <= 0 for c in v):
            raise ValueError("All c_vec values must be positive")
        return v


class CatchmentConfig(BaseModel):
    """Pydantic configuration model for Catchment component."""
    area: Optional[float] = Field(None, gt=0, description="Catchment area in km² (alternative to area_km2)")
    area_km2: Optional[float] = Field(None, gt=0, description="Catchment area in km²")
    snow17_params: Optional[Snow17ParamsConfig] = Field(None, description="Snow17 parameters (None to skip snow)")
    snow_params: Optional[Snow17ParamsConfig] = Field(None, description="Alias for snow17_params")
    awbm_params: AWBMParamsConfig = Field(..., description="AWBM parameters (required)")

    @field_validator('awbm_params', mode='before')
    @classmethod
    def convert_awbm_dict(cls, v):
        """Convert dict to AWBMParamsConfig if needed."""
        if isinstance(v, dict):
            return AWBMParamsConfig(**v)
        return v

    @field_validator('snow17_params', 'snow_params', mode='before')
    @classmethod
    def convert_snow_dict(cls, v):
        """Convert dict to Snow17ParamsConfig if needed."""
        if v is None:
            return None
        if isinstance(v, dict):
            return Snow17ParamsConfig(**v)
        return v


class Catchment(Component):
    """Catchment component with integrated snow and rainfall-runoff modeling.

    This component combines Snow17 (snow accumulation and melt) with AWBM
    (Australian Water Balance Model) to simulate complete catchment hydrology.
    Snow17 processes precipitation and temperature to generate snowmelt, which
    is then combined with rainfall and routed through AWBM to produce runoff.

    The component accepts climate inputs from DriverRegistry and outputs runoff
    volume and snow water equivalent.

    Parameters:
        area: Catchment area in square kilometers (required)
        snow17_params: Dictionary of Snow17 parameters (optional, None to skip snow)
            - latitude: Latitude in degrees
            - elevation: Elevation in meters (single value or list)
            - ref_elevation: Reference elevation for temperature adjustment
            - Other Snow17 parameters (mfmax, mfmin, scf, etc.)
        awbm_params: Dictionary of AWBM parameters (required)
            - c_vec: List of three capacity values [C1, C2, C3] in mm
            - bfi: Baseflow index (0-1)
            - ks: Surface recession constant (0-1)
            - kb: Baseflow recession constant (0-1)
            - initial_stores: Optional initial state (5 values)

    Inputs (from DriverRegistry):
        precipitation: Daily precipitation in mm
        temperature: Daily mean temperature in degrees C
        et: Potential evapotranspiration in mm

    Outputs:
        runoff: Daily runoff volume in m³/day
        runoff_mm: Daily runoff depth in mm
        snow_water_equivalent: Snow water equivalent in mm
        swe_mm: Alias for snow_water_equivalent

    Example YAML:
        upper_catchment:
          type: Catchment
          params:
            area: 150.0
            snow17_params:
              latitude: 45.0
              elevation: 1500.0
              ref_elevation: 1000.0
              mfmax: 1.2
              scf: 1.1
            awbm_params:
              c_vec: [7.5, 76.0, 152.0]
              bfi: 0.35
              ks: 0.35
              kb: 0.95
    """

    def __init__(self, name: str, **params):
        """Initialize Catchment component.

        Args:
            name: Unique component identifier
            **params: Component parameters (automatically validated by CatchmentConfig)
                     Special parameter: _site (SiteConfig) - passed by loader, not from YAML

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        # Extract site config before passing to parent (not a component parameter)
        self._site = params.pop('_site', None)

        super().__init__(name, **params)

        # Validate all parameters using Pydantic model
        try:
            config = CatchmentConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"Catchment '{name}' configuration error: {e}"
            )

        # Extract area (support both 'area' and 'area_km2')
        self.area = config.area_km2 if config.area_km2 is not None else config.area
        if self.area is None:
            raise ConfigurationError(
                f"Catchment '{name}' missing required parameter 'area' or 'area_km2'"
            )

        # Determine which snow params to use (support both aliases)
        snow_config = config.snow17_params or config.snow_params
        self.has_snow = snow_config is not None

        # Create kernel parameter objects for Snow17 (if enabled)
        if self.has_snow:
            self.snow17_params = Snow17Params(
                mfmax=snow_config.mfmax,
                mfmin=snow_config.mfmin,
                mbase=snow_config.mbase,
                pxtemp1=snow_config.pxtemp1,
                pxtemp2=snow_config.pxtemp2,
                scf=snow_config.scf,
                nmf=snow_config.nmf,
                plwhc=snow_config.plwhc,
                uadj=snow_config.uadj,
                tipm=snow_config.tipm,
                lapse_rate=snow_config.lapse_rate
            )

            # Get latitude and elevation from site configuration
            if self._site is None:
                raise ConfigurationError(
                    f"Catchment '{name}' with Snow17 requires site configuration. "
                    f"Add a 'site:' block with latitude and elevation_m to your YAML."
                )

            self.latitude = self._site.latitude
            self.elevation = self._site.elevation_m
            self.ref_elevation = snow_config.ref_elevation or self.elevation

            # Initialize Snow17 state
            self.snow17_state = Snow17State(
                w_i=snow_config.initial_swe,
                w_q=0.0,
                ait=0.0,
                deficit=0.0
            )
        else:
            self.snow17_params = None
            self.snow17_state = None

        # Create kernel parameter objects for AWBM
        awbm_config = config.awbm_params

        self.awbm_params = AWBMParams(
            c_vec=awbm_config.c_vec,
            bfi=awbm_config.bfi,
            ks=awbm_config.ks,
            kb=awbm_config.kb,
            a1=awbm_config.a1,
            a2=awbm_config.a2
        )

        # Initialize AWBM state
        initial_stores = awbm_config.initial_stores
        if initial_stores is None:
            # Default: all stores start empty
            self.awbm_state = AWBMState(
                ss1=0.0, ss2=0.0, ss3=0.0, s_surf=0.0, b_base=0.0
            )
        elif isinstance(initial_stores, list):
            # List format: [ss1, ss2, ss3, s_surf, b_base]
            self.awbm_state = AWBMState(
                ss1=initial_stores[0] if len(initial_stores) > 0 else 0.0,
                ss2=initial_stores[1] if len(initial_stores) > 1 else 0.0,
                ss3=initial_stores[2] if len(initial_stores) > 2 else 0.0,
                s_surf=initial_stores[3] if len(initial_stores) > 3 else 0.0,
                b_base=initial_stores[4] if len(initial_stores) > 4 else 0.0
            )
        else:
            # Dictionary format
            self.awbm_state = AWBMState(
                ss1=initial_stores.get('ss1', 0.0),
                ss2=initial_stores.get('ss2', 0.0),
                ss3=initial_stores.get('ss3', 0.0),
                s_surf=initial_stores.get('s_surf', 0.0),
                b_base=initial_stores.get('b_base', 0.0)
            )

        # Initialize outputs
        self.outputs['runoff'] = 0.0
        self.outputs['runoff_mm'] = 0.0
        self.outputs['snow_water_equivalent'] = 0.0
        self.outputs['swe_mm'] = 0.0

    def step(self, date: datetime, drivers) -> dict:
        """Execute one timestep of catchment simulation.

        This method:
        1. Retrieves climate data from drivers (DriverRegistry)
        2. Runs Snow17 kernel to partition precip into rain/snow and calculate melt (if enabled)
        3. Runs AWBM kernel with rainfall + snowmelt to generate runoff
        4. Returns component outputs

        Args:
            date: Current simulation date
            drivers: DriverRegistry instance providing climate data

        Returns:
            Dictionary of output values for this timestep
        """
        # Get climate inputs from DriverRegistry using type-safe API
        # New API: drivers.climate.precipitation instead of drivers.get('precipitation')
        try:
            precip = drivers.climate.precipitation.get_value(date)
            temp = drivers.climate.temperature.get_value(date)
            pet = drivers.climate.et.get_value(date)
        except AttributeError as e:
            self.logger.warning(
                f"Failed to get climate data from drivers at {date}: {e}. Using zeros."
            )
            precip = 0.0
            temp = 0.0
            pet = 0.0

        # Step 1: Run Snow17 kernel to partition precipitation and calculate melt (if enabled)
        if self.has_snow:
            # Prepare Snow17 inputs
            day_of_year = date.timetuple().tm_yday
            is_leap_year = (date.year % 4 == 0 and date.year % 100 != 0) or (date.year % 400 == 0)
            days_in_year = 366 if is_leap_year else 365

            snow17_inputs = Snow17Inputs(
                temp_c=temp,
                precip_mm=precip,
                elevation_m=self.elevation,
                ref_elevation_m=self.ref_elevation,
                day_of_year=day_of_year,
                days_in_year=days_in_year,
                dt_hours=24.0,
                latitude=self.latitude
            )

            # Call Snow17 kernel
            self.snow17_state, snow17_outputs = snow17_step(
                snow17_inputs, self.snow17_params, self.snow17_state
            )

            # Extract Snow17 outputs
            snowmelt_mm = snow17_outputs.runoff_mm
            rainfall_mm = snow17_outputs.rain_mm
            swe_mm = snow17_outputs.swe_mm

            # Effective precipitation is rainfall + snowmelt
            effective_precip = rainfall_mm + snowmelt_mm
        else:
            # Skip snow processing: all precipitation goes directly to AWBM
            effective_precip = precip
            swe_mm = 0.0

        # Step 2: Run AWBM kernel with effective precipitation
        awbm_inputs = AWBMInputs(
            precip_mm=effective_precip,
            pet_mm=pet
        )

        # Call AWBM kernel
        self.awbm_state, awbm_outputs = awbm_step(
            awbm_inputs, self.awbm_params, self.awbm_state
        )

        # Convert runoff from mm to m³/day
        runoff_mm = awbm_outputs.runoff_mm
        runoff_m3d = runoff_mm * self.area * 1000.0  # area is in km², convert to m²

        # Update outputs
        self.outputs['runoff'] = runoff_m3d
        self.outputs['runoff_mm'] = runoff_mm
        self.outputs['snow_water_equivalent'] = swe_mm
        self.outputs['swe_mm'] = swe_mm

        return self.outputs.copy()
