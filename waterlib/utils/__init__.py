"""
Utilities module for waterlib

This module contains utility functions and helper classes used throughout
the waterlib library, including interpolation utilities, validation functions,
and other common operations.
"""

from waterlib.utils.path_validation import (
    is_absolute_path,
    validate_relative_path,
    convert_to_relative_path,
)

# Utility functions will be imported here after implementation
# from waterlib.utils.interpolation import interpolate_eav
# from waterlib.utils.validation import validate_parameters

__all__ = [
    "is_absolute_path",
    "validate_relative_path",
    "convert_to_relative_path",
    # "interpolate_eav",
    # "validate_parameters",
]
