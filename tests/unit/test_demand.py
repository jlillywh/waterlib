"""Unit tests for Demand component."""

import pytest
from datetime import datetime

from waterlib.components.demand import Demand
from waterlib.core.exceptions import ConfigurationError


class TestDemandInitialization:
    """Test Demand component initialization and validation."""

    def test_municipal_mode_basic(self):
        """Test municipal mode with indoor demand only."""
        demand = Demand(
            name='city',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150
        )
        assert demand.mode == 'municipal'
        assert demand.population == 50000
        assert demand.per_capita_demand_lpd == 150
        assert demand.indoor_demand == 150  # Backward compatibility alias
        assert demand.outdoor_area == 0.0
        assert demand.outdoor_coefficient == 0.8

    def test_municipal_mode_with_outdoor(self):
        """Test municipal mode with indoor and outdoor components."""
        demand = Demand(
            name='city',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150,
            outdoor_area=25,
            outdoor_coefficient=0.7
        )
        assert demand.outdoor_area == 25
        assert demand.outdoor_coefficient == 0.7

    def test_agricultural_mode(self):
        """Test agricultural mode initialization."""
        demand = Demand(
            name='farm',
            mode='agricultural',
            irrigated_area=500,
            crop_coefficient=0.8
        )
        assert demand.mode == 'agricultural'
        assert demand.irrigated_area == 500
        assert demand.crop_coefficient == 0.8

    def test_mode_case_insensitive(self):
        """Test that mode parameter is case-insensitive."""
        demand = Demand(
            name='test',
            mode='MUNICIPAL',
            population=1000,
            per_capita_demand_lpd=100
        )
        assert demand.mode == 'municipal'

    def test_type_coercion(self):
        """Test automatic type coercion from strings."""
        demand = Demand(
            name='test',
            mode='municipal',
            population='50000',  # String
            per_capita_demand_lpd='150'  # String
        )
        assert demand.population == 50000
        assert demand.per_capita_demand_lpd == 150

    def test_backward_compatible_indoor_demand(self):
        """Test backward compatibility with deprecated 'indoor_demand' parameter."""
        demand = Demand(
            name='test',
            mode='municipal',
            population=10000,
            indoor_demand=120  # Deprecated name
        )
        assert demand.per_capita_demand_lpd == 120
        assert demand.indoor_demand == 120


class TestDemandValidation:
    """Test Demand parameter validation."""

    def test_missing_mode(self):
        """Test error when mode parameter is missing."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(name='test', population=1000)

    def test_invalid_mode(self):
        """Test error for invalid mode value."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(name='test', mode='industrial', population=1000)

    def test_municipal_missing_population(self):
        """Test error when population is missing in municipal mode."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='municipal',
                per_capita_demand_lpd=150
            )

    def test_municipal_missing_demand_parameter(self):
        """Test error when per_capita_demand_lpd is missing in municipal mode."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='municipal',
                population=50000
            )

    def test_agricultural_missing_irrigated_area(self):
        """Test error when irrigated_area is missing in agricultural mode."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='agricultural',
                crop_coefficient=0.8
            )

    def test_agricultural_missing_crop_coefficient(self):
        """Test error when crop_coefficient is missing in agricultural mode."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='agricultural',
                irrigated_area=500
            )

    def test_negative_population(self):
        """Test error for negative population."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='municipal',
                population=-1000,
                per_capita_demand_lpd=150
            )

    def test_negative_per_capita_demand(self):
        """Test error for negative per_capita_demand_lpd."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='municipal',
                population=50000,
                per_capita_demand_lpd=-150
            )

    def test_negative_outdoor_area(self):
        """Test error for negative outdoor_area."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='municipal',
                population=50000,
                per_capita_demand_lpd=150,
                outdoor_area=-10
            )

    def test_negative_irrigated_area(self):
        """Test error for negative irrigated_area."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            Demand(
                name='test',
                mode='agricultural',
                irrigated_area=-500,
                crop_coefficient=0.8
            )


class TestDemandOperation:
    """Test Demand component operational behavior."""

    def test_municipal_indoor_only(self):
        """Test municipal demand calculation with indoor only."""
        demand = Demand(
            name='city',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150
        )

        # Indoor demand = 50,000 × 150 / 1000 = 7,500 m³/day
        global_data = {'et0': 5.0}
        result = demand.step(datetime(2023, 6, 15), global_data)

        assert result['demand'] == 7500.0
        assert result['indoor_demand'] == 7500.0
        assert result['outdoor_demand'] == 0.0

    def test_municipal_with_outdoor(self):
        """Test municipal demand with indoor and outdoor components."""
        demand = Demand(
            name='city',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150,
            outdoor_area=25,  # hectares
            outdoor_coefficient=0.8
        )

        global_data = {'et0': 5.0}  # mm/day
        result = demand.step(datetime(2023, 6, 15), global_data)

        # Indoor = 50,000 × 150 / 1000 = 7,500 m³/day
        # Outdoor = 25 ha × 0.8 × 5 mm/day × 10 = 1,000 m³/day
        # Total = 8,500 m³/day
        assert result['demand'] == 8500.0
        assert result['indoor_demand'] == 7500.0
        assert result['outdoor_demand'] == 1000.0

    def test_agricultural_demand(self):
        """Test agricultural demand calculation."""
        demand = Demand(
            name='farm',
            mode='agricultural',
            irrigated_area=500,  # hectares
            crop_coefficient=0.8
        )

        global_data = {'et0': 6.0}  # mm/day
        result = demand.step(datetime(2023, 7, 1), global_data)

        # Demand = 500 ha × 0.8 × 6 mm/day × 10 = 24,000 m³/day
        assert result['demand'] == 24000.0

    def test_supply_limited(self):
        """Test that supply is limited by available supply."""
        demand = Demand(
            name='test',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150
        )

        demand.inputs['available_supply'] = 5000  # Less than demand
        global_data = {'et0': 5.0}
        result = demand.step(datetime(2023, 6, 15), global_data)

        # Demand = 7,500 m³/day, Available = 5,000 m³/day
        assert result['demand'] == 7500.0
        assert result['supplied'] == 5000.0
        assert result['deficit'] == 2500.0

    def test_supply_exceeds_demand(self):
        """Test that supply cannot exceed demand."""
        demand = Demand(
            name='test',
            mode='municipal',
            population=50000,
            per_capita_demand_lpd=150
        )

        demand.inputs['available_supply'] = 10000  # More than demand
        global_data = {'et0': 5.0}
        result = demand.step(datetime(2023, 6, 15), global_data)

        # Demand = 7,500 m³/day, Supplied = min(7,500, 10,000) = 7,500
        assert result['demand'] == 7500.0
        assert result['supplied'] == 7500.0
        assert result['deficit'] == 0.0

    def test_zero_et0(self):
        """Test demand calculation with zero ET0."""
        demand = Demand(
            name='farm',
            mode='agricultural',
            irrigated_area=500,
            crop_coefficient=0.8
        )

        global_data = {'et0': 0.0}
        result = demand.step(datetime(2023, 1, 15), global_data)

        # Demand = 500 × 0.8 × 0 × 10 = 0
        assert result['demand'] == 0.0
