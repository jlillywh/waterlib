"""
Core module for waterlib

This module contains the fundamental classes and functions for the waterlib
simulation framework, including the base component class, model class,
YAML loader functionality, and project scaffolding utilities.
"""

from waterlib.core.base import Component
from waterlib.core.simple_model import Model
from waterlib.core.loader import (
    load_yaml,
    load_model,
    create_component,
    instantiate_components,
    parse_dot_notation,
    build_graph,
    compute_execution_order,
)
from waterlib.core.exceptions import (
    WaterlibError,
    YAMLSyntaxError,
    ConfigurationError,
    ParameterValidationError,
    CircularDependencyError,
    UndefinedComponentError,
    MissingConnectionError,
    InvalidConnectionError,
    TimestepNotFoundError,
    SimulationError,
    ValidationError,
    DriverError,
)
from waterlib.core.drivers import (
    Driver,
    ClimateDrivers,
    DriverRegistry,
    StochasticDriver,
    TimeseriesDriver,
    validate_driver_config,
    create_driver_from_config,
)
from waterlib.core.validation import (
    validate_positive,
    validate_range,
    validate_required,
    validate_type,
    validate_choice,
    validate_dict_structure,
    validate_date_format,
    validate_date_range,
    ModelValidator,
)
from waterlib.core.scaffold import create_project

__all__ = [
    # Core classes
    "Component",
    "Model",
    # Loader functions
    "load_model",
    "load_yaml",
    "create_component",
    "instantiate_components",
    "parse_dot_notation",
    "build_graph",
    "compute_execution_order",
    # Exceptions
    "WaterlibError",
    "YAMLSyntaxError",
    "ConfigurationError",
    "ParameterValidationError",
    "CircularDependencyError",
    "UndefinedComponentError",
    "MissingConnectionError",
    "InvalidConnectionError",
    "TimestepNotFoundError",
    "SimulationError",
    "ValidationError",
    "DriverError",
    # Validation utilities
    "validate_positive",
    "validate_range",
    "validate_required",
    "validate_type",
    "validate_choice",
    "validate_dict_structure",
    "validate_date_format",
    "validate_date_range",
    "ModelValidator",
    # Driver system
    "Driver",
    "ClimateDrivers",
    "DriverRegistry",
    "StochasticDriver",
    "TimeseriesDriver",
    "validate_driver_config",
    "create_driver_from_config",
    # Project scaffolding
    "create_project",
]
