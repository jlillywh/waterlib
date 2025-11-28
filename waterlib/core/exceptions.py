"""
Custom exception classes for waterlib.

This module defines all custom exceptions used throughout the waterlib library
to provide clear, actionable error messages to users.
"""


class WaterlibError(Exception):
    """Base exception class for all waterlib errors.

    All custom exceptions in waterlib inherit from this class, making it
    easy to catch any waterlib-specific error.
    """
    pass


class YAMLSyntaxError(WaterlibError):
    """Raised when YAML file has syntax errors.

    This exception is raised during model loading when the YAML file cannot
    be parsed due to syntax errors (invalid YAML structure, indentation issues, etc.).
    """
    pass


class ConfigurationError(WaterlibError):
    """Raised when component configuration is invalid.

    This exception is raised when:
    - Required parameters are missing from component configuration
    - Parameter values are invalid or out of acceptable range
    - Component type is not recognized
    """
    pass


class ParameterValidationError(ConfigurationError):
    """Raised when component parameter validation fails.

    This exception is raised when a component parameter has an invalid value,
    such as negative values where positive is required, or values outside
    acceptable ranges.
    """
    pass


class CircularDependencyError(WaterlibError):
    """Raised when graph contains cycles.

    This exception is raised during graph construction when the component
    connections form a circular dependency, which would make it impossible
    to determine a valid execution order.
    """
    pass


class UndefinedComponentError(ConfigurationError):
    """Raised when component references non-existent component.

    This exception is raised when a component's connection parameter
    (inflows, source, control_source) references a component name that
    doesn't exist in the model configuration.
    """
    pass


class MissingConnectionError(ConfigurationError):
    """Raised when a required connection is missing.

    This exception is raised when a component requires a connection
    (e.g., inflows, source) but none is provided in the YAML configuration.
    """
    pass


class InvalidConnectionError(ConfigurationError):
    """Raised when a connection is invalid.

    This exception is raised when a connection references a non-existent
    output or has an invalid format.
    """
    pass


class TimestepNotFoundError(WaterlibError):
    """Raised when timeseries data missing for timestep.

    This exception is raised by Timeseries components when the requested
    timestep does not exist in the loaded CSV data.
    """
    pass


class SimulationError(WaterlibError):
    """Raised when simulation execution fails.

    This exception is raised during simulation execution when:
    - Invalid date range is provided
    - Component execution fails
    - Required settings are missing
    """

    def __init__(self, message: str, component: str = None, date: str = None,
                 inputs: dict = None, original_error: Exception = None):
        """Initialize simulation error with context.

        Args:
            message: Error message
            component: Name of component that failed (optional)
            date: Date when error occurred (optional)
            inputs: Component inputs at time of failure (optional)
            original_error: Original exception that caused this error (optional)
        """
        self.component = component
        self.date = date
        self.inputs = inputs
        self.original_error = original_error

        # Build detailed error message
        full_message = message
        if component:
            full_message = f"[Component: {component}] {full_message}"
        if date:
            full_message = f"[Date: {date}] {full_message}"
        if inputs:
            full_message += f"\nInputs: {inputs}"
        if original_error:
            full_message += f"\nOriginal error: {type(original_error).__name__}: {str(original_error)}"

        super().__init__(full_message)


class ValidationError(WaterlibError):
    """Raised when model validation fails.

    This exception is raised during dry-run validation when issues are
    detected in the model configuration or structure.
    """
    pass


class DriverError(WaterlibError):
    """Raised when driver configuration or execution fails.

    This exception is raised when:
    - Driver configuration is invalid
    - Driver data cannot be loaded
    - Driver execution fails
    """
    pass
