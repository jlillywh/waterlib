"""Unit tests for RiverDiversion component."""

import pytest
from datetime import datetime

from waterlib.components.diversion import RiverDiversion
from waterlib.core.exceptions import ConfigurationError


class TestRiverDiversionInitialization:
    """Test RiverDiversion component initialization and validation."""

    def test_simple_diversion(self):
        """Test basic diversion without outflows."""
        diversion = RiverDiversion(
            name='simple_div',
            max_diversion=10000
        )
        assert diversion.max_diversion == 10000
        assert diversion.instream_flow_requirement == 0.0
        assert len(diversion.outflow_specs) == 0

    def test_with_instream_flow(self):
        """Test diversion with instream flow requirement."""
        diversion = RiverDiversion(
            name='env_div',
            max_diversion=10000,
            instream_flow=2000
        )
        assert diversion.max_diversion == 10000
        assert diversion.instream_flow_requirement == 2000

    def test_with_single_outflow(self):
        """Test diversion with one outflow."""
        diversion = RiverDiversion(
            name='single_out',
            max_diversion=15000,
            outflows=[
                {'name': 'canal_a', 'priority': 1, 'demand': 5000}
            ]
        )
        assert len(diversion.outflow_specs) == 1
        assert diversion.outflow_specs[0] == ('canal_a', 1, 5000)

    def test_with_multiple_outflows(self):
        """Test diversion with multiple prioritized outflows."""
        diversion = RiverDiversion(
            name='multi_out',
            max_diversion=15000,
            instream_flow=3000,
            outflows=[
                {'name': 'municipal', 'priority': 1, 'demand': 5000},
                {'name': 'irrigation', 'priority': 2, 'demand': 8000},
                {'name': 'industrial', 'priority': 3, 'demand': 2000}
            ]
        )
        assert len(diversion.outflow_specs) == 3
        # Should be sorted by priority
        assert diversion.outflow_specs[0][0] == 'municipal'
        assert diversion.outflow_specs[1][0] == 'irrigation'
        assert diversion.outflow_specs[2][0] == 'industrial'

    def test_priority_sorting(self):
        """Test that outflows are sorted by priority."""
        diversion = RiverDiversion(
            name='sorted',
            max_diversion=10000,
            outflows=[
                {'name': 'low', 'priority': 3, 'demand': 1000},
                {'name': 'high', 'priority': 1, 'demand': 2000},
                {'name': 'medium', 'priority': 2, 'demand': 1500}
            ]
        )
        # Should be sorted by priority: high (1), medium (2), low (3)
        assert diversion.outflow_specs[0][0] == 'high'
        assert diversion.outflow_specs[1][0] == 'medium'
        assert diversion.outflow_specs[2][0] == 'low'

    def test_type_coercion(self):
        """Test automatic type coercion from strings."""
        diversion = RiverDiversion(
            name='test',
            max_diversion='10000',  # String
            instream_flow='2000'  # String
        )
        assert diversion.max_diversion == 10000
        assert diversion.instream_flow_requirement == 2000


class TestRiverDiversionValidation:
    """Test RiverDiversion parameter validation."""

    def test_missing_max_diversion(self):
        """Test error when max_diversion is missing."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(name='test', instream_flow=1000)

    def test_negative_max_diversion(self):
        """Test error for negative max_diversion."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(name='test', max_diversion=-1000)

    def test_negative_instream_flow(self):
        """Test error for negative instream_flow."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(name='test', max_diversion=10000, instream_flow=-500)

    def test_missing_outflow_name(self):
        """Test error when outflow missing name field."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(
                name='test',
                max_diversion=10000,
                outflows=[
                    {'priority': 1, 'demand': 5000}  # Missing 'name'
                ]
            )

    def test_missing_outflow_priority(self):
        """Test error when outflow missing priority field."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(
                name='test',
                max_diversion=10000,
                outflows=[
                    {'name': 'canal', 'demand': 5000}  # Missing 'priority'
                ]
            )

    def test_missing_outflow_demand(self):
        """Test error when outflow missing demand field."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(
                name='test',
                max_diversion=10000,
                outflows=[
                    {'name': 'canal', 'priority': 1}  # Missing 'demand'
                ]
            )

    def test_priority_less_than_one(self):
        """Test error for priority < 1."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(
                name='test',
                max_diversion=10000,
                outflows=[
                    {'name': 'canal', 'priority': 0, 'demand': 5000}
                ]
            )

    def test_negative_demand(self):
        """Test error for negative demand."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            RiverDiversion(
                name='test',
                max_diversion=10000,
                outflows=[
                    {'name': 'canal', 'priority': 1, 'demand': -5000}
                ]
            )


class TestRiverDiversionOperation:
    """Test RiverDiversion component operational behavior."""

    def test_simple_diversion_no_constraints(self):
        """Test simple diversion with abundant flow."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=10000
        )

        diversion.inputs['river_flow'] = 20000
        result = diversion.step(datetime(2023, 6, 1), {})

        # Should divert up to max_diversion
        assert result['diverted_flow'] == 10000
        assert result['remaining_flow'] == 10000
        assert result['instream_flow'] == 0.0

    def test_diversion_limited_by_available_flow(self):
        """Test diversion when river flow is less than max."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=10000
        )

        diversion.inputs['river_flow'] = 6000
        result = diversion.step(datetime(2023, 6, 1), {})

        # Can only divert what's available
        assert result['diverted_flow'] == 6000
        assert result['remaining_flow'] == 0.0

    def test_instream_flow_priority(self):
        """Test that instream flow has highest priority."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=10000,
            instream_flow=3000
        )

        diversion.inputs['river_flow'] = 5000
        result = diversion.step(datetime(2023, 6, 1), {})

        # Instream flow satisfied first, remaining 2000 diverted
        assert result['instream_flow'] == 3000
        assert result['diverted_flow'] == 2000
        assert result['remaining_flow'] == 0.0

    def test_insufficient_flow_for_instream(self):
        """Test when river flow cannot meet instream requirement."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=10000,
            instream_flow=5000
        )

        diversion.inputs['river_flow'] = 3000
        result = diversion.step(datetime(2023, 6, 1), {})

        # All flow goes to instream, nothing to divert
        assert result['instream_flow'] == 3000
        assert result['diverted_flow'] == 0.0
        assert result['remaining_flow'] == 0.0

    def test_priority_allocation_full_supply(self):
        """Test priority-based allocation with sufficient flow."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=15000,
            outflows=[
                {'name': 'high', 'priority': 1, 'demand': 5000},
                {'name': 'low', 'priority': 2, 'demand': 3000}
            ]
        )

        diversion.inputs['river_flow'] = 20000
        result = diversion.step(datetime(2023, 6, 1), {})

        # Both demands satisfied
        assert result['high'] == 5000
        assert result['high_deficit'] == 0.0
        assert result['low'] == 3000
        assert result['low_deficit'] == 0.0
        assert result['diverted_flow'] == 8000
        assert result['remaining_flow'] == 12000

    def test_priority_allocation_partial_supply(self):
        """Test priority allocation with shortage."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=15000,
            outflows=[
                {'name': 'high', 'priority': 1, 'demand': 5000},
                {'name': 'low', 'priority': 2, 'demand': 8000}
            ]
        )

        diversion.inputs['river_flow'] = 8000
        result = diversion.step(datetime(2023, 6, 1), {})

        # High priority gets full demand, low priority gets remainder
        assert result['high'] == 5000
        assert result['high_deficit'] == 0.0
        assert result['low'] == 3000  # Only 3000 left after high priority
        assert result['low_deficit'] == 5000
        assert result['diverted_flow'] == 8000
        assert result['remaining_flow'] == 0.0

    def test_priority_allocation_with_instream(self):
        """Test priority allocation with instream flow requirement."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=15000,
            instream_flow=2000,
            outflows=[
                {'name': 'municipal', 'priority': 1, 'demand': 5000},
                {'name': 'irrigation', 'priority': 2, 'demand': 8000}
            ]
        )

        diversion.inputs['river_flow'] = 10000
        result = diversion.step(datetime(2023, 6, 1), {})

        # Instream (2000) + municipal (5000) + irrigation (3000) = 10000
        assert result['instream_flow'] == 2000
        assert result['municipal'] == 5000
        assert result['municipal_deficit'] == 0.0
        assert result['irrigation'] == 3000  # Only 3000 available after instream and municipal
        assert result['irrigation_deficit'] == 5000
        assert result['diverted_flow'] == 8000
        assert result['remaining_flow'] == 0.0

    def test_zero_river_flow(self):
        """Test behavior with zero river flow."""
        diversion = RiverDiversion(
            name='test',
            max_diversion=10000,
            instream_flow=1000,
            outflows=[
                {'name': 'canal', 'priority': 1, 'demand': 5000}
            ]
        )

        diversion.inputs['river_flow'] = 0.0
        result = diversion.step(datetime(2023, 6, 1), {})

        # Nothing to allocate
        assert result['instream_flow'] == 0.0
        assert result['canal'] == 0.0
        assert result['canal_deficit'] == 5000
        assert result['diverted_flow'] == 0.0
        assert result['remaining_flow'] == 0.0
