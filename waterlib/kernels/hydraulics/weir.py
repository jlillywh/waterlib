"""
Weir kernel for waterlib.

This module provides pure computational functions for weir flow calculations
using the standard weir equation for rectangular sharp-crested weirs.

The weir equation:
    Q = C × L × H^(3/2)
Where:
    Q = discharge (m³/s)
    C = discharge coefficient
    L = weir width (m)
    H = head over crest (m)
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class WeirParams:
    """Fixed parameters for weir discharge calculation.

    Attributes:
        coefficient: Discharge coefficient, typically 1.5-2.0 for sharp-crested weirs
        width_m: Weir width in meters
        crest_elevation_m: Weir crest elevation in meters
    """
    coefficient: float
    width_m: float
    crest_elevation_m: float


@dataclass
class WeirInputs:
    """Inputs for weir discharge calculation.

    Attributes:
        water_elevation_m: Current water surface elevation in meters
    """
    water_elevation_m: float


@dataclass
class WeirOutputs:
    """Outputs from weir discharge calculation.

    Attributes:
        discharge_m3s: Discharge in cubic meters per second
        discharge_m3d: Discharge in cubic meters per day
        head_m: Head over crest in meters
    """
    discharge_m3s: float
    discharge_m3d: float
    head_m: float


def weir_discharge(inputs: WeirInputs, params: WeirParams) -> WeirOutputs:
    """
    Calculate weir discharge using the standard weir equation.

    For a rectangular sharp-crested weir:
        Q = C × L × H^(3/2)

    Where:
        Q = discharge (m³/s)
        C = discharge coefficient
        L = weir width (m)
        H = head over crest (m)

    If head <= 0, discharge is zero.

    Args:
        inputs: WeirInputs containing water elevation
        params: WeirParams containing weir characteristics

    Returns:
        WeirOutputs containing discharge in m³/s and m³/d, and head

    Example:
        >>> params = WeirParams(coefficient=1.8, width_m=10.0, crest_elevation_m=100.0)
        >>> inputs = WeirInputs(water_elevation_m=101.5)
        >>> outputs = weir_discharge(inputs, params)
        >>> outputs.head_m
        1.5
        >>> outputs.discharge_m3s > 0
        True
    """
    # Calculate head over crest
    head_m = max(0.0, inputs.water_elevation_m - params.crest_elevation_m)

    if head_m > 0:
        # Apply weir equation: Q = C × L × H^1.5
        discharge_m3s = params.coefficient * params.width_m * (head_m ** 1.5)

        # Convert to m³/day
        discharge_m3d = discharge_m3s * 86400.0
    else:
        # No flow when head <= 0
        discharge_m3s = 0.0
        discharge_m3d = 0.0

    return WeirOutputs(
        discharge_m3s=discharge_m3s,
        discharge_m3d=discharge_m3d,
        head_m=head_m
    )


def spillway_discharge(inputs: WeirInputs, params: WeirParams) -> WeirOutputs:
    """
    Calculate spillway discharge using weir equation.

    This is an alias for weir_discharge() provided for semantic clarity
    when calculating spillway flows. Spillways are typically modeled as
    broad-crested weirs.

    Args:
        inputs: WeirInputs containing water elevation
        params: WeirParams containing spillway characteristics

    Returns:
        WeirOutputs containing discharge in m³/s and m³/d, and head

    Example:
        >>> params = WeirParams(coefficient=1.7, width_m=20.0, crest_elevation_m=245.0)
        >>> inputs = WeirInputs(water_elevation_m=246.0)
        >>> outputs = spillway_discharge(inputs, params)
        >>> outputs.discharge_m3s > 0
        True
    """
    return weir_discharge(inputs, params)
