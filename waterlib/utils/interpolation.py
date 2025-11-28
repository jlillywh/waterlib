"""
Interpolation utilities for waterlib.

This module provides interpolation functions for elevation-area-volume (EAV)
tables used by storage components like Reservoir.
"""

import numpy as np
import pandas as pd
from typing import Union


def interpolate_elevation_from_volume(
    eav_table: pd.DataFrame,
    volume: float
) -> float:
    """Interpolate elevation from volume using EAV table.

    Uses linear interpolation to find the elevation corresponding to a given
    volume. Handles edge cases where volume is outside the table range.

    Args:
        eav_table: DataFrame with columns ['elevation', 'area', 'volume']
        volume: Volume in cubic meters

    Returns:
        Interpolated elevation in meters

    Note:
        If volume is below the minimum table value, returns minimum elevation.
        If volume is above the maximum table value, returns maximum elevation.
    """
    volumes = eav_table['volume'].values
    elevations = eav_table['elevation'].values

    # Handle edge cases
    if volume <= volumes[0]:
        return elevations[0]
    if volume >= volumes[-1]:
        return elevations[-1]

    # Linear interpolation
    elevation = np.interp(volume, volumes, elevations)
    return float(elevation)


def interpolate_area_from_volume(
    eav_table: pd.DataFrame,
    volume: float
) -> float:
    """Interpolate surface area from volume using EAV table.

    Uses linear interpolation to find the surface area corresponding to a
    given volume. Handles edge cases where volume is outside the table range.

    Args:
        eav_table: DataFrame with columns ['elevation', 'area', 'volume']
        volume: Volume in cubic meters

    Returns:
        Interpolated surface area in square meters

    Note:
        If volume is below the minimum table value, returns minimum area.
        If volume is above the maximum table value, returns maximum area.
    """
    volumes = eav_table['volume'].values
    areas = eav_table['area'].values

    # Handle edge cases
    if volume <= volumes[0]:
        return areas[0]
    if volume >= volumes[-1]:
        return areas[-1]

    # Linear interpolation
    area = np.interp(volume, volumes, areas)
    return float(area)
