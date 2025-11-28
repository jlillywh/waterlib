"""
WGEN Templates and Utilities

This module provides template files and utilities for WGEN parameter configuration.
"""

from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent

def get_template_path(filename: str) -> Path:
    """Get the full path to a template file."""
    return TEMPLATE_DIR / filename

__all__ = ['get_template_path', 'TEMPLATE_DIR']
