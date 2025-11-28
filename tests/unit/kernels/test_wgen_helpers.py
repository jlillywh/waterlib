"""Unit tests for WGEN helper functions."""
import datetime
import pytest
from waterlib.kernels.climate.wgen import (
    _celsius_to_kelvin,
    _kelvin_to_celsius,
    _get_monthly_params,
    _calculate_seasonal_temp,
    _calculate_seasonal_radiation,
    WGENParams
)


def test_celsius_to_kelvin():
    """Test Celsius to Kelvin conversion."""
    assert _celsius_to_kelvin(0.0) == 273.15
    assert _celsius_to_kelvin(100.0) == 373.15
    assert _celsius_to_kelvin(-273.15) == 0.0


def test_kelvin_to_celsius():
    """Test Kelvin to Celsius conversion."""
    assert _kelvin_to_celsius(273.15) == 0.0
    assert _kelvin_to_celsius(373.15) == 100.0
    assert _kelvin_to_celsius(0.0) == -273.15


def test_temperature_conversion_roundtrip():
    """Test that temperature conversion is reversible."""
    temps_c = [0.0, 25.0, -10.0, 100.0, -273.15]
    for temp_c in temps_c:
        temp_k = _celsius_to_kelvin(temp_c)
        temp_c_back = _kelvin_to_celsius(temp_k)
        assert abs(temp_c - temp_c_back) < 1e-10


def test_get_monthly_params():
    """Test extraction of monthly parameters."""
    params = WGENParams(
        pww=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.85, 0.75],
        pwd=[0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6],
        alpha=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1],
        beta=[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5],
        txmd=20.0, atx=10.0, txmw=18.0, tn=10.0, atn=8.0,
        cvtx=0.1, acvtx=0.05, cvtn=0.1, acvtn=0.05,
        rmd=15.0, ar=5.0, rmw=12.0, latitude=40.0
    )

    # Test January (month 1)
    pww, pwd, alpha, beta = _get_monthly_params(params, 1)
    assert pww == 0.1
    assert pwd == 0.05
    assert alpha == 1.0
    assert beta == 5.0

    # Test June (month 6)
    pww, pwd, alpha, beta = _get_monthly_params(params, 6)
    assert pww == 0.6
    assert pwd == 0.3
    assert alpha == 1.5
    assert beta == 7.5

    # Test December (month 12)
    pww, pwd, alpha, beta = _get_monthly_params(params, 12)
    assert pww == 0.75
    assert pwd == 0.6
    assert alpha == 2.1
    assert beta == 10.5


def test_calculate_seasonal_temp():
    """Test seasonal temperature calculation using Fourier function."""
    mean = 288.15  # 15°C in Kelvin
    amplitude = 10.0  # 10K amplitude
    latitude = 40.0  # Northern hemisphere

    # Day 200 should be near peak (summer) for Northern hemisphere
    temp_summer = _calculate_seasonal_temp(mean, amplitude, 200, latitude)
    assert temp_summer > mean  # Should be warmer than mean

    # Day 20 should be near minimum (winter) for Northern hemisphere
    temp_winter = _calculate_seasonal_temp(mean, amplitude, 20, latitude)
    assert temp_winter < mean  # Should be cooler than mean

    # Test Southern hemisphere (opposite pattern)
    latitude_south = -40.0
    temp_summer_south = _calculate_seasonal_temp(mean, amplitude, 20, latitude_south)
    assert temp_summer_south > mean  # Day 20 is summer in Southern hemisphere


def test_calculate_seasonal_radiation():
    """Test seasonal radiation calculation using Fourier function."""
    mean = 15.0  # MJ/m²/day
    amplitude = 5.0  # MJ/m²/day
    latitude = 40.0  # Northern hemisphere

    # Day 172 should be near peak (summer solstice) for Northern hemisphere
    rad_summer = _calculate_seasonal_radiation(mean, amplitude, 172, latitude)
    assert rad_summer > mean  # Should be higher than mean
    assert rad_summer >= 0  # Radiation cannot be negative

    # Day 355 should be near minimum (winter solstice) for Northern hemisphere
    rad_winter = _calculate_seasonal_radiation(mean, amplitude, 355, latitude)
    assert rad_winter < mean  # Should be lower than mean
    assert rad_winter >= 0  # Radiation cannot be negative

    # Test that negative values are clipped to zero
    rad_negative = _calculate_seasonal_radiation(5.0, 10.0, 355, latitude)
    assert rad_negative >= 0
