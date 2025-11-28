"""
Unit tests for the Driver system and DriverRegistry.

Tests verify type-safe driver access, backwards compatibility with legacy API,
and proper error handling.
"""

import pytest
from datetime import datetime
from pathlib import Path

from waterlib.core.drivers import (
    Driver,
    StochasticDriver,
    TimeseriesDriver,
    ClimateDrivers,
    DriverRegistry
)


class TestClimateDriversNamespace:
    """Test the type-safe ClimateDrivers namespace."""

    def test_climate_drivers_initialization(self):
        """Test that ClimateDrivers initializes with all drivers None."""
        climate = ClimateDrivers()
        assert not climate.has_precipitation()
        assert not climate.has_temperature()
        assert not climate.has_et()

    def test_precipitation_setter_and_getter(self):
        """Test setting and getting precipitation driver."""
        climate = ClimateDrivers()
        driver = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=42)

        climate.precipitation = driver
        assert climate.has_precipitation()
        assert climate.precipitation is driver

    def test_temperature_setter_and_getter(self):
        """Test setting and getting temperature driver."""
        climate = ClimateDrivers()
        driver = StochasticDriver(params={'mean': 15.0, 'std': 3.0}, seed=42)

        climate.temperature = driver
        assert climate.has_temperature()
        assert climate.temperature is driver

    def test_et_setter_and_getter(self):
        """Test setting and getting ET driver."""
        climate = ClimateDrivers()
        driver = StochasticDriver(params={'mean': 3.0, 'std': 0.5}, seed=42)

        climate.et = driver
        assert climate.has_et()
        assert climate.et is driver

    def test_precipitation_access_before_registration_raises_error(self):
        """Test that accessing unregistered precipitation driver raises AttributeError."""
        climate = ClimateDrivers()

        with pytest.raises(AttributeError, match=r"Precipitation driver not registered"):
            _ = climate.precipitation

    def test_temperature_access_before_registration_raises_error(self):
        """Test that accessing unregistered temperature driver raises AttributeError."""
        climate = ClimateDrivers()

        with pytest.raises(AttributeError, match=r"Temperature driver not registered"):
            _ = climate.temperature

    def test_et_access_before_registration_raises_error(self):
        """Test that accessing unregistered ET driver raises AttributeError."""
        climate = ClimateDrivers()

        with pytest.raises(AttributeError, match=r"ET driver not registered"):
            _ = climate.et

    def test_multiple_drivers_registration(self):
        """Test registering all three climate drivers."""
        climate = ClimateDrivers()

        precip_driver = StochasticDriver(params={'mean': 5.0}, seed=1)
        temp_driver = StochasticDriver(params={'mean': 15.0}, seed=2)
        et_driver = StochasticDriver(params={'mean': 3.0}, seed=3)

        climate.precipitation = precip_driver
        climate.temperature = temp_driver
        climate.et = et_driver

        assert climate.has_precipitation()
        assert climate.has_temperature()
        assert climate.has_et()
        assert climate.precipitation is precip_driver
        assert climate.temperature is temp_driver
        assert climate.et is et_driver


class TestDriverRegistryNewAPI:
    """Test the new type-safe DriverRegistry API."""

    def test_registry_initialization(self):
        """Test that DriverRegistry initializes with climate namespace."""
        registry = DriverRegistry()
        assert hasattr(registry, 'climate')
        assert isinstance(registry.climate, ClimateDrivers)

    def test_register_precipitation_accessible_via_climate_namespace(self):
        """Test that registering precipitation makes it accessible via climate.precipitation."""
        registry = DriverRegistry()
        driver = StochasticDriver(params={'mean': 5.0}, seed=42)

        registry.register('precipitation', driver)

        # New API access
        assert registry.climate.precipitation is driver
        assert registry.climate.precipitation.get_value(datetime(2020, 1, 1)) >= 0

    def test_register_temperature_accessible_via_climate_namespace(self):
        """Test that registering temperature makes it accessible via climate.temperature."""
        registry = DriverRegistry()
        driver = StochasticDriver(params={'mean': 15.0}, seed=42)

        registry.register('temperature', driver)

        # New API access
        assert registry.climate.temperature is driver

    def test_register_et_accessible_via_climate_namespace(self):
        """Test that registering ET makes it accessible via climate.et."""
        registry = DriverRegistry()
        driver = StochasticDriver(params={'mean': 3.0}, seed=42)

        registry.register('et', driver)

        # New API access
        assert registry.climate.et is driver

    def test_new_api_usage_example(self):
        """Test realistic usage of new type-safe API."""
        registry = DriverRegistry()

        # Register drivers
        registry.register('precipitation', StochasticDriver({'mean': 5.0, 'std': 1.0}, seed=1))
        registry.register('temperature', StochasticDriver({'mean': 15.0, 'std': 3.0}, seed=2))
        registry.register('et', StochasticDriver({'mean': 3.0, 'std': 0.5}, seed=3))

        date = datetime(2020, 6, 15)

        # New type-safe API usage
        precip = registry.climate.precipitation.get_value(date)
        temp = registry.climate.temperature.get_value(date)
        et = registry.climate.et.get_value(date)

        assert isinstance(precip, float)
        assert isinstance(temp, float)
        assert isinstance(et, float)
        assert precip >= 0  # StochasticDriver ensures non-negative

    def test_type_safety_catches_typos(self):
        """Test that typos in attribute names raise AttributeError (caught by IDE)."""
        registry = DriverRegistry()
        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=42))

        # This should raise AttributeError (would be caught by IDE/type checker)
        with pytest.raises(AttributeError):
            _ = registry.climate.precip  # Typo: should be 'precipitation'

        with pytest.raises(AttributeError):
            _ = registry.climate.temp  # Typo: should be 'temperature'


class TestDriverRegistryLegacyAPI:
    """Test backwards compatibility with legacy string-based API."""

    def test_legacy_get_method_still_works(self):
        """Test that legacy drivers.get('precipitation') still works."""
        registry = DriverRegistry()
        driver = StochasticDriver(params={'mean': 5.0}, seed=42)

        registry.register('precipitation', driver)

        # Legacy API access
        assert registry.get('precipitation') is driver

    def test_legacy_has_driver_method(self):
        """Test that has_driver() method still works."""
        registry = DriverRegistry()
        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=42))

        assert registry.has_driver('precipitation')
        assert not registry.has_driver('temperature')

    def test_legacy_get_with_missing_driver_raises_keyerror(self):
        """Test that legacy get() raises KeyError for missing drivers."""
        registry = DriverRegistry()

        with pytest.raises(KeyError, match=r"Driver 'precipitation' not found"):
            registry.get('precipitation')

    def test_legacy_and_new_api_both_work(self):
        """Test that both legacy and new API work simultaneously."""
        registry = DriverRegistry()
        driver = StochasticDriver(params={'mean': 5.0}, seed=42)

        registry.register('precipitation', driver)

        # Both APIs should access the same driver
        assert registry.get('precipitation') is driver
        assert registry.climate.precipitation is driver
        assert registry.get('precipitation') is registry.climate.precipitation

    def test_get_all_values_legacy_method(self):
        """Test that get_all_values() legacy method still works."""
        registry = DriverRegistry()

        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=1))
        registry.register('temperature', StochasticDriver({'mean': 15.0}, seed=2))

        date = datetime(2020, 6, 15)
        all_values = registry.get_all_values(date)

        assert 'precipitation' in all_values
        assert 'temperature' in all_values
        assert isinstance(all_values['precipitation'], float)
        assert isinstance(all_values['temperature'], float)


class TestDriverRegistryMigrationPath:
    """Test scenarios for migrating from legacy to new API."""

    def test_components_can_use_new_api(self):
        """Test that components can migrate to new type-safe API."""
        registry = DriverRegistry()

        # Use same driver instance for both API tests
        precip_driver = StochasticDriver({'mean': 5.0}, seed=42)
        registry.register('precipitation', precip_driver)
        registry.register('temperature', StochasticDriver({'mean': 15.0}, seed=42))
        registry.register('et', StochasticDriver({'mean': 3.0}, seed=42))

        date = datetime(2020, 1, 1)

        # Old way (still works)
        precip_old = registry.get('precipitation').get_value(date)

        # New way (type-safe, IDE-friendly) - accesses same driver instance
        precip_new = registry.climate.precipitation.get_value(date)

        # Both APIs access the same driver instance, but values differ because
        # get_value() advances the RNG state each time it's called
        # Instead, verify both APIs access the same driver object
        assert registry.get('precipitation') is registry.climate.precipitation

    def test_error_messages_guide_users_to_configuration(self):
        """Test that error messages help users fix configuration issues."""
        registry = DriverRegistry()

        # User forgot to configure precipitation
        with pytest.raises(AttributeError, match=r"Configure 'precipitation' in settings.climate"):
            _ = registry.climate.precipitation

        # User forgot to configure temperature
        with pytest.raises(AttributeError, match=r"Configure 'temperature' in settings.climate"):
            _ = registry.climate.temperature

        # User forgot to configure ET
        with pytest.raises(AttributeError, match=r"Configure 'et' in settings.climate"):
            _ = registry.climate.et


class TestStochasticDriver:
    """Test StochasticDriver functionality."""

    def test_stochastic_driver_generates_values(self):
        """Test that StochasticDriver generates non-negative values."""
        driver = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=42)

        date = datetime(2020, 1, 1)
        value = driver.get_value(date)

        assert isinstance(value, float)
        assert value >= 0.0  # Should be non-negative

    def test_stochastic_driver_seed_reproducibility(self):
        """Test that same seed produces same values."""
        driver1 = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=42)
        driver2 = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=42)

        date = datetime(2020, 1, 1)

        assert driver1.get_value(date) == driver2.get_value(date)

    def test_stochastic_driver_different_seeds_different_values(self):
        """Test that different seeds produce different values."""
        driver1 = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=42)
        driver2 = StochasticDriver(params={'mean': 5.0, 'std': 1.0}, seed=99)

        date = datetime(2020, 1, 1)

        # Very unlikely to be equal with different seeds
        assert driver1.get_value(date) != driver2.get_value(date)


class TestDriverAPIComparison:
    """Test comparison between old and new API patterns."""

    def test_old_api_pattern(self):
        """Document the old magic string pattern (still supported)."""
        registry = DriverRegistry()
        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=42))

        date = datetime(2020, 1, 1)

        # Old pattern: string lookup, runtime error if typo
        precip = registry.get('precipitation').get_value(date)

        assert isinstance(precip, float)

    def test_new_api_pattern(self):
        """Document the new type-safe pattern (recommended)."""
        registry = DriverRegistry()
        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=42))

        date = datetime(2020, 1, 1)

        # New pattern: attribute access, IDE autocomplete, design-time error if typo
        precip = registry.climate.precipitation.get_value(date)

        assert isinstance(precip, float)

    def test_migration_benefits(self):
        """Demonstrate benefits of new API."""
        registry = DriverRegistry()
        registry.register('precipitation', StochasticDriver({'mean': 5.0}, seed=42))
        registry.register('temperature', StochasticDriver({'mean': 15.0}, seed=42))
        registry.register('et', StochasticDriver({'mean': 3.0}, seed=42))

        date = datetime(2020, 1, 1)

        # Old API: Easy to make typos
        # precip = registry.get('precip').get_value(date)  # Runtime KeyError

        # New API: Typos caught by IDE/type checker
        # precip = registry.climate.precip.get_value(date)  # AttributeError at design time

        # Correct usage with autocomplete support
        precip = registry.climate.precipitation.get_value(date)
        temp = registry.climate.temperature.get_value(date)
        et = registry.climate.et.get_value(date)

        assert all(isinstance(v, float) for v in [precip, temp, et])
