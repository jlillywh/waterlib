"""
Components module for waterlib

This module contains all the water simulation components that can be used
in waterlib models. Each component inherits from the Component base class
and implements specific water resources modeling functionality.

Core Components:
- Catchment: Rainfall-runoff with integrated Snow17 + AWBM kernels
- Reservoir: Water storage with integrated spillway
- Demand: Water extraction (municipal or agricultural)
- Pump: Flow control (constant or variable)
- RiverDiversion: River flow diversion
- Junction: Flow aggregation
- LaggedValue: Feedback loop breaker
"""

# Component classes
from waterlib.components.reservoir import Reservoir
from waterlib.components.demand import Demand
from waterlib.components.junction import Junction
from waterlib.components.logic import LaggedValue
from waterlib.components.pump import Pump
from waterlib.components.catchment import Catchment
from waterlib.components.diversion import RiverDiversion

# Backward compatibility alias
DemandNode = Demand

# Component registry for factory instantiation
COMPONENT_REGISTRY = {
    "Reservoir": Reservoir,
    "DemandNode": DemandNode,
    "Demand": Demand,
    "Junction": Junction,
    "LaggedValue": LaggedValue,
    "Pump": Pump,
    "Catchment": Catchment,
    "RiverDiversion": RiverDiversion,
}


def get_component_registry():
    """Get the component registry for factory instantiation.

    Returns:
        Dictionary mapping component type strings to component classes
    """
    return COMPONENT_REGISTRY.copy()


__all__ = [
    "COMPONENT_REGISTRY",
    "get_component_registry",
    "Reservoir",
    "DemandNode",
    "Demand",
    "Junction",
    "LaggedValue",
    "Pump",
    "Catchment",
    "RiverDiversion",
]
