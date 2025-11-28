"""
Climate kernels for waterlib.

This module contains pure computational algorithms for climate-related
calculations including evapotranspiration methods and stochastic weather
generation.

Available kernels:
    - ET: Evapotranspiration calculations (Hargreaves-Samani, Penman-Monteith)
    - WGEN: Stochastic weather generator

All kernels follow the pure function pattern:
    kernel_function(inputs, params, state) -> (new_state, outputs)
"""

from waterlib.kernels.climate.et import (
    hargreaves_et,
    HargreavesETParams,
    HargreavesETInputs,
    ETOutputs
)

from waterlib.kernels.climate.wgen import (
    wgen_step,
    estimate_wgen_params,
    WGENParams,
    WGENState,
    WGENOutputs
)

__all__ = [
    'hargreaves_et',
    'HargreavesETParams',
    'HargreavesETInputs',
    'ETOutputs',
    'wgen_step',
    'estimate_wgen_params',
    'WGENParams',
    'WGENState',
    'WGENOutputs'
]
