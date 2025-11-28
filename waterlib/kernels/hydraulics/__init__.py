"""
Hydraulics kernels for waterlib.

This module contains pure computational algorithms for hydraulic structures
and flow calculations including weir equations, spillway calculations, and
routing algorithms.

Available kernels:
    - Weir: Weir flow equations and discharge calculations
    - Spillway: Spillway flow calculations

All kernels follow the pure function pattern:
    kernel_function(inputs, params, state) -> (new_state, outputs)
"""

from waterlib.kernels.hydraulics.weir import (
    weir_discharge,
    spillway_discharge,
    WeirParams,
    WeirInputs,
    WeirOutputs
)

__all__ = [
    'weir_discharge',
    'spillway_discharge',
    'WeirParams',
    'WeirInputs',
    'WeirOutputs'
]
