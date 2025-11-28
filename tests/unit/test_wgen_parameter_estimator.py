"""
Unit tests for WGEN parameter estimator.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from waterlib.templates.wgen_parameter_estimator import (
    estimate_precipitation_params,
    estimate_temperature_params,
    estimate_radiation_params
)
from waterlib.kernels.climate.wgen import WGENParams


def generate_synthetic_climate_data(n_years=3):
    """Generate synthetic climate data for testing."""
    start_date = datetime(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(365 * n_years)]

    # Generate synthetic precipitation (simple random)
    np.random.seed(42)
    precip = np.random.gamma(0.8, 5.0, len(dates))
    precip[np.random.random(len(dates)) > 0.3] = 0  # Make some days dry

    # Generate synthetic temperatures with seasonal variation
    doy = np.array([d.timetuple().tm_yday for d in dates])
    tmax = 20 + 10 * np.cos(2 * np.pi * (doy - 200) / 365) + np.random.normal(0, 2, len(dates))
    tmin = 10 + 8 * np.cos(2 * np.pi * (doy - 200) / 365) + np.random.normal(0, 2, len(dates))

    # Generate synthetic solar radiation with seasonal variation
    solar = 15 + 5 * np.cos(2 * np.pi * (doy - 172) / 365) + np.random.normal(0, 1, len(dates))
    solar = np.maximum(solar, 0)  # Ensure non-negative

    return pd.DataFrame({
        'date': dates,
        'precip_mm': precip,
        'tmax_c': tmax,
        'tmin_c': tmin,
        'solar_mjm2': solar
    })


def test_estimate_precipitation_params():
    """Test that precipitation parameter estimation returns correct structure."""
    df = generate_synthetic_climate_data()

    params = estimate_precipitation_params(df['precip_mm'], df['date'])

    # Check structure
    assert isinstance(params, dict)
    assert set(params.keys()) == {'pww', 'pwd', 'alpha', 'beta'}

    # Check each list has 12 values
    for key in params.keys():
        assert len(params[key]) == 12, f"{key} should have 12 values"

    # Check probability ranges
    for i in range(12):
        assert 0 <= params['pww'][i] <= 1, f"pww[{i}] out of range"
        assert 0 <= params['pwd'][i] <= 1, f"pwd[{i}] out of range"

    # Check positive values
    for i in range(12):
        assert params['alpha'][i] > 0, f"alpha[{i}] must be positive"
        assert params['beta'][i] > 0, f"beta[{i}] must be positive"


def test_estimate_temperature_params():
    """Test that temperature parameter estimation returns correct structure."""
    df = generate_synthetic_climate_data()

    params = estimate_temperature_params(
        df['tmax_c'], df['tmin_c'], df['precip_mm'], df['date']
    )

    # Check structure
    assert isinstance(params, dict)
    expected_keys = {'txmd', 'atx', 'txmw', 'tn', 'atn', 'cvtx', 'acvtx', 'cvtn', 'acvtn'}
    assert set(params.keys()) == expected_keys

    # Check all values are scalars
    for key, value in params.items():
        assert isinstance(value, (int, float)), f"{key} should be a scalar"


def test_estimate_radiation_params():
    """Test that radiation parameter estimation returns correct structure."""
    df = generate_synthetic_climate_data()

    params = estimate_radiation_params(df['solar_mjm2'], df['precip_mm'], df['date'])

    # Check structure
    assert isinstance(params, dict)
    expected_keys = {'rmd', 'ar', 'rmw'}
    assert set(params.keys()) == expected_keys

    # Check all values are scalars
    for key, value in params.items():
        assert isinstance(value, (int, float)), f"{key} should be a scalar"


def test_parameter_compatibility_with_wgen_params():
    """Test that estimated parameters can be used to create a valid WGENParams object."""
    df = generate_synthetic_climate_data()

    # Estimate all parameters
    precip_params = estimate_precipitation_params(df['precip_mm'], df['date'])
    temp_params = estimate_temperature_params(
        df['tmax_c'], df['tmin_c'], df['precip_mm'], df['date']
    )
    rad_params = estimate_radiation_params(df['solar_mjm2'], df['precip_mm'], df['date'])

    # Create WGENParams object
    wgen_params = WGENParams(
        pww=precip_params['pww'],
        pwd=precip_params['pwd'],
        alpha=precip_params['alpha'],
        beta=precip_params['beta'],
        txmd=temp_params['txmd'],
        atx=temp_params['atx'],
        txmw=temp_params['txmw'],
        tn=temp_params['tn'],
        atn=temp_params['atn'],
        cvtx=temp_params['cvtx'],
        acvtx=temp_params['acvtx'],
        cvtn=temp_params['cvtn'],
        acvtn=temp_params['acvtn'],
        rmd=rad_params['rmd'],
        ar=rad_params['ar'],
        rmw=rad_params['rmw'],
        latitude=40.0
    )

    # If we get here without exceptions, the parameters are compatible
    assert wgen_params is not None
    assert len(wgen_params.pww) == 12
    assert len(wgen_params.pwd) == 12
    assert len(wgen_params.alpha) == 12
    assert len(wgen_params.beta) == 12


def test_insufficient_data_handling():
    """Test that the estimator handles insufficient data gracefully."""
    # Create very small dataset
    dates = pd.date_range('2020-01-01', periods=30)
    precip = pd.Series([1.0] * 30)

    params = estimate_precipitation_params(precip, dates)

    # Should still return 12 values (with defaults for months with insufficient data)
    assert len(params['pww']) == 12
    assert len(params['pwd']) == 12
    assert len(params['alpha']) == 12
    assert len(params['beta']) == 12


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
