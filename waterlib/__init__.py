"""
waterlib - A Python-native water resources simulation library

waterlib is designed for dynamic, 1-day time-step modeling with a focus on
transparency, flexibility, and user control. The library enables water resources
consultants to rapidly build custom water models while maintaining full visibility
and control over model behavior.

Key Features:
- Human-readable YAML configuration
- Graph-based model representation
- Library-first approach for Jupyter notebooks
- Extensible component architecture
- Project scaffolding for quick setup
"""

__version__ = "1.1.0"

# Core functionality
from waterlib.core.base import Component
from waterlib.core.simple_model import Model
from waterlib.core.loader import load_model
from waterlib.core.simulation import run_simulation, SimulationEngine
from waterlib.core.results import Results, SimulationResult
from waterlib.core.scaffold import create_project

# Analysis tools
from waterlib.analysis import ResultsLogger

# Plotting utilities (optional - requires matplotlib)
from waterlib import plotting

# Climate utilities
from waterlib.climate import (
    PrecipGen,
    TempGen,
    TimeseriesClimate,
    calculate_hargreaves_et,
    ClimateManager,
)

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

__all__ = [
    "__version__",
    "Component",
    "Model",
    "load_model",
    "run_simulation",
    "SimulationEngine",
    "Results",
    "SimulationResult",
    "ResultsLogger",
    "PrecipGen",
    "TempGen",
    "TimeseriesClimate",
    "calculate_hargreaves_et",
    "ClimateManager",
    "create_project",
]
