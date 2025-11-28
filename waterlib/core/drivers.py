"""
Global driver system for waterlib.

This module implements the driver pattern for managing climate data sources.
Drivers provide climate data (precipitation, temperature, ET) to components
through a type-safe registry with IDE autocompletion support.

The new API uses attribute-based access instead of string lookups:
    Old: drivers.get('precipitation').get_value(date)
    New: drivers.climate.precipitation.get_value(date)

This enables IDE autocompletion, catches typos at design time, and provides
better documentation through type hints.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Protocol
import logging

import pandas as pd
import numpy as np

from waterlib.core.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class Driver(ABC):
    """Base class for climate drivers.

    Drivers provide climate data values for specific dates. Subclasses
    implement different data sources (stochastic generation, CSV timeseries).
    """

    @abstractmethod
    def get_value(self, date: datetime) -> float:
        """Get driver value for a specific date.

        Args:
            date: Date to retrieve value for

        Returns:
            Climate value for the specified date
        """
        pass


class StochasticDriver(Driver):
    """Generates synthetic climate data using statistical parameters.

    This driver generates random values based on statistical parameters,
    optionally loaded from a CSV file. Supports reproducibility through
    random seed specification.

    Attributes:
        params: Dictionary of statistical parameters
        seed: Random seed for reproducibility (optional)
        rng: NumPy random generator instance
    """

    def __init__(self, params: Dict[str, Any], seed: Optional[int] = None):
        """Initialize stochastic driver.

        Args:
            params: Statistical parameters for generation
            seed: Random seed for reproducibility (optional)
        """
        self.params = params
        self.seed = seed

        # Initialize random number generator with seed
        self.rng = np.random.default_rng(seed)

        logger.info(f"Initialized StochasticDriver with seed={seed}")

    def get_value(self, date: datetime) -> float:
        """Generate a random value based on parameters.

        Args:
            date: Current simulation date

        Returns:
            Generated climate value
        """
        # Simple implementation: generate from normal distribution
        # Using mean and std from params, with defaults
        mean = self.params.get('mean', 0.0)
        std = self.params.get('std', 1.0)

        value = self.rng.normal(mean, std)
        return max(0.0, value)  # Ensure non-negative for climate data

    @classmethod
    def from_csv(cls, csv_path: Path, seed: Optional[int] = None) -> 'StochasticDriver':
        """Create stochastic driver with parameters loaded from CSV.

        Args:
            csv_path: Path to CSV file containing parameters
            seed: Random seed for reproducibility (optional)

        Returns:
            StochasticDriver instance with loaded parameters

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is missing required columns
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"Parameter file not found: {csv_path}")

        # Load parameters from CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise ValueError(f"Failed to read parameter file {csv_path}: {e}")

        # Convert to dictionary (simple implementation)
        # Assumes CSV has columns like 'mean', 'std', etc.
        params = df.to_dict('records')[0] if len(df) > 0 else {}

        logger.info(f"Loaded stochastic parameters from {csv_path}")

        return cls(params=params, seed=seed)


class TimeseriesDriver(Driver):
    """Reads historical climate data from CSV files.

    This driver loads timeseries data from a CSV file and returns values
    for specific dates through interpolation or direct lookup.

    Attributes:
        csv_path: Path to CSV file
        column: Column name containing the data
        data: Loaded pandas DataFrame with date index
    """

    def __init__(self, csv_path: Path, column: str):
        """Initialize timeseries driver.

        Args:
            csv_path: Path to CSV file containing timeseries data
            column: Column name to read values from

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If column doesn't exist in CSV
        """
        self.csv_path = csv_path
        self.column = column

        if not csv_path.exists():
            raise FileNotFoundError(f"Timeseries file not found: {csv_path}")

        # Load data with date parsing
        try:
            self.data = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
        except Exception as e:
            raise ValueError(f"Failed to read timeseries file {csv_path}: {e}")

        # Validate column exists
        if column not in self.data.columns:
            raise ValueError(
                f"Column '{column}' not found in {csv_path}. "
                f"Available columns: {list(self.data.columns)}"
            )

        logger.info(f"Loaded timeseries data from {csv_path}, column '{column}'")
        logger.info(f"  Date range: {self.data.index.min()} to {self.data.index.max()}")

    def get_value(self, date: datetime) -> float:
        """Get value from timeseries for a specific date.

        Args:
            date: Date to retrieve value for

        Returns:
            Value from timeseries for the specified date

        Raises:
            KeyError: If date not found in timeseries
        """
        try:
            # Convert to pandas Timestamp for indexing
            date_ts = pd.Timestamp(date)
            value = self.data.loc[date_ts, self.column]
            return float(value)
        except KeyError:
            raise KeyError(
                f"Date {date.strftime('%Y-%m-%d')} not found in timeseries data. "
                f"Available range: {self.data.index.min()} to {self.data.index.max()}"
            )


class ClimateDrivers:
    """Type-safe namespace for climate drivers with IDE autocompletion.

    This class provides attribute-based access to climate drivers, enabling
    IDE autocompletion and catching typos before runtime.

    Example:
        >>> drivers.climate.precipitation.get_value(date)
        >>> drivers.climate.temperature.get_value(date)
        >>> drivers.climate.et.get_value(date)

    Attributes:
        precipitation: Precipitation driver (mm/day)
        temperature: Temperature driver (°C)
        et: Evapotranspiration driver (mm/day)
    """

    def __init__(self):
        """Initialize climate drivers namespace."""
        self._precipitation: Optional[Driver] = None
        self._temperature: Optional[Driver] = None
        self._et: Optional[Driver] = None

    @property
    def precipitation(self) -> Driver:
        """Get precipitation driver.

        Returns:
            Precipitation driver instance

        Raises:
            AttributeError: If precipitation driver not registered
        """
        if self._precipitation is None:
            raise AttributeError(
                "Precipitation driver not registered. "
                "Configure 'precipitation' in settings.climate section."
            )
        return self._precipitation

    @precipitation.setter
    def precipitation(self, driver: Driver) -> None:
        """Set precipitation driver."""
        self._precipitation = driver

    @property
    def temperature(self) -> Driver:
        """Get temperature driver.

        Returns:
            Temperature driver instance

        Raises:
            AttributeError: If temperature driver not registered
        """
        if self._temperature is None:
            raise AttributeError(
                "Temperature driver not registered. "
                "Configure 'temperature' in settings.climate section."
            )
        return self._temperature

    @temperature.setter
    def temperature(self, driver: Driver) -> None:
        """Set temperature driver."""
        self._temperature = driver

    @property
    def et(self) -> Driver:
        """Get evapotranspiration driver.

        Returns:
            ET driver instance

        Raises:
            AttributeError: If ET driver not registered
        """
        if self._et is None:
            raise AttributeError(
                "ET driver not registered. "
                "Configure 'et' in settings.climate section."
            )
        return self._et

    @et.setter
    def et(self, driver: Driver) -> None:
        """Set evapotranspiration driver."""
        self._et = driver

    def has_precipitation(self) -> bool:
        """Check if precipitation driver is registered."""
        return self._precipitation is not None

    def has_temperature(self) -> bool:
        """Check if temperature driver is registered."""
        return self._temperature is not None

    def has_et(self) -> bool:
        """Check if ET driver is registered."""
        return self._et is not None


class DriverRegistry:
    """Registry for managing global climate drivers with type-safe access.

    The DriverRegistry provides both legacy string-based access and new
    type-safe attribute-based access through namespaces.

    New API (recommended):
        drivers.climate.precipitation.get_value(date)
        drivers.climate.temperature.get_value(date)
        drivers.climate.et.get_value(date)

    Legacy API (still supported):
        drivers.get('precipitation').get_value(date)

    Attributes:
        climate: Type-safe namespace for climate drivers
        drivers: Internal dictionary (legacy compatibility)
    """

    def __init__(self):
        """Initialize driver registry with type-safe namespaces."""
        # Legacy string-based storage
        self.drivers: Dict[str, Driver] = {}

        # Type-safe namespace for climate drivers
        self.climate = ClimateDrivers()

        logger.info("Initialized DriverRegistry with type-safe access")

    def register(self, name: str, driver: Driver) -> None:
        """Register a driver with a given name.

        Registers the driver in both the legacy dictionary and the appropriate
        type-safe namespace for backwards compatibility.

        Args:
            name: Name to register driver under (e.g., 'precipitation', 'temperature')
            driver: Driver instance to register
        """
        # Store in legacy dictionary
        self.drivers[name] = driver

        # Also register in type-safe namespace
        if name == 'precipitation':
            self.climate.precipitation = driver
        elif name == 'temperature':
            self.climate.temperature = driver
        elif name == 'et':
            self.climate.et = driver

        logger.info(f"Registered driver: {name} ({type(driver).__name__})")

    def get(self, name: str) -> Driver:
        """Get a driver by name.

        Args:
            name: Name of driver to retrieve

        Returns:
            Driver instance

        Raises:
            KeyError: If driver name not found in registry
        """
        if name not in self.drivers:
            raise KeyError(
                f"Driver '{name}' not found in registry. "
                f"Available drivers: {list(self.drivers.keys())}"
            )
        return self.drivers[name]

    def has_driver(self, name: str) -> bool:
        """Check if a driver is registered.

        Args:
            name: Name of driver to check

        Returns:
            True if driver is registered, False otherwise
        """
        return name in self.drivers

    def get_all_values(self, date: datetime) -> Dict[str, float]:
        """Get values from all drivers for a specific date.

        Args:
            date: Date to retrieve values for

        Returns:
            Dictionary mapping driver names to their values
        """
        return {name: driver.get_value(date) for name, driver in self.drivers.items()}


def validate_driver_config(driver_config: Dict[str, Any], driver_name: str) -> None:
    """Validate driver configuration for mode-specific requirements.

    Args:
        driver_config: Driver configuration dictionary
        driver_name: Name of driver (for error messages)

    Raises:
        ConfigurationError: If configuration is invalid
    """
    if 'mode' not in driver_config:
        raise ConfigurationError(
            f"Driver '{driver_name}' missing required field: 'mode'. "
            f"Must be 'stochastic', 'timeseries', or 'wgen'"
        )

    mode = driver_config['mode']

    if mode not in ['stochastic', 'timeseries', 'wgen']:
        raise ConfigurationError(
            f"Driver '{driver_name}' has invalid mode: '{mode}'. "
            f"Must be 'stochastic', 'timeseries', or 'wgen'"
        )

    # Validate mode-specific requirements
    if mode == 'stochastic':
        # Stochastic mode can have seed and/or file parameters
        # At minimum, we need some way to generate data
        if 'file' not in driver_config and 'params' not in driver_config:
            raise ConfigurationError(
                f"Stochastic driver '{driver_name}' must specify either 'file' "
                f"(for CSV parameters) or 'params' (inline parameters)"
            )

    elif mode == 'timeseries':
        # Timeseries mode requires file and column
        if 'file' not in driver_config:
            raise ConfigurationError(
                f"Timeseries driver '{driver_name}' missing required field: 'file'"
            )
        if 'column' not in driver_config:
            raise ConfigurationError(
                f"Timeseries driver '{driver_name}' missing required field: 'column'"
            )

    elif mode == 'wgen':
        # WGEN mode - validation happens in ClimateManager
        # No specific validation needed here as WGEN config is shared
        pass


def create_driver_from_config(driver_config: Dict[str, Any],
                              driver_name: str,
                              yaml_dir: Path) -> Driver:
    """Create a driver instance from configuration.

    Args:
        driver_config: Driver configuration dictionary
        driver_name: Name of driver (for error messages)
        yaml_dir: Directory containing YAML file (for resolving relative paths)

    Returns:
        Driver instance (StochasticDriver or TimeseriesDriver)

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate configuration first
    validate_driver_config(driver_config, driver_name)

    mode = driver_config['mode']

    if mode == 'stochastic':
        seed = driver_config.get('seed')

        # Load from file if specified
        if 'file' in driver_config:
            file_path = yaml_dir / driver_config['file']
            return StochasticDriver.from_csv(file_path, seed=seed)
        else:
            # Use inline params
            params = driver_config.get('params', {})
            return StochasticDriver(params=params, seed=seed)

    elif mode == 'timeseries':
        file_path = yaml_dir / driver_config['file']
        column = driver_config['column']
        return TimeseriesDriver(file_path, column)

    else:
        raise ConfigurationError(f"Invalid driver mode: {mode}")
