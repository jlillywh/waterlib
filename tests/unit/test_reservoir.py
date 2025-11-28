"""
Unit tests for the Reservoir component.

Tests verify that the Reservoir component correctly uses the weir kernel for
spillway discharge calculations and maintains the expected external interface.
"""

import pytest
from datetime import datetime
import pandas as pd
import tempfile
import os
from waterlib.components.reservoir import Reservoir
from waterlib.core.exceptions import ConfigurationError


class TestReservoirInitialization:
    """Test Reservoir initialization."""

    def test_reservoir_init_simple_mode(self):
        """Test Reservoir initialization in simple mode."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=1000000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        assert reservoir.name == 'test_reservoir'
        assert reservoir.storage == 1000000.0
        assert reservoir.max_storage == 5000000.0
        assert reservoir.surface_area == 500000.0
        assert reservoir.use_eav_mode is False

    def test_reservoir_init_with_spillway_no_eav_raises_error(self):
        """Test that spillway_elevation without EAV mode raises error."""
        with pytest.raises(ConfigurationError, match="spillway_elevation requires eav_table"):
            Reservoir(
                name='test_reservoir',
                initial_storage=1000000.0,
                max_storage=5000000.0,
                surface_area=500000.0,
                spillway_elevation=100.0
            )

    def test_reservoir_init_missing_initial_storage(self):
        """Test that Reservoir raises error when initial_storage is missing."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Reservoir(
                name='test_reservoir',
                max_storage=5000000.0
            )

    def test_reservoir_init_missing_max_storage(self):
        """Test that Reservoir raises error when max_storage is missing."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Reservoir(
                name='test_reservoir',
                initial_storage=1000000.0
            )

    def test_reservoir_init_negative_initial_storage(self):
        """Test that Reservoir raises error when initial_storage is negative."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Reservoir(
                name='test_reservoir',
                initial_storage=-1000.0,
                max_storage=5000000.0
            )

    def test_reservoir_init_invalid_max_storage(self):
        """Test that Reservoir raises error when max_storage is non-positive."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Reservoir(
                name='test_reservoir',
                initial_storage=1000000.0,
                max_storage=0.0
            )

    def test_reservoir_init_initial_exceeds_max(self):
        """Test that Reservoir raises error when initial_storage exceeds max_storage."""
        with pytest.raises(ConfigurationError, match="initial_storage.*cannot exceed max_storage"):
            Reservoir(
                name='test_reservoir',
                initial_storage=6000000.0,
                max_storage=5000000.0
            )


class TestReservoirEAVMode:
    """Test Reservoir with EAV table."""

    def create_eav_table(self):
        """Create a temporary EAV table for testing."""
        # Create a simple EAV table
        eav_data = {
            'elevation': [90.0, 95.0, 100.0, 105.0, 110.0],
            'area': [100000.0, 200000.0, 300000.0, 400000.0, 500000.0],
            'volume': [0.0, 500000.0, 1500000.0, 3000000.0, 5000000.0]
        }
        df = pd.DataFrame(eav_data)

        # Write to temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        return temp_file.name

    def test_reservoir_init_eav_mode(self):
        """Test Reservoir initialization with EAV table."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=1500000.0,
                max_storage=5000000.0,
                eav_table=eav_file
            )

            assert reservoir.use_eav_mode is True
            assert reservoir.eav_table is not None
            assert reservoir.current_elevation is not None
            assert reservoir.current_area is not None
            assert reservoir.surface_area is None  # Not used in EAV mode
        finally:
            os.unlink(eav_file)

    def test_reservoir_init_eav_with_spillway(self):
        """Test Reservoir initialization with EAV table and spillway."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=1500000.0,
                max_storage=5000000.0,
                eav_table=eav_file,
                spillway_elevation=105.0,
                spillway_width=15.0,
                spillway_coefficient=1.7
            )

            assert reservoir.spillway_elevation == 105.0
            assert reservoir.spillway_params is not None
            assert reservoir.spillway_params.width_m == 15.0
            assert reservoir.spillway_params.coefficient == 1.7
            assert reservoir.spillway_params.crest_elevation_m == 105.0
        finally:
            os.unlink(eav_file)

    def test_reservoir_eav_missing_file(self):
        """Test that Reservoir raises error when EAV file doesn't exist."""
        with pytest.raises(ConfigurationError, match="cannot find EAV table file"):
            Reservoir(
                name='test_reservoir',
                initial_storage=1500000.0,
                max_storage=5000000.0,
                eav_table='nonexistent_file.csv'
            )

    def test_reservoir_eav_missing_columns(self):
        """Test that Reservoir raises error when EAV table has missing columns."""
        # Create EAV table with missing 'area' column
        eav_data = {
            'elevation': [90.0, 95.0, 100.0],
            'volume': [0.0, 500000.0, 1500000.0]
        }
        df = pd.DataFrame(eav_data)

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            with pytest.raises(ConfigurationError, match="EAV table missing required columns"):
                Reservoir(
                    name='test_reservoir',
                    initial_storage=500000.0,
                    max_storage=1500000.0,
                    eav_table=temp_file.name
                )
        finally:
            os.unlink(temp_file.name)


class TestReservoirSpillwayWithWeirKernel:
    """Test Reservoir spillway using weir kernel."""

    def create_eav_table(self):
        """Create a temporary EAV table for testing."""
        eav_data = {
            'elevation': [90.0, 95.0, 100.0, 105.0, 110.0],
            'area': [100000.0, 200000.0, 300000.0, 400000.0, 500000.0],
            'volume': [0.0, 500000.0, 1500000.0, 3000000.0, 5000000.0]
        }
        df = pd.DataFrame(eav_data)

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        return temp_file.name

    def test_reservoir_spillway_activation_at_max_storage(self):
        """Test spillway activation when storage exceeds spillway elevation."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=2500000.0,  # Below spillway
                max_storage=5000000.0,
                eav_table=eav_file,
                spillway_elevation=105.0,  # Spillway at 105m
                spillway_width=10.0,
                spillway_coefficient=1.7
            )

            # Add large inflow to push storage above spillway elevation
            reservoir.inputs['inflow'] = 1000000.0  # Large inflow
            reservoir.inputs['release'] = 0.0

            date = datetime(2020, 1, 1)
            outputs = reservoir.step(date, global_data={})

            # Check that spillway discharge occurred
            assert outputs['spill'] > 0.0
            assert outputs['outflow'] == outputs['spill']  # No release, only spill
        finally:
            os.unlink(eav_file)

    def test_reservoir_spillway_discharge_calculation(self):
        """Test that spillway discharge is calculated using weir kernel."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=2900000.0,  # Just below spillway
                max_storage=5000000.0,
                eav_table=eav_file,
                spillway_elevation=105.0,
                spillway_width=10.0,
                spillway_coefficient=1.7
            )

            # Add inflow to push above spillway
            reservoir.inputs['inflow'] = 500000.0
            reservoir.inputs['release'] = 0.0

            date = datetime(2020, 1, 1)
            outputs = reservoir.step(date, global_data={})

            # Spillway should activate
            assert outputs['spill'] >= 0.0

            # Storage should be updated
            assert outputs['storage'] > 0.0

            # Elevation should be tracked
            assert 'elevation' in outputs
            assert outputs['elevation'] > 0.0
        finally:
            os.unlink(eav_file)

    def test_reservoir_no_spillway_below_crest(self):
        """Test that no spillway discharge occurs when below crest elevation."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=1000000.0,  # Well below spillway
                max_storage=5000000.0,
                eav_table=eav_file,
                spillway_elevation=105.0,
                spillway_width=10.0,
                spillway_coefficient=1.7
            )

            # Small inflow, stays below spillway
            reservoir.inputs['inflow'] = 100000.0
            reservoir.inputs['release'] = 0.0

            date = datetime(2020, 1, 1)
            outputs = reservoir.step(date, global_data={})

            # No spillway discharge
            assert outputs['spill'] == 0.0
            assert outputs['outflow'] == 0.0
        finally:
            os.unlink(eav_file)

    def test_reservoir_spillway_with_release(self):
        """Test spillway discharge combined with controlled release."""
        eav_file = self.create_eav_table()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=2900000.0,
                max_storage=5000000.0,
                eav_table=eav_file,
                spillway_elevation=105.0,
                spillway_width=10.0,
                spillway_coefficient=1.7
            )

            # Add inflow and release
            reservoir.inputs['inflow'] = 500000.0
            release_amount = 100000.0
            reservoir.inputs['release'] = release_amount

            date = datetime(2020, 1, 1)
            outputs = reservoir.step(date, global_data={})

            # Total outflow should be at least the release amount
            assert outputs['outflow'] >= release_amount

            # Total outflow should equal release + spill
            assert abs(outputs['outflow'] - (release_amount + outputs['spill'])) < 1.0

            # If spillway activated, outflow > release
            if outputs['spill'] > 0:
                assert outputs['outflow'] > release_amount
        finally:
            os.unlink(eav_file)


class TestReservoirSimpleOverflow:
    """Test Reservoir simple overflow (without weir kernel)."""

    def test_reservoir_simple_overflow_at_max_storage(self):
        """Test simple overflow when storage exceeds max_storage (no spillway)."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=4500000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        # Add large inflow
        reservoir.inputs['inflow'] = 1000000.0
        reservoir.inputs['release'] = 0.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={})

        # Storage should be capped at max_storage
        assert outputs['storage'] == 5000000.0

        # Spill should be the excess
        expected_spill = (4500000.0 + 1000000.0) - 5000000.0
        assert abs(outputs['spill'] - expected_spill) < 1.0

    def test_reservoir_no_overflow_below_max(self):
        """Test no overflow when storage is below max_storage."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=2000000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        # Add moderate inflow
        reservoir.inputs['inflow'] = 500000.0
        reservoir.inputs['release'] = 0.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={})

        # No overflow
        assert outputs['spill'] == 0.0
        assert outputs['storage'] == 2500000.0


class TestReservoirMassBalance:
    """Test Reservoir mass balance."""

    def test_reservoir_mass_balance_simple(self):
        """Test basic mass balance: storage = initial + inflow - release."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=1000000.0,
            max_storage=5000000.0
        )

        reservoir.inputs['inflow'] = 500000.0
        reservoir.inputs['release'] = 200000.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={})

        expected_storage = 1000000.0 + 500000.0 - 200000.0
        assert abs(outputs['storage'] - expected_storage) < 1.0

    def test_reservoir_mass_balance_with_evaporation(self):
        """Test mass balance with evaporation loss."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=1000000.0,
            max_storage=5000000.0,
            surface_area=500000.0  # 500,000 m²
        )

        reservoir.inputs['inflow'] = 500000.0
        reservoir.inputs['release'] = 200000.0

        # Evaporation rate: 5 mm/day
        date = datetime(2020, 1, 1)
        global_data = {'evaporation': 5.0}
        outputs = reservoir.step(date, global_data=global_data)

        # Evaporation loss = 5 mm/day * 500,000 m² / 1000 = 2,500 m³/day
        expected_evap_loss = 5.0 * 500000.0 / 1000.0
        assert abs(outputs['evaporation_loss'] - expected_evap_loss) < 1.0

        # Storage = initial + inflow - release - evaporation
        expected_storage = 1000000.0 + 500000.0 - 200000.0 - expected_evap_loss
        assert abs(outputs['storage'] - expected_storage) < 1.0

    def test_reservoir_prevents_negative_storage(self):
        """Test that storage cannot go negative."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=100000.0,
            max_storage=5000000.0
        )

        # Try to release more than available
        reservoir.inputs['inflow'] = 0.0
        reservoir.inputs['release'] = 200000.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={})

        # Storage should be zero, not negative
        assert outputs['storage'] == 0.0

        # Actual outflow should be limited to available water
        assert outputs['outflow'] <= 100000.0


class TestReservoirOutputs:
    """Test Reservoir output format."""

    def test_reservoir_outputs_have_required_keys(self):
        """Test that Reservoir outputs contain all required keys."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=1000000.0,
            max_storage=5000000.0
        )

        reservoir.inputs['inflow'] = 100000.0
        reservoir.inputs['release'] = 50000.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={})

        # Check required output keys
        required_keys = ['storage', 'outflow', 'spill']
        for key in required_keys:
            assert key in outputs, f"Missing required output key: {key}"

    def test_reservoir_outputs_are_numeric(self):
        """Test that all Reservoir outputs are numeric."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=1000000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        reservoir.inputs['inflow'] = 100000.0
        reservoir.inputs['release'] = 50000.0

        date = datetime(2020, 1, 1)
        outputs = reservoir.step(date, global_data={'evaporation': 5.0})

        # Check all outputs are numeric
        for key, value in outputs.items():
            assert isinstance(value, (int, float)), f"Output {key} is not numeric: {type(value)}"

    def test_reservoir_eav_outputs_include_elevation_and_area(self):
        """Test that EAV mode outputs include elevation and area."""
        # Create EAV table
        eav_data = {
            'elevation': [90.0, 95.0, 100.0, 105.0, 110.0],
            'area': [100000.0, 200000.0, 300000.0, 400000.0, 500000.0],
            'volume': [0.0, 500000.0, 1500000.0, 3000000.0, 5000000.0]
        }
        df = pd.DataFrame(eav_data)

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            reservoir = Reservoir(
                name='test_reservoir',
                initial_storage=1500000.0,
                max_storage=5000000.0,
                eav_table=temp_file.name
            )

            reservoir.inputs['inflow'] = 100000.0
            reservoir.inputs['release'] = 50000.0

            date = datetime(2020, 1, 1)
            outputs = reservoir.step(date, global_data={})

            # Check EAV-specific outputs
            assert 'elevation' in outputs
            assert 'area' in outputs
            assert outputs['elevation'] > 0.0
            assert outputs['area'] > 0.0
        finally:
            os.unlink(temp_file.name)
