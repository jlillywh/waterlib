"""
Computational kernels for waterlib.

This package contains pure computational algorithms organized by domain.
Kernels are pure functions with no dependencies on the graph structure or
component system. They implement core algorithms that are orchestrated by
components in waterlib.components.

Subpackages:
    hydrology: Rainfall-runoff and snow accumulation algorithms
    hydraulics: Flow structure and routing algorithms
    climate: Evapotranspiration and weather generation algorithms

Design Principles:
    - Kernels are pure functions with no side effects
    - Kernels use dataclasses for parameters, state, inputs, and outputs
    - Kernels have no knowledge of the graph structure
    - Components orchestrate kernels but don't implement core algorithms
"""

__version__ = "0.1.0"
