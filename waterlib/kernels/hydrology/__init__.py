"""
Hydrology kernels for waterlib.

This module contains pure computational algorithms for hydrological processes
including snow accumulation, rainfall-runoff transformation, and runoff generation.

Available kernels:
    - Snow17: Snow accumulation and melt algorithm
    - AWBM: Australian Water Balance Model for rainfall-runoff
    - Runoff generation utilities

All kernels follow the pure function pattern:
    kernel_function(inputs, params, state) -> (new_state, outputs)
"""

from waterlib.kernels.hydrology.snow17 import (
    snow17_step,
    Snow17Params,
    Snow17State,
    Snow17Inputs,
    Snow17Outputs
)

from waterlib.kernels.hydrology.awbm import (
    awbm_step,
    AWBMParams,
    AWBMState,
    AWBMInputs,
    AWBMOutputs
)

__all__ = [
    'snow17_step',
    'Snow17Params',
    'Snow17State',
    'Snow17Inputs',
    'Snow17Outputs',
    'awbm_step',
    'AWBMParams',
    'AWBMState',
    'AWBMInputs',
    'AWBMOutputs'
]
