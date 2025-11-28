"""
Validation utilities for waterlib.

This module provides utilities for validating component parameters,
model structure, and performing dry-run validation.
"""

from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime

from waterlib.core.exceptions import (
    ParameterValidationError,
    ValidationError,
    ConfigurationError,
)


logger = logging.getLogger(__name__)


def validate_positive(value: Union[int, float], param_name: str,
                     component_name: str, allow_zero: bool = False) -> None:
    """Validate that a parameter is positive.

    Args:
        value: Parameter value to validate
        param_name: Name of the parameter
        component_name: Name of the component
        allow_zero: Whether to allow zero values

    Raises:
        ParameterValidationError: If value is not positive
    """
    if value is None:
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' cannot be None"
        )

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' must be numeric, got {type(value).__name__}"
        )

    if allow_zero:
        if value < 0:
            raise ParameterValidationError(
                f"Component '{component_name}': parameter '{param_name}' must be >= 0, got {value}"
            )
    else:
        if value <= 0:
            raise ParameterValidationError(
                f"Component '{component_name}': parameter '{param_name}' must be > 0, got {value}"
            )


def validate_range(value: Union[int, float], param_name: str,
                  component_name: str, min_val: float = None,
                  max_val: float = None, inclusive: bool = True) -> None:
    """Validate that a parameter is within a specified range.

    Args:
        value: Parameter value to validate
        param_name: Name of the parameter
        component_name: Name of the component
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        inclusive: Whether range bounds are inclusive

    Raises:
        ParameterValidationError: If value is outside the range
    """
    if value is None:
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' cannot be None"
        )

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' must be numeric, got {type(value).__name__}"
        )

    if min_val is not None:
        if inclusive:
            if value < min_val:
                raise ParameterValidationError(
                    f"Component '{component_name}': parameter '{param_name}' must be >= {min_val}, got {value}"
                )
        else:
            if value <= min_val:
                raise ParameterValidationError(
                    f"Component '{component_name}': parameter '{param_name}' must be > {min_val}, got {value}"
                )

    if max_val is not None:
        if inclusive:
            if value > max_val:
                raise ParameterValidationError(
                    f"Component '{component_name}': parameter '{param_name}' must be <= {max_val}, got {value}"
                )
        else:
            if value >= max_val:
                raise ParameterValidationError(
                    f"Component '{component_name}': parameter '{param_name}' must be < {max_val}, got {value}"
                )


def validate_required(value: Any, param_name: str, component_name: str) -> None:
    """Validate that a required parameter is present.

    Args:
        value: Parameter value to validate
        param_name: Name of the parameter
        component_name: Name of the component

    Raises:
        ParameterValidationError: If value is None
    """
    if value is None:
        raise ParameterValidationError(
            f"Component '{component_name}': required parameter '{param_name}' is missing"
        )


def validate_type(value: Any, param_name: str, component_name: str,
                 expected_type: type) -> None:
    """Validate that a parameter has the expected type.

    Args:
        value: Parameter value to validate
        param_name: Name of the parameter
        component_name: Name of the component
        expected_type: Expected type

    Raises:
        ParameterValidationError: If value has wrong type
    """
    if value is not None and not isinstance(value, expected_type):
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def validate_choice(value: Any, param_name: str, component_name: str,
                   choices: List[Any]) -> None:
    """Validate that a parameter is one of the allowed choices.

    Args:
        value: Parameter value to validate
        param_name: Name of the parameter
        component_name: Name of the component
        choices: List of allowed values

    Raises:
        ParameterValidationError: If value is not in choices
    """
    if value not in choices:
        choices_str = ', '.join(f"'{c}'" for c in choices)
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' must be one of [{choices_str}], "
            f"got '{value}'"
        )


def validate_dict_structure(value: Dict, param_name: str, component_name: str,
                           required_keys: List[str] = None,
                           optional_keys: List[str] = None) -> None:
    """Validate that a dictionary parameter has the expected structure.

    Args:
        value: Dictionary to validate
        param_name: Name of the parameter
        component_name: Name of the component
        required_keys: List of required keys (optional)
        optional_keys: List of optional keys (optional)

    Raises:
        ParameterValidationError: If dictionary structure is invalid
    """
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"Component '{component_name}': parameter '{param_name}' must be a dictionary, "
            f"got {type(value).__name__}"
        )

    if required_keys:
        missing_keys = [k for k in required_keys if k not in value]
        if missing_keys:
            raise ParameterValidationError(
                f"Component '{component_name}': parameter '{param_name}' is missing required keys: "
                f"{', '.join(missing_keys)}"
            )

    if optional_keys is not None:
        # If optional_keys is provided, check for unexpected keys
        allowed_keys = set(required_keys or []) | set(optional_keys)
        unexpected_keys = [k for k in value.keys() if k not in allowed_keys]
        if unexpected_keys:
            logger.warning(
                f"Component '{component_name}': parameter '{param_name}' has unexpected keys: "
                f"{', '.join(unexpected_keys)}"
            )


def validate_date_format(date_str: str, param_name: str,
                        context: str = "settings") -> datetime:
    """Validate and parse a date string.

    Args:
        date_str: Date string to validate
        param_name: Name of the parameter
        context: Context for error message (e.g., "settings", "component")

    Returns:
        Parsed datetime object

    Raises:
        ConfigurationError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise ConfigurationError(
            f"Invalid {param_name} format in {context}: '{date_str}'. "
            f"Expected YYYY-MM-DD format. Error: {str(e)}"
        )
    except TypeError:
        raise ConfigurationError(
            f"Invalid {param_name} in {context}: expected string, got {type(date_str).__name__}"
        )


def validate_date_range(start_date: datetime, end_date: datetime) -> None:
    """Validate that a date range is valid.

    Args:
        start_date: Start date
        end_date: End date

    Raises:
        ConfigurationError: If date range is invalid
    """
    if end_date < start_date:
        raise ConfigurationError(
            f"end_date ({end_date.strftime('%Y-%m-%d')}) must be >= "
            f"start_date ({start_date.strftime('%Y-%m-%d')})"
        )


class ModelValidator:
    """Validator for performing dry-run validation of models.

    This class performs comprehensive validation of a model without
    executing the simulation, checking for:
    - YAML structure validity
    - Component parameter validity
    - Connection graph validity
    - Settings validity
    """

    def __init__(self, model):
        """Initialize validator with a model.

        Args:
            model: Model instance to validate
        """
        self.model = model
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, raise_on_error: bool = True) -> bool:
        """Perform comprehensive validation.

        Args:
            raise_on_error: Whether to raise ValidationError if errors found

        Returns:
            True if validation passed, False otherwise

        Raises:
            ValidationError: If validation fails and raise_on_error is True
        """
        logger.info(f"Starting dry-run validation for model '{self.model.name}'")

        # Clear previous results
        self.errors = []
        self.warnings = []

        # Run validation checks
        self._validate_settings()
        self._validate_components()
        self._validate_connections()
        self._validate_graph()

        # Report results
        if self.warnings:
            logger.warning(f"Validation found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        if self.errors:
            logger.error(f"Validation found {len(self.errors)} errors:")
            for error in self.errors:
                logger.error(f"  - {error}")

            if raise_on_error:
                error_msg = "Model validation failed:\n" + "\n".join(f"  - {e}" for e in self.errors)
                raise ValidationError(error_msg)

            return False

        logger.info("Validation passed successfully")
        return True

    def _validate_settings(self) -> None:
        """Validate model settings."""
        try:
            from waterlib.core.config import ModelSettings

            # Handle both ModelSettings and dict formats
            if isinstance(self.model.settings, ModelSettings):
                # ModelSettings already validated during parsing
                # Just check that dates are present
                if self.model.settings.start_date is None:
                    self.errors.append("Missing required setting: 'start_date'")
                if self.model.settings.end_date is None:
                    self.errors.append("Missing required setting: 'end_date'")

                # Validate date range
                if self.model.settings.start_date and self.model.settings.end_date:
                    try:
                        validate_date_range(self.model.settings.start_date, self.model.settings.end_date)
                    except ConfigurationError as e:
                        self.errors.append(str(e))
            else:
                # Legacy dict format
                start_date = None
                end_date = None

                # Check for required date settings
                if 'start_date' not in self.model.settings:
                    self.errors.append("Missing required setting: 'start_date'")
                else:
                    try:
                        start_date = validate_date_format(
                            self.model.settings['start_date'],
                            'start_date',
                            'settings'
                        )
                    except ConfigurationError as e:
                        self.errors.append(str(e))
                        start_date = None

                if 'end_date' not in self.model.settings:
                    self.errors.append("Missing required setting: 'end_date'")
                else:
                    try:
                        end_date = validate_date_format(
                            self.model.settings['end_date'],
                            'end_date',
                            'settings'
                        )
                    except ConfigurationError as e:
                        self.errors.append(str(e))
                        end_date = None

                # Validate date range if both dates are valid
                if start_date is not None and end_date is not None:
                    try:
                        validate_date_range(start_date, end_date)
                    except ConfigurationError as e:
                        self.errors.append(str(e))

        except Exception as e:
            self.errors.append(f"Error validating settings: {str(e)}")

    def _validate_components(self) -> None:
        """Validate all components."""
        if not self.model.components:
            self.errors.append("Model has no components")
            return

        for name, component in self.model.components.items():
            try:
                # Check if component has validate method and call it
                if hasattr(component, 'validate_parameters'):
                    component.validate_parameters()
            except Exception as e:
                self.errors.append(f"Component '{name}' validation failed: {str(e)}")

    def _validate_connections(self) -> None:
        """Validate component connections."""
        # This is handled by the graph building process
        # Just check that graph can be built
        pass

    def _validate_graph(self) -> None:
        """Validate connection graph."""
        try:
            # Try to build graph if not already built
            if self.model.graph is None:
                self.model.build_graph()

            # Try to compute execution order
            if not self.model.execution_order:
                self.model.compute_execution_order()

            # Check for disconnected components
            if self.model.graph:
                import networkx as nx

                # Find weakly connected components
                weak_components = list(nx.weakly_connected_components(self.model.graph))

                if len(weak_components) > 1:
                    self.warnings.append(
                        f"Model has {len(weak_components)} disconnected subgraphs. "
                        f"This may indicate missing connections."
                    )

        except Exception as e:
            self.errors.append(f"Graph validation failed: {str(e)}")
