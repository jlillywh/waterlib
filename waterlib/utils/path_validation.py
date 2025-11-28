"""
Path validation utilities for waterlib.

This module provides functions to validate that file paths in model configurations
use relative paths rather than absolute paths, ensuring portability across systems.
"""

from pathlib import Path
from typing import Union
from waterlib.core.exceptions import ConfigurationError


def is_absolute_path(path: Union[str, Path]) -> bool:
    """Check if a path is absolute.

    Args:
        path: Path string or Path object to check

    Returns:
        True if path is absolute, False if relative
    """
    path_obj = Path(path)
    return path_obj.is_absolute()


def validate_relative_path(path: Union[str, Path], component_name: str, parameter_name: str) -> None:
    """Validate that a path is relative, not absolute.

    This function checks if a path is relative and raises a helpful error
    if an absolute path is detected. Absolute paths reduce portability
    as they are specific to a particular machine's file system.

    Args:
        path: Path to validate
        component_name: Name of the component using this path (for error messages)
        parameter_name: Name of the parameter containing the path (for error messages)

    Raises:
        ConfigurationError: If the path is absolute

    Example:
        >>> validate_relative_path('../data/rainfall.csv', 'rainfall', 'file')
        >>> # No error - relative path is valid

        >>> validate_relative_path('/home/user/data/rainfall.csv', 'rainfall', 'file')
        ConfigurationError: Component 'rainfall' parameter 'file' uses absolute path...
    """
    if is_absolute_path(path):
        raise ConfigurationError(
            f"Component '{component_name}' parameter '{parameter_name}' uses absolute path '{path}'. "
            f"Please use relative paths for portability. "
            f"Example: '../data/rainfall.csv' instead of '{path}'"
        )


def convert_to_relative_path(path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
    """Convert an absolute path to a relative path from a base directory.

    This utility function can help convert absolute paths to relative paths
    when needed. It's primarily for tooling and migration purposes.

    Args:
        path: Path to convert
        base_dir: Base directory to compute relative path from

    Returns:
        Relative path from base_dir to path

    Example:
        >>> convert_to_relative_path('/home/user/project/data/file.csv', '/home/user/project/config')
        Path('../data/file.csv')
    """
    path_obj = Path(path).resolve()
    base_obj = Path(base_dir).resolve()

    try:
        return path_obj.relative_to(base_obj)
    except ValueError:
        # If paths don't share a common base, use relative_to with walk_up
        # This requires Python 3.12+, so we'll compute it manually
        # Find common ancestor and build relative path
        common = Path(*[p for p in base_obj.parts if p in path_obj.parts[:len(base_obj.parts)]])

        # Count how many levels up from base_dir to common ancestor
        up_levels = len([p for p in base_obj.parts if p not in common.parts])

        # Build path: go up, then down to target
        rel_parts = ['..'] * up_levels + [p for p in path_obj.parts if p not in common.parts]
        return Path(*rel_parts) if rel_parts else Path('.')
