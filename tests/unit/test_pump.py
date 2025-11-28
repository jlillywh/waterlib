"""
Unit tests for Pump component.
"""

import pytest
from datetime import datetime
from waterlib.components.pump import Pump
from waterlib.core.exceptions import ConfigurationError


class TestPumpInitialization:
    """Test Pump component initialization and validation."""

    def test_pump_deadband_mode(self):
        """Test Pump initialization with deadband mode."""
        pump = Pump(
            name='test_pump',
            control_mode='deadband',
            capacity=50000,
            process_variable='reservoir.elevation',
            target=100.0,
            deadband=2.0
        )

        assert pump.control_mode == 'deadband'
        assert pump.capacity == 50000
        assert pump.deadband == 2.0
        assert pump.kp is None
        assert pump.target_constant == 100.0

    def test_pump_proportional_mode(self):
        """Test Pump initialization with proportional mode."""
        pump = Pump(
            name='test_pump',
            control_mode='proportional',
            capacity=50000,
            process_variable='reservoir.storage',
            target=1000000,
            kp=0.1
        )

        assert pump.control_mode == 'proportional'
        assert pump.capacity == 50000
        assert pump.kp == 0.1
        assert pump.deadband is None
        assert pump.target_constant == 1000000

    def test_pump_seasonal_target(self):
        """Test Pump initialization with seasonal target schedule."""
        pump = Pump(
            name='test_pump',
            control_mode='proportional',
            capacity=50000,
            process_variable='reservoir.storage',
            target={
                1: 1000000,
                182: 1500000,
                365: 1000000
            },
            kp=0.1
        )

        assert pump.target_constant is None
        assert pump.target_schedule is not None
        assert len(pump.target_schedule) == 3
        assert pump.target_schedule[0] == (1, 1000000)

    def test_pump_missing_required_parameter(self):
        """Test that Pump raises error when required parameter is missing."""
        with pytest.raises(ConfigurationError, match="configuration error"):
            Pump(
                name='test_pump',
                control_mode='deadband',
                capacity=50000,
                process_variable='reservoir.elevation'
                # Missing 'target'
            )

    def test_pump_invalid_control_mode(self):
        """Test that Pump raises error with invalid control mode."""
        with pytest.raises(ConfigurationError, match="control_mode must be"):
            Pump(
                name='test_pump',
                control_mode='invalid_mode',
                capacity=50000,
                process_variable='reservoir.elevation',
                target=100.0
            )

    def test_pump_negative_capacity(self):
        """Test that Pump raises error with negative capacity."""
        with pytest.raises(ConfigurationError, match="greater than or equal to 0"):
            Pump(
                name='test_pump',
                control_mode='deadband',
                capacity=-50000,
                process_variable='reservoir.elevation',
                target=100.0,
                deadband=2.0
            )

    def test_pump_deadband_mode_missing_deadband(self):
        """Test that deadband mode requires deadband parameter."""
        with pytest.raises(ConfigurationError, match="deadband mode requires 'deadband'"):
            Pump(
                name='test_pump',
                control_mode='deadband',
                capacity=50000,
                process_variable='reservoir.elevation',
                target=100.0
                # Missing 'deadband'
            )

    def test_pump_proportional_mode_missing_kp(self):
        """Test that proportional mode requires kp parameter."""
        with pytest.raises(ConfigurationError, match="proportional mode requires 'kp'"):
            Pump(
                name='test_pump',
                control_mode='proportional',
                capacity=50000,
                process_variable='reservoir.storage',
                target=1000000
                # Missing 'kp'
            )

    def test_pump_invalid_target_schedule(self):
        """Test that invalid target schedule raises error."""
        with pytest.raises(ConfigurationError, match="day-of-year must be between"):
            Pump(
                name='test_pump',
                control_mode='proportional',
                capacity=50000,
                process_variable='reservoir.storage',
                target={
                    0: 1000000,  # Invalid: day must be >= 1
                    182: 1500000
                },
                kp=0.1
            )

    def test_pump_type_coercion(self):
        """Test that Pydantic handles type coercion (string to float)."""
        pump = Pump(
            name='test_pump',
            control_mode='deadband',
            capacity="50000",  # String instead of float
            process_variable='reservoir.elevation',
            target="100.0",  # String instead of float
            deadband="2.0"  # String instead of float
        )

        assert pump.capacity == 50000.0
        assert pump.target_constant == 100.0
        assert pump.deadband == 2.0


class TestPumpOperation:
    """Test Pump component operation during simulation."""

    def test_pump_deadband_on(self):
        """Test deadband pump turns ON when error exceeds deadband."""
        pump = Pump(
            name='test_pump',
            control_mode='deadband',
            capacity=50000,
            process_variable='reservoir.elevation',
            target=100.0,
            deadband=2.0
        )

        # Mock input: current elevation = 95.0, error = 5.0 > deadband
        pump.inputs['reservoir.elevation'] = 95.0

        date = datetime(2020, 1, 1)
        outputs = pump.step(date, {})

        assert outputs['pumped_flow'] == 50000  # Full capacity
        assert outputs['error'] == 5.0  # target - current
        assert outputs['target_value'] == 100.0

    def test_pump_deadband_off(self):
        """Test deadband pump turns OFF when within deadband."""
        pump = Pump(
            name='test_pump',
            control_mode='deadband',
            capacity=50000,
            process_variable='reservoir.elevation',
            target=100.0,
            deadband=2.0
        )

        # Mock input: current elevation = 99.0, error = 1.0 < deadband
        pump.inputs['reservoir.elevation'] = 99.0

        date = datetime(2020, 1, 1)
        outputs = pump.step(date, {})

        assert outputs['pumped_flow'] == 0.0  # Off
        assert outputs['error'] == 1.0

    def test_pump_proportional_control(self):
        """Test proportional pump flow calculation."""
        pump = Pump(
            name='test_pump',
            control_mode='proportional',
            capacity=50000,
            process_variable='reservoir.storage',
            target=1000000,
            kp=0.1
        )

        # Mock input: current storage = 900000, error = 100000
        pump.inputs['reservoir.storage'] = 900000

        date = datetime(2020, 1, 1)
        outputs = pump.step(date, {})

        # Flow = kp * error = 0.1 * 100000 = 10000
        assert outputs['pumped_flow'] == 10000
        assert outputs['error'] == 100000

    def test_pump_proportional_clamped_to_capacity(self):
        """Test proportional pump clamps to max capacity."""
        pump = Pump(
            name='test_pump',
            control_mode='proportional',
            capacity=50000,
            process_variable='reservoir.storage',
            target=1000000,
            kp=0.1
        )

        # Mock input: large error that would exceed capacity
        pump.inputs['reservoir.storage'] = 0  # Error = 1000000

        date = datetime(2020, 1, 1)
        outputs = pump.step(date, {})

        # Flow should be clamped to capacity
        assert outputs['pumped_flow'] == 50000  # Clamped
        assert outputs['error'] == 1000000
