import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta, date
from waterlib.core.drivers import DriverRegistry
from waterlib.components.met_station import MetStation, MetStationConfig

class DummyDriver:
    def __init__(self, data):
        self.data = data
    def get_value(self, date):
        return self.data.get(date)

@pytest.fixture
def climate_data():
    # Generate synthetic climate data for 5 days
    base = datetime(2025, 1, 1)
    dates = [base + timedelta(days=i) for i in range(5)]
    return {
        'dates': dates,
        'precip': {d: 10.0 + i for i, d in enumerate(dates)},
        'temp': {d: {'tmin': 5.0 + i, 'tmax': 15.0 + i} for i, d in enumerate(dates)},
        'solar': {d: 20.0 + i for i, d in enumerate(dates)},
        'et': {d: 2.0 + i for i, d in enumerate(dates)},
    }

@pytest.fixture
def drivers(climate_data):
    registry = DriverRegistry()
    registry.register('precipitation', DummyDriver(climate_data['precip']))
    registry.register('temperature', DummyDriver(climate_data['temp']))
    registry.register('solar_radiation', DummyDriver(climate_data['solar']))
    registry.register('et', DummyDriver(climate_data['et']))
    return registry

def test_metstation_records_all(drivers, climate_data):
    met = MetStation(drivers)
    for d in climate_data['dates']:
        met.step(d)
    df = met.to_dataframe()
    assert len(df) == 5
    # Check columns
    assert 'precip_mm' in df.columns
    assert 'tmin_c' in df.columns
    assert 'tmax_c' in df.columns
    assert 'solar_mjm2' in df.columns
    assert 'et0_mm' in df.columns
    # Check values
    for i, d in enumerate(climate_data['dates']):
        assert df.iloc[i]['precip_mm'] == climate_data['precip'][d]
        assert df.iloc[i]['tmin_c'] == climate_data['temp'][d]['tmin']
        assert df.iloc[i]['tmax_c'] == climate_data['temp'][d]['tmax']
        assert df.iloc[i]['solar_mjm2'] == climate_data['solar'][d]
        assert df.iloc[i]['et0_mm'] == climate_data['et'][d]

def test_metstation_config_flags(drivers, climate_data):
    met = MetStation(drivers, log_precip=False, log_temp=False, log_solar=False, log_et0=False)
    for d in climate_data['dates']:
        met.step(d)
    df = met.to_dataframe()
    # Should have no columns
    assert df.shape[1] == 0

def test_metstation_partial_config(drivers, climate_data):
    met = MetStation(drivers, log_precip=True, log_temp=False, log_solar=True, log_et0=False)
    for d in climate_data['dates']:
        met.step(d)
    df = met.to_dataframe()
    assert 'precip_mm' in df.columns
    assert 'solar_mjm2' in df.columns
    assert 'tmin_c' not in df.columns
    assert 'tmax_c' not in df.columns
    assert 'et0_mm' not in df.columns

def test_metstation_default_config(drivers, climate_data):
    """Test that MetStation works with default config (no explicit config provided)."""
    met = MetStation(drivers)
    for d in climate_data['dates']:
        met.step(d)
    df = met.to_dataframe()
    # Default config should log everything
    assert len(df) == 5
    assert 'precip_mm' in df.columns
    assert 'tmin_c' in df.columns
    assert 'tmax_c' in df.columns
    assert 'solar_mjm2' in df.columns
    assert 'et0_mm' in df.columns

def test_metstation_export_csv(drivers, climate_data):
    """Test CSV export functionality."""
    met = MetStation(drivers)
    for d in climate_data['dates']:
        met.step(d)

    # Export to temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    temp_file.close()

    try:
        met.export_csv(temp_file.name)

        # Verify file exists
        assert os.path.exists(temp_file.name)

        # Read back and verify content
        df_read = pd.read_csv(temp_file.name)
        df_original = met.to_dataframe()

        # Check shape matches
        assert df_read.shape == df_original.shape

        # Check columns match
        assert list(df_read.columns) == list(df_original.columns)

        # Check values match (within floating point tolerance)
        pd.testing.assert_frame_equal(df_read, df_original)
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def test_metstation_empty_dataframe():
    """Test that to_dataframe works before any step() calls."""
    registry = DriverRegistry()
    met = MetStation(registry)
    df = met.to_dataframe()

    # Should return empty DataFrame
    assert len(df) == 0
    assert isinstance(df, pd.DataFrame)

def test_metstation_missing_precipitation_driver():
    """Test behavior when precipitation driver is missing but log_precip=True."""
    registry = DriverRegistry()
    # Only register temperature, not precipitation
    temp_data = {datetime(2025, 1, 1): {'tmin': 5.0, 'tmax': 15.0}}
    registry.register('temperature', DummyDriver(temp_data))

    met = MetStation(registry, log_precip=True, log_temp=True, log_solar=False, log_et0=False)

    # Should not crash, just skip precipitation
    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should only have temperature columns
    assert 'precip_mm' not in df.columns
    assert 'tmin_c' in df.columns
    assert 'tmax_c' in df.columns

def test_metstation_missing_temperature_driver():
    """Test behavior when temperature driver is missing but log_temp=True."""
    registry = DriverRegistry()
    # Only register precipitation, not temperature
    precip_data = {datetime(2025, 1, 1): 10.0}
    registry.register('precipitation', DummyDriver(precip_data))

    met = MetStation(registry, log_precip=True, log_temp=True, log_solar=False, log_et0=False)

    # Should not crash, just skip temperature
    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should only have precipitation column
    assert 'precip_mm' in df.columns
    assert 'tmin_c' not in df.columns
    assert 'tmax_c' not in df.columns

def test_metstation_missing_solar_driver():
    """Test behavior when solar radiation driver is missing but log_solar=True."""
    registry = DriverRegistry()
    precip_data = {datetime(2025, 1, 1): 10.0}
    registry.register('precipitation', DummyDriver(precip_data))

    met = MetStation(registry, log_precip=True, log_temp=False, log_solar=True, log_et0=False)

    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should only have precipitation, not solar
    assert 'precip_mm' in df.columns
    assert 'solar_mjm2' not in df.columns

def test_metstation_missing_et_driver():
    """Test behavior when ET driver is missing but log_et0=True."""
    registry = DriverRegistry()
    precip_data = {datetime(2025, 1, 1): 10.0}
    registry.register('precipitation', DummyDriver(precip_data))

    met = MetStation(registry, log_precip=True, log_temp=False, log_solar=False, log_et0=True)

    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should only have precipitation, not ET
    assert 'precip_mm' in df.columns
    assert 'et0_mm' not in df.columns

def test_metstation_with_date_objects(drivers):
    """Test that MetStation works with date objects (not just datetime)."""
    met = MetStation(drivers)

    # Use date objects instead of datetime
    test_dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]

    # This should work without errors
    for d in test_dates:
        met.step(d)

    df = met.to_dataframe()
    assert len(df) == 3

def test_metstation_none_values():
    """Test behavior when driver returns None."""
    registry = DriverRegistry()

    # Driver that returns None
    none_data = {datetime(2025, 1, 1): None}
    registry.register('precipitation', DummyDriver(none_data))

    met = MetStation(registry, log_precip=True, log_temp=False, log_solar=False, log_et0=False)

    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should record None value
    assert len(df) == 1
    assert 'precip_mm' in df.columns
    assert pd.isna(df.iloc[0]['precip_mm']) or df.iloc[0]['precip_mm'] is None

class TempObject:
    """Helper class for testing temperature as object with attributes."""
    def __init__(self, tmin, tmax):
        self.tmin = tmin
        self.tmax = tmax

def test_metstation_temperature_as_object():
    """Test temperature handling when returned as object with attributes."""
    registry = DriverRegistry()

    # Temperature as object with attributes
    temp_data = {datetime(2025, 1, 1): TempObject(tmin=5.0, tmax=15.0)}
    registry.register('temperature', DummyDriver(temp_data))

    met = MetStation(registry, log_precip=False, log_temp=True, log_solar=False, log_et0=False)

    met.step(datetime(2025, 1, 1))
    df = met.to_dataframe()

    # Should extract tmin/tmax from object
    assert df.iloc[0]['tmin_c'] == 5.0
    assert df.iloc[0]['tmax_c'] == 15.0
