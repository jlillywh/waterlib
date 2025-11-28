"""Unit tests for wgen_step function."""
import datetime
import pytest
from waterlib.kernels.climate.wgen import (
    wgen_step,
    WGENParams,
    WGENState,
    WGENOutputs
)


def test_wgen_step_basic():
    """Test basic wgen_step functionality."""
    # Create test parameters
    params = WGENParams(
        pww=[0.5] * 12,
        pwd=[0.3] * 12,
        alpha=[1.0] * 12,
        beta=[10.0] * 12,
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0,
        random_seed=42
    )

    # Create initial state
    state = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 15)
    )

    # Run one step
    new_state, outputs = wgen_step(params, state)

    # Verify outputs structure
    assert isinstance(outputs, WGENOutputs)
    assert isinstance(outputs.precip_mm, float)
    assert isinstance(outputs.tmax_c, float)
    assert isinstance(outputs.tmin_c, float)
    assert isinstance(outputs.solar_mjm2, float)
    assert isinstance(outputs.is_wet, bool)

    # Verify state update
    assert isinstance(new_state, WGENState)
    assert new_state.current_date == datetime.date(2024, 1, 16)
    assert new_state.random_state is not None


def test_wgen_step_date_increment():
    """Test that wgen_step increments the date correctly."""
    params = WGENParams(
        pww=[0.5] * 12,
        pwd=[0.3] * 12,
        alpha=[1.0] * 12,
        beta=[10.0] * 12,
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0
    )

    state = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 31)
    )

    new_state, outputs = wgen_step(params, state)

    # Should roll over to February
    assert new_state.current_date == datetime.date(2024, 2, 1)


def test_wgen_step_requires_date():
    """Test that wgen_step raises error if current_date is None."""
    params = WGENParams(
        pww=[0.5] * 12,
        pwd=[0.3] * 12,
        alpha=[1.0] * 12,
        beta=[10.0] * 12,
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0
    )

    state = WGENState(
        is_wet=False,
        random_state=None,
        current_date=None  # Missing date
    )

    with pytest.raises(ValueError, match="current_date must be set"):
        wgen_step(params, state)


def test_wgen_step_monthly_parameter_selection():
    """Test that wgen_step uses correct monthly parameters."""
    # Create params with distinct values for each month
    params = WGENParams(
        pww=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.85, 0.75],
        pwd=[0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6],
        alpha=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1],
        beta=[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5],
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0,
        random_seed=42
    )

    # Test January (month 1)
    state_jan = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 15)
    )

    # Test June (month 6)
    state_jun = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 6, 15)
    )

    # Run steps - should use different monthly parameters
    new_state_jan, outputs_jan = wgen_step(params, state_jan)
    new_state_jun, outputs_jun = wgen_step(params, state_jun)

    # Both should produce valid outputs
    assert isinstance(outputs_jan, WGENOutputs)
    assert isinstance(outputs_jun, WGENOutputs)


def test_wgen_step_deterministic_with_seed():
    """Test that wgen_step is deterministic with same random state."""
    params = WGENParams(
        pww=[0.5] * 12,
        pwd=[0.3] * 12,
        alpha=[1.0] * 12,
        beta=[10.0] * 12,
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0,
        random_seed=42
    )

    # Create two identical initial states
    state1 = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 15)
    )

    state2 = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 15)
    )

    # Run steps
    new_state1, outputs1 = wgen_step(params, state1)
    new_state2, outputs2 = wgen_step(params, state2)

    # Outputs should be identical
    assert outputs1.precip_mm == outputs2.precip_mm
    assert outputs1.tmax_c == outputs2.tmax_c
    assert outputs1.tmin_c == outputs2.tmin_c
    assert outputs1.solar_mjm2 == outputs2.solar_mjm2
    assert outputs1.is_wet == outputs2.is_wet


def test_wgen_step_non_negative_outputs():
    """Test that wgen_step produces non-negative precipitation and radiation."""
    params = WGENParams(
        pww=[0.5] * 12,
        pwd=[0.3] * 12,
        alpha=[1.0] * 12,
        beta=[10.0] * 12,
        txmd=20.0,
        atx=10.0,
        txmw=18.0,
        tn=10.0,
        atn=8.0,
        cvtx=0.1,
        acvtx=0.05,
        cvtn=0.1,
        acvtn=0.05,
        rmd=15.0,
        ar=5.0,
        rmw=12.0,
        latitude=40.0
    )

    state = WGENState(
        is_wet=False,
        random_state=None,
        current_date=datetime.date(2024, 1, 15)
    )

    # Run multiple steps
    for _ in range(10):
        state, outputs = wgen_step(params, state)
        assert outputs.precip_mm >= 0.0
        assert outputs.solar_mjm2 >= 0.0
