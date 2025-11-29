"""
Base component class for waterlib simulation framework.

This module defines the Component abstract base class that all simulation
components must inherit from. It enforces a standard interface for initialization,
calculation, and value retrieval.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime
import logging


@dataclass
class SiteConfig:
    """Physical properties of the simulation site.

    This dataclass stores geographic and physical characteristics of the
    simulation site that are used by climate drivers and hydrological kernels.

    Attributes:
        latitude: Site latitude in decimal degrees (-90 to 90)
        elevation_m: Site elevation in meters above sea level (default: 0.0)
        time_zone: Optional time zone offset from UTC in hours

    Example:
        >>> site = SiteConfig(latitude=45.5, elevation_m=1200.0)
        >>> site = SiteConfig(latitude=-33.8, elevation_m=50.0, time_zone=10.0)
    """
    latitude: float
    elevation_m: float = 0.0
    time_zone: Optional[float] = None

    def __post_init__(self):
        """Validate latitude after initialization."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90. Got {self.latitude}")


class Component(ABC):
    """Abstract base class for all water simulation components.

    All components in waterlib must inherit from this class and implement
    the required step() method. This ensures a consistent interface that
    the simulator can interact with uniformly.

    Attributes:
        name: Unique identifier for this component instance
        inputs: Dictionary storing component input connections
        outputs: Dictionary storing component output values
    """

    def __init__(self, name: str, meta: Dict[str, Any] = None, **params):
        """Initialize component with YAML parameters.

        Args:
            name: Unique component identifier from YAML configuration
            meta: Optional metadata dictionary for visualization (x, y, color, label)
            **params: Component-specific parameters from YAML
        """
        self.name = name
        self.meta = meta or {}
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"waterlib.{self.__class__.__name__}.{name}")

    @abstractmethod
    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep and return outputs.

        This method is called once per simulation timestep. Components should:
        1. Read inputs from self.inputs or global_data
        2. Perform calculations
        3. Store results in self.outputs
        4. Return the outputs dictionary

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data
                        (precipitation, temperature, PET, etc.)

        Returns:
            Dictionary of output values for this timestep
        """
        pass
