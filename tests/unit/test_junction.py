"""Unit tests for Junction component."""

import pytest
from datetime import datetime

from waterlib.components.junction import Junction
from waterlib.core.exceptions import ConfigurationError


class TestJunctionInitialization:
    """Test Junction component initialization and validation."""

    def test_basic_junction(self):
        """Test basic junction initialization with no parameters."""
        junction = Junction(name='confluence')
        assert junction.name == 'confluence'
        assert junction.outputs['outflow'] == 0.0

    def test_junction_with_meta(self):
        """Test junction initialization with metadata."""
        meta = {'description': 'Tributary confluence', 'color': 'blue'}
        junction = Junction(name='confluence', meta=meta)
        assert junction.name == 'confluence'
        assert junction.meta == meta

    def test_junction_rejects_unexpected_params(self):
        """Test that junction rejects unexpected parameters."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Junction(name='test', unexpected_param=123)


class TestJunctionOperation:
    """Test Junction component operational behavior."""

    def test_single_inflow(self):
        """Test aggregation with single inflow."""
        junction = Junction(name='test')
        junction.inputs['inflow_1'] = 1000.0

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 1000.0

    def test_multiple_inflows(self):
        """Test aggregation with multiple inflows."""
        junction = Junction(name='test')
        junction.inputs['inflow_1'] = 1000.0
        junction.inputs['inflow_2'] = 2500.0
        junction.inputs['inflow_3'] = 1500.0

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 5000.0

    def test_zero_inflows(self):
        """Test junction with zero inflows."""
        junction = Junction(name='test')

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 0.0

    def test_negative_inflows(self):
        """Test that negative flows are correctly summed."""
        junction = Junction(name='test')
        junction.inputs['inflow_1'] = 1000.0
        junction.inputs['inflow_2'] = -200.0  # Withdrawal or reverse flow
        junction.inputs['inflow_3'] = 500.0

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 1300.0

    def test_type_coercion(self):
        """Test automatic type coercion of input values."""
        junction = Junction(name='test')
        junction.inputs['inflow_1'] = '1000'  # String
        junction.inputs['inflow_2'] = 2500  # Int
        junction.inputs['inflow_3'] = 1500.0  # Float

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 5000.0

    def test_dynamic_inputs(self):
        """Test that junction handles dynamically added inputs."""
        junction = Junction(name='test')

        # Start with one input
        junction.inputs['tributary_a'] = 1000.0
        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 1000.0

        # Add more inputs dynamically
        junction.inputs['tributary_b'] = 1500.0
        junction.inputs['tributary_c'] = 2000.0
        result = junction.step(datetime(2023, 6, 2), {})
        assert result['outflow'] == 4500.0

        # Remove an input
        del junction.inputs['tributary_b']
        result = junction.step(datetime(2023, 6, 3), {})
        assert result['outflow'] == 3000.0

    def test_large_number_of_inflows(self):
        """Test junction with many inflows."""
        junction = Junction(name='test')

        # Add 100 inflows of 100 m³/day each
        for i in range(100):
            junction.inputs[f'inflow_{i}'] = 100.0

        result = junction.step(datetime(2023, 6, 1), {})
        assert result['outflow'] == 10000.0

    def test_timestep_independence(self):
        """Test that each timestep is independent (stateless)."""
        junction = Junction(name='test')

        # Timestep 1: 3 inflows
        junction.inputs['inflow_1'] = 1000.0
        junction.inputs['inflow_2'] = 2000.0
        junction.inputs['inflow_3'] = 3000.0
        result1 = junction.step(datetime(2023, 6, 1), {})
        outflow_t1 = result1['outflow']
        assert outflow_t1 == 6000.0

        # Timestep 2: Different values
        junction.inputs['inflow_1'] = 500.0
        junction.inputs['inflow_2'] = 1000.0
        junction.inputs['inflow_3'] = 1500.0
        result2 = junction.step(datetime(2023, 6, 2), {})
        outflow_t2 = result2['outflow']
        assert outflow_t2 == 3000.0

        # Verify outputs were calculated correctly for each timestep
        assert outflow_t1 == 6000.0
        assert outflow_t2 == 3000.0
