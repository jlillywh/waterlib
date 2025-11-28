"""
Snow17 - Daily Snow Accumulation and Ablation Model Kernel.

This module contains the pure computational algorithm for the NWS Snow-17 model.
It is a pure function implementation with no dependencies on the graph structure.

The Snow17 algorithm simulates snow accumulation, melt, and liquid water movement
through a snowpack using an energy balance approach with temperature index melt.

References:
    Anderson, E. A. (2006). Snow accumulation and ablation model - SNOW-17.
    NOAA's National Weather Service, Hydrology Laboratory.
"""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class Snow17Params:
    """
    Fixed parameters for Snow17 algorithm.

    Attributes:
        mfmax: Maximum melt factor (June 21) [mm/degC/6hr]
        mfmin: Minimum melt factor (Dec 21) [mm/degC/6hr]
        mbase: Base temperature for melt (deg C)
        pxtemp1: Temperature below which precip is 100% snow (deg C)
        pxtemp2: Temperature above which precip is 100% rain (deg C)
        scf: Snow correction factor for gauge undercatch (dimensionless)
        nmf: Maximum negative melt factor [mm/degC/6hr]
        plwhc: Percent liquid water holding capacity (0.0-0.4)
        uadj: Wind function for rain-on-snow [mm/mb/6hr]
        tipm: Antecedent temperature index weighting factor (0.01-1.0)
        lapse_rate: Temperature lapse rate (deg C/m)
    """
    mfmax: float = 1.6
    mfmin: float = 0.6
    mbase: float = 0.0
    pxtemp1: float = 0.0
    pxtemp2: float = 1.0
    scf: float = 1.0
    nmf: float = 0.15
    plwhc: float = 0.04
    uadj: float = 0.05
    tipm: float = 0.15
    lapse_rate: float = 0.006


@dataclass
class Snow17State:
    """
    State variables for Snow17 algorithm.

    Attributes:
        w_i: Water equivalent of ice portion of snow cover (mm)
        w_q: Liquid water held by the snow (mm)
        ait: Antecedent Temperature Index (deg C)
        deficit: Heat deficit (mm)
    """
    w_i: float = 0.0
    w_q: float = 0.0
    ait: float = 0.0
    deficit: float = 0.0


@dataclass
class Snow17Inputs:
    """
    Inputs for one Snow17 timestep.

    Attributes:
        temp_c: Air temperature (deg C)
        precip_mm: Precipitation (mm)
        elevation_m: Elevation of the zone (m)
        ref_elevation_m: Elevation of the temperature station (m)
        day_of_year: Day of year (1-366)
        days_in_year: Days in the year (365 or 366)
        dt_hours: Time step duration (hours)
        latitude: Latitude of the catchment (degrees)
    """
    temp_c: float
    precip_mm: float
    elevation_m: float
    ref_elevation_m: float
    day_of_year: int
    days_in_year: int
    dt_hours: float
    latitude: float = 45.0


@dataclass
class Snow17Outputs:
    """
    Outputs from one Snow17 timestep.

    Attributes:
        runoff_mm: Excess water (melt + rain runoff) (mm)
        swe_mm: Snow Water Equivalent (mm)
        rain_mm: Rainfall component (mm)
        snow_mm: Snowfall component (mm)
    """
    runoff_mm: float
    swe_mm: float
    rain_mm: float
    snow_mm: float


def snow17_step(
    inputs: Snow17Inputs,
    params: Snow17Params,
    state: Snow17State
) -> Tuple[Snow17State, Snow17Outputs]:
    """
    Execute one timestep of Snow17 algorithm.

    Pure function with no side effects. Calculates snow accumulation, melt,
    and liquid water movement through the snowpack.

    Args:
        inputs: Current timestep inputs (temperature, precipitation, etc.)
        params: Fixed model parameters
        state: Current state variables

    Returns:
        Tuple of (new_state, outputs) where:
            - new_state: Updated state variables
            - outputs: Calculated outputs for this timestep
    """
    # Extract state variables
    w_i = state.w_i
    w_q = state.w_q
    ait = state.ait
    deficit = state.deficit

    # Calculate timestep intervals
    dt_6hr_intervals = inputs.dt_hours / 6.0

    # --- 1. Adjust Temperature for Elevation ---
    altitude_adj = params.lapse_rate * (inputs.ref_elevation_m - inputs.elevation_m)
    t_air_mean = inputs.temp_c + altitude_adj

    # --- 2. Partition Rain / Snow ---
    frac_snow = _interpolate_temperature(
        t_air_mean, params.pxtemp1, params.pxtemp2, 1.0, 0.0
    )
    frac_rain = 1.0 - frac_snow

    rain = frac_rain * inputs.precip_mm
    pn = frac_snow * inputs.precip_mm * params.scf  # Water equivalent of new snow

    # Update ice storage with new snow
    w_i += pn

    # --- 3. Energy Exchange (ATI & Heat Deficit) ---
    t_snow_new = min(t_air_mean, 0.0)

    # Heat deficit from new snow
    delta_hd_snow = -(t_snow_new * pn) / 160.0

    # Update ATI (Antecedent Temperature Index)
    tipm_dt = 1.0 - math.pow(1.0 - params.tipm, dt_6hr_intervals)

    # If significant new snow, ATI resets to new snow temp
    timestep_threshold = 1.5 * dt_6hr_intervals

    if pn > timestep_threshold:
        ait = t_snow_new
    else:
        ait = ait + tipm_dt * (t_air_mean - ait)

    ait = min(ait, 0.0)  # ATI cannot be > 0

    # Calculate Melt Factor
    mf = _calculate_melt_factor(
        inputs.day_of_year, inputs.days_in_year, inputs.latitude,
        params.mfmax, params.mfmin, dt_6hr_intervals
    )

    # Heat deficit change from temperature gradient
    delta_hd_t = params.nmf * dt_6hr_intervals * (mf / params.mfmax) * (ait - t_snow_new)
    delta_hd_t = max(-10.0, min(delta_hd_t, 10.0))  # Clamp for stability

    # --- 4. Melt Calculation ---
    melt = 0.0

    if t_air_mean > params.mbase:
        # Check for Rain-on-Snow (ROS) conditions
        is_rain = (rain > 0.25 * inputs.dt_hours) and (t_air_mean > 0.0)

        if is_rain:
            melt = _calculate_rain_on_snow_melt(
                t_air_mean, rain, inputs.elevation_m,
                inputs.dt_hours, dt_6hr_intervals, params.uadj
            )
        else:
            # Regular Temperature Index Melt
            t_rain_energy = max(max(t_air_mean, params.pxtemp1), 0.0)
            melt = (mf * (t_air_mean - params.mbase)) + (0.0125 * rain * t_rain_energy)

        melt = max(melt, 0.0)

    # --- 5. Apply Melt and Liquid Water Balance ---
    melt_applied = min(w_i, melt)
    w_i -= melt_applied
    melt = melt_applied

    # Total Liquid Water Available
    qw = melt + rain

    # Liquid Water Capacity
    w_qx = params.plwhc * w_i

    # Update Heat Deficit
    deficit += delta_hd_snow + delta_hd_t
    deficit = max(0.0, min(deficit, 0.33 * w_i))

    # --- 6. Ripeness and Excess Water (Runoff) ---
    excess_melt = 0.0

    if w_i + w_q > 0.0:  # Snowpack exists
        water_demand_to_ripen = (deficit * (1.0 + params.plwhc)) + w_qx
        current_liquid_plus_new = w_q + qw

        if current_liquid_plus_new > water_demand_to_ripen:
            # Super-ripe: Generating runoff
            excess_melt = current_liquid_plus_new - water_demand_to_ripen
            w_q = w_qx
            w_i += deficit
            deficit = 0.0
        elif current_liquid_plus_new >= deficit:
            # Ripening: Filling pores/removing deficit, no runoff
            excess_melt = 0.0
            w_q = w_q + qw - deficit
            w_i += deficit
            deficit = 0.0
        else:
            # Cold snow: Water refreezes completely
            excess_melt = 0.0
            w_i += qw
            deficit -= qw
            # w_q remains unchanged
    else:
        # Bare ground: All input is excess
        excess_melt = qw + w_q
        w_i = 0.0
        w_q = 0.0
        deficit = 0.0

    # If deficit is 0, ATI should be 0 (isothermal)
    if deficit == 0.0:
        ait = 0.0

    # --- 7. Calculate Outputs ---
    swe = w_i + w_q

    new_state = Snow17State(
        w_i=w_i,
        w_q=w_q,
        ait=ait,
        deficit=deficit
    )

    outputs = Snow17Outputs(
        runoff_mm=excess_melt,
        swe_mm=swe,
        rain_mm=rain,
        snow_mm=pn
    )

    return new_state, outputs


# --- Helper Functions ---

def _interpolate_temperature(
    temp: float, t1: float, t2: float, v1: float, v2: float
) -> float:
    """
    Linearly interpolate value based on temperature range.

    Args:
        temp: Current temperature
        t1: Lower temperature threshold
        t2: Upper temperature threshold
        v1: Value at or below t1
        v2: Value at or above t2

    Returns:
        Interpolated value
    """
    if temp <= t1:
        return v1
    elif temp >= t2:
        return v2
    else:
        fraction = (temp - t1) / (t2 - t1)
        return v1 + fraction * (v2 - v1)


def _calculate_melt_factor(
    day_of_year: int,
    days_in_year: int,
    lat: float,
    mfmax: float,
    mfmin: float,
    dt_6hr_intervals: float
) -> float:
    """
    Calculate seasonally varying melt factor.

    The melt factor varies seasonally based on solar radiation patterns,
    with a peak around June 21 and minimum around December 21.

    Args:
        day_of_year: Day of year (1-366)
        days_in_year: Days in the year (365 or 366)
        lat: Latitude (degrees)
        mfmax: Maximum melt factor
        mfmin: Minimum melt factor
        dt_6hr_intervals: Number of 6-hour intervals in timestep

    Returns:
        Melt factor for this timestep
    """
    # Seasonality based on sine wave peaking June 21 (approx day 172)
    n = day_of_year - 80
    sv = 0.5 * math.sin((n * 2.0 * math.pi) / days_in_year) + 0.5

    # Latitude adjustment for high latitudes
    av = 1.0
    if lat >= 54.0:
        if day_of_year <= 78:
            av = 0.0
        elif day_of_year <= 116:
            av = (day_of_year - 78.0) / 38.0
        elif day_of_year <= 228:
            av = 1.0
        elif day_of_year <= 266:
            av = 1.0 - (day_of_year - 228.0) / 38.0
        else:
            av = 0.0

    return dt_6hr_intervals * ((sv * av * (mfmax - mfmin)) + mfmin)


def _calculate_rain_on_snow_melt(
    t_air: float,
    rain: float,
    elev: float,
    dt_hours: float,
    dt_6hr_int: float,
    uadj: float
) -> float:
    """
    Energy balance approximation for Rain-on-Snow events.

    Calculates melt from three energy sources:
    1. Longwave radiation exchange
    2. Heat from rain advection
    3. Turbulent transfer (sensible + latent heat)

    Args:
        t_air: Air temperature (deg C)
        rain: Rainfall amount (mm)
        elev: Elevation (m)
        dt_hours: Time step duration (hours)
        dt_6hr_int: Number of 6-hour intervals
        uadj: Wind function parameter

    Returns:
        Melt amount (mm)
    """
    t_k = t_air + 273.15

    # 1. Longwave Radiation Exchange (Stefan-Boltzmann)
    sigma = 6.12e-10
    m_ros1 = sigma * dt_hours * (math.pow(t_k, 4.0) - math.pow(273.15, 4.0))

    # 2. Heat from Rain Advection
    t_rain = max(t_air, 0.0)
    m_ros2 = 0.0125 * rain * t_rain

    # 3. Turbulent Transfer
    p_atm = _calculate_atm_pressure(elev)
    e_sat = _calculate_sat_vapor_pressure(t_air)

    term3 = (0.9 * e_sat - 6.11) + (0.00057 * p_atm * t_air)
    m_ros3 = 8.5 * uadj * dt_6hr_int * term3

    return max(m_ros1, 0.0) + max(m_ros2, 0.0) + max(m_ros3, 0.0)


def _calculate_atm_pressure(elev: float) -> float:
    """
    Calculate atmospheric pressure (mb) based on elevation (m).

    Args:
        elev: Elevation (m)

    Returns:
        Atmospheric pressure (mb)
    """
    elev_100m = elev / 100.0
    return 33.86 * (29.9 - (0.335 * elev_100m) + (0.00022 * math.pow(elev_100m, 2.4)))


def _calculate_sat_vapor_pressure(temp: float) -> float:
    """
    Calculate saturated vapor pressure (mb) for a given temperature (C).

    Args:
        temp: Temperature (deg C)

    Returns:
        Saturated vapor pressure (mb)
    """
    return 2.7489e8 * math.exp(-4278.63 / (temp + 242.792))
