"""
Evapotranspiration (ET) Calculation Kernels.

This module contains pure computational algorithms for calculating reference
evapotranspiration (ET0) using various methods. Currently implements:
- Hargreaves-Samani method (temperature-based)

Future methods can be added:
- Penman-Monteith (full energy balance)
- Priestley-Taylor (simplified energy balance)

All kernels are pure functions with no dependencies on the graph structure.
"""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class HargreavesETParams:
    """
    Fixed parameters for Hargreaves-Samani ET calculation.

    Attributes:
        latitude_deg: Site latitude in degrees (required for solar radiation)
        coefficient: Hargreaves coefficient (typically 0.0023)
    """
    latitude_deg: float
    coefficient: float = 0.0023


@dataclass
class HargreavesETInputs:
    """
    Inputs for one Hargreaves-Samani ET calculation.

    Attributes:
        tmin_c: Minimum daily temperature (deg C)
        tmax_c: Maximum daily temperature (deg C)
        day_of_year: Day of year (1-366)
    """
    tmin_c: float
    tmax_c: float
    day_of_year: int


@dataclass
class ETOutputs:
    """
    Outputs from ET calculation.

    Attributes:
        et0_mm: Reference evapotranspiration (mm/day)
    """
    et0_mm: float


def hargreaves_et(
    inputs: HargreavesETInputs,
    params: HargreavesETParams
) -> ETOutputs:
    """
    Calculate reference evapotranspiration using Hargreaves-Samani method.

    The Hargreaves-Samani method estimates daily reference evapotranspiration (ET0)
    using only temperature data and latitude. The formula is:

    ET0 = C_H * R_a * (T_mean + 17.8) * sqrt(T_max - T_min)

    Where:
    - C_H is the Hargreaves coefficient (typically 0.0023)
    - R_a is extraterrestrial radiation (MJ/m²/day)
    - T_mean is the mean daily temperature (°C)
    - T_max and T_min are daily max and min temperatures (°C)

    Pure function with no side effects.

    Args:
        inputs: Current timestep inputs (tmin, tmax, day of year)
        params: Fixed parameters (latitude, coefficient)

    Returns:
        ETOutputs with calculated et0_mm

    References:
        Hargreaves, G.H. and Samani, Z.A. (1985). Reference crop evapotranspiration
        from temperature. Applied Engineering in Agriculture, 1(2), 96-99.
    """
    # Calculate mean temperature
    tmean = (inputs.tmin_c + inputs.tmax_c) / 2.0

    # Calculate temperature range, clamping to zero if tmin > tmax
    trange = max(0.0, inputs.tmax_c - inputs.tmin_c)

    # Calculate extraterrestrial radiation
    ra = _calculate_ra(inputs.day_of_year, params.latitude_deg)

    # Calculate ET0 using Hargreaves-Samani equation
    # ET0 = C_H * R_a * (T_mean + 17.8) * sqrt(T_range)
    # Result is in mm/day (R_a in MJ/m²/day, coefficient dimensionless)
    et0_mm = params.coefficient * ra * (tmean + 17.8) * math.sqrt(trange)

    # Ensure non-negative result
    et0_mm = max(0.0, et0_mm)

    return ETOutputs(et0_mm=et0_mm)


def _calculate_ra(day_of_year: int, latitude_deg: float) -> float:
    """
    Calculate extraterrestrial radiation (R_a) for a given day and latitude.

    This implements the FAO-56 method for calculating daily extraterrestrial
    radiation based on latitude and day of year.

    Args:
        day_of_year: Day of year (1-366)
        latitude_deg: Site latitude in degrees

    Returns:
        Extraterrestrial radiation in MJ/m²/day

    References:
        Allen, R.G., Pereira, L.S., Raes, D., and Smith, M. (1998).
        Crop evapotranspiration - Guidelines for computing crop water requirements.
        FAO Irrigation and drainage paper 56. FAO, Rome.
    """
    # Convert latitude to radians
    latitude_rad = math.radians(latitude_deg)

    # Solar constant
    Gsc = 0.0820  # MJ/m²/min

    # Inverse relative distance Earth-Sun
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)

    # Solar declination (radians)
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)

    # Sunset hour angle (radians)
    ws = math.acos(-math.tan(latitude_rad) * math.tan(delta))

    # Extraterrestrial radiation (MJ/m²/day)
    ra = (24 * 60 / math.pi) * Gsc * dr * (
        ws * math.sin(latitude_rad) * math.sin(delta) +
        math.cos(latitude_rad) * math.cos(delta) * math.sin(ws)
    )

    return max(0.0, ra)  # Ensure non-negative
