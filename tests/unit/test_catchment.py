"""
Unit tests for the Catchment component.

Tests verify that the Catchment component correctly orchestrates Snow17 and AWBM
kernels and maintains the expected external interface.
"""

import pytest
from datetime import datetime
from waterlib.components.catchment import Catchment
from waterlib.core.exceptions import ConfigurationError


# Mock driver for testing
class MockDriver:
    """Mock climate driver for testing."""
    def __init__(self, value):
        self.value = value

    def get_value(self, date):
        return self.value


class MockClimateDrivers:
    """Mock ClimateDrivers namespace for type-safe API testing."""
    def __init__(self, precipitation=0.0, temperature=0.0, et=0.0):
        self.precipitation = MockDriver(precipitation)
        self.temperature = MockDriver(temperature)
        self.et = MockDriver(et)


class MockDriverRegistry:
    """Mock DriverRegistry supporting both legacy and new API."""
    def __init__(self, precipitation=0.0, temperature=0.0, et=0.0):
        # Legacy API support
        self.drivers = {
            'precipitation': MockDriver(precipitation),
            'temperature': MockDriver(temperature),
            'et': MockDriver(et)
        }
        # New type-safe API support
        self.climate = MockClimateDrivers(precipitation, temperature, et)

    def get(self, name):
        """Legacy API method."""
        return self.drivers.get(name, MockDriver(0.0))


class TestCatchmentInitialization:
    """Test Catchment initialization with kernel parameters."""

    def test_catchment_init_with_snow_and_awbm(self):
        """Test Catchment initialization with both Snow17 and AWBM parameters."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow17_params={
                'latitude': 45.0,
                'elevation': 1500.0,
                'ref_elevation': 1000.0,
                'mfmax': 1.2,
                'mfmin': 0.6,
                'scf': 1.1
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        assert catchment.name == 'test_catchment'
        assert catchment.area == 100.0
        assert catchment.has_snow is True
        assert catchment.snow17_params is not None
        assert catchment.snow17_params.mfmax == 1.2
        assert catchment.snow17_params.scf == 1.1
        assert catchment.awbm_params is not None
        assert catchment.awbm_params.c_vec == [7.5, 76.0, 152.0]
        assert catchment.awbm_params.bfi == 0.35

    def test_catchment_init_without_snow(self):
        """Test Catchment initialization without Snow17 (snow_params=None)."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        assert catchment.name == 'test_catchment'
        assert catchment.area == 100.0
        assert catchment.has_snow is False
        assert catchment.snow17_params is None
        assert catchment.snow17_state is None
        assert catchment.awbm_params is not None

    def test_catchment_init_with_area_km2(self):
        """Test Catchment initialization with area_km2 parameter."""
        catchment = Catchment(
            name='test_catchment',
            area_km2=150.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        assert catchment.area == 150.0

    def test_catchment_init_missing_area(self):
        """Test that Catchment raises error when area is missing."""
        with pytest.raises(ConfigurationError, match="missing required parameter 'area'"):
            Catchment(
                name='test_catchment',
                awbm_params={
                    'c_vec': [7.5, 76.0, 152.0],
                    'bfi': 0.35,
                    'ks': 0.35,
                    'kb': 0.95
                }
            )

    def test_catchment_init_negative_area(self):
        """Test that Catchment raises error when area is negative."""
        with pytest.raises(ConfigurationError, match="(area|greater than 0)"):
            Catchment(
                name='test_catchment',
                area=-10.0,
                awbm_params={
                    'c_vec': [7.5, 76.0, 152.0],
                    'bfi': 0.35,
                    'ks': 0.35,
                    'kb': 0.95
                }
            )

    def test_catchment_init_missing_awbm_params(self):
        """Test that Catchment raises error when awbm_params is missing."""
        with pytest.raises(ConfigurationError, match="(awbm_params|Field required)"):
            Catchment(
                name='test_catchment',
                area=100.0
            )

    def test_catchment_init_missing_c_vec(self):
        """Test that Catchment raises error when c_vec is missing from awbm_params."""
        with pytest.raises(ConfigurationError, match="(c_vec|Field required)"):
            Catchment(
                name='test_catchment',
                area=100.0,
                snow_params=None,
                awbm_params={
                    'bfi': 0.35,
                    'ks': 0.35,
                    'kb': 0.95
                }
            )

    def test_catchment_init_with_initial_stores_list(self):
        """Test Catchment initialization with initial_stores as list."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'initial_stores': [1.0, 2.0, 3.0, 4.0, 5.0]
            }
        )

        assert catchment.awbm_state.ss1 == 1.0
        assert catchment.awbm_state.ss2 == 2.0
        assert catchment.awbm_state.ss3 == 3.0
        assert catchment.awbm_state.s_surf == 4.0
        assert catchment.awbm_state.b_base == 5.0

    def test_catchment_init_with_initial_stores_dict(self):
        """Test Catchment initialization with initial_stores as dict."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'initial_stores': {
                    'ss1': 1.5,
                    'ss2': 2.5,
                    'ss3': 3.5,
                    's_surf': 4.5,
                    'b_base': 5.5
                }
            }
        )

        assert catchment.awbm_state.ss1 == 1.5
        assert catchment.awbm_state.ss2 == 2.5
        assert catchment.awbm_state.ss3 == 3.5
        assert catchment.awbm_state.s_surf == 4.5
        assert catchment.awbm_state.b_base == 5.5


class TestCatchmentStep:
    """Test Catchment.step orchestrates both kernels correctly."""

    def test_catchment_step_with_snow_and_awbm(self):
        """Test that Catchment.step orchestrates Snow17 and AWBM kernels."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow17_params={
                'latitude': 45.0,
                'elevation': 1500.0,
                'ref_elevation': 1000.0,
                'mfmax': 1.2,
                'mfmin': 0.6,
                'scf': 1.0
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Run a timestep with cold temperature (snow accumulation)
        date = datetime(2020, 1, 15)
        drivers = MockDriverRegistry(
            precipitation=10.0,  # mm
            temperature=-5.0,    # deg C
            et=1.0               # mm
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check that outputs are present
        assert 'runoff' in outputs
        assert 'runoff_mm' in outputs
        assert 'snow_water_equivalent' in outputs
        assert 'swe_mm' in outputs

        # At cold temperature, snow should accumulate
        assert outputs['swe_mm'] > 0.0

        # Runoff should be minimal (no melt)
        assert outputs['runoff_mm'] >= 0.0

    def test_catchment_step_without_snow(self):
        """Test that Catchment.step works without Snow17."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Run a timestep
        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=20.0,  # mm
            temperature=20.0,    # deg C
            et=5.0               # mm
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check that outputs are present
        assert 'runoff' in outputs
        assert 'runoff_mm' in outputs
        assert 'snow_water_equivalent' in outputs
        assert 'swe_mm' in outputs

        # No snow processing, so SWE should be 0
        assert outputs['swe_mm'] == 0.0

        # Runoff should be positive with precipitation
        assert outputs['runoff_mm'] >= 0.0

    def test_catchment_step_warm_temperature_melt(self):
        """Test that Catchment produces melt at warm temperatures."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow17_params={
                'latitude': 45.0,
                'elevation': 1500.0,
                'ref_elevation': 1000.0,
                'mfmax': 1.2,
                'mfmin': 0.6,
                'scf': 1.0,
                'initial_swe': 50.0  # Start with snow on ground
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Run a timestep with warm temperature (melt)
        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=5.0,   # mm
            temperature=15.0,    # deg C (warm, should cause melt)
            et=3.0               # mm
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # SWE should decrease due to melt
        assert outputs['swe_mm'] < 50.0

        # Runoff should be non-negative (melt + rain goes through AWBM)
        assert outputs['runoff_mm'] >= 0.0

    def test_catchment_step_runoff_volume_conversion(self):
        """Test that runoff is correctly converted from mm to m³/day."""
        area_km2 = 100.0
        catchment = Catchment(
            name='test_catchment',
            area=area_km2,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Run a timestep
        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=20.0,
            temperature=20.0,
            et=5.0
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check conversion: runoff_m3d = runoff_mm * area_km2 * 1000
        expected_runoff_m3d = outputs['runoff_mm'] * area_km2 * 1000.0
        assert abs(outputs['runoff'] - expected_runoff_m3d) < 0.01


class TestCatchmentOutputFormat:
    """Test Catchment outputs match expected format."""

    def test_catchment_outputs_have_required_keys(self):
        """Test that Catchment outputs contain all required keys."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=10.0,
            temperature=15.0,
            et=3.0
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check all required output keys are present
        required_keys = ['runoff', 'runoff_mm', 'snow_water_equivalent', 'swe_mm']
        for key in required_keys:
            assert key in outputs, f"Missing required output key: {key}"

    def test_catchment_outputs_are_numeric(self):
        """Test that all Catchment outputs are numeric."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=10.0,
            temperature=15.0,
            et=3.0
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check all outputs are numeric
        for key, value in outputs.items():
            assert isinstance(value, (int, float)), f"Output {key} is not numeric: {type(value)}"

    def test_catchment_swe_aliases(self):
        """Test that swe_mm and snow_water_equivalent are aliases."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow17_params={
                'latitude': 45.0,
                'elevation': 1500.0,
                'ref_elevation': 1000.0
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        date = datetime(2020, 1, 15)
        drivers = MockDriverRegistry(
            precipitation=10.0,
            temperature=-5.0,
            et=1.0
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # Check that both aliases have the same value
        assert outputs['swe_mm'] == outputs['snow_water_equivalent']


class TestCatchmentVariousInputs:
    """Test Catchment with various input combinations."""

    def test_catchment_with_zero_precipitation(self):
        """Test Catchment with zero precipitation."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=0.0,
            temperature=20.0,
            et=5.0
        )

        catchment.step(date, drivers)
        outputs = catchment.outputs

        # With no precipitation, runoff should be minimal or zero
        assert outputs['runoff_mm'] >= 0.0

    def test_catchment_with_high_precipitation(self):
        """Test Catchment with high precipitation eventually produces runoff."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow_params=None,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Run multiple timesteps with high precipitation to fill stores
        date = datetime(2020, 6, 15)
        drivers = MockDriverRegistry(
            precipitation=100.0,  # High precipitation
            temperature=20.0,
            et=5.0
        )

        for i in range(5):
            catchment.step(date, drivers)

        outputs = catchment.outputs

        # After multiple high precipitation events, runoff should be significant
        assert outputs['runoff_mm'] > 0.0

    def test_catchment_multiple_timesteps(self):
        """Test Catchment over multiple timesteps maintains state."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            snow17_params={
                'latitude': 45.0,
                'elevation': 1500.0,
                'ref_elevation': 1000.0
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95
            }
        )

        # Timestep 1: Cold, snow accumulation
        date1 = datetime(2020, 1, 15)
        drivers1 = MockDriverRegistry(
            precipitation=10.0,
            temperature=-5.0,
            et=1.0
        )
        catchment.step(date1, drivers1)
        swe1 = catchment.outputs['swe_mm']

        # Timestep 2: More cold, more snow
        date2 = datetime(2020, 1, 16)
        drivers2 = MockDriverRegistry(
            precipitation=10.0,
            temperature=-5.0,
            et=1.0
        )
        catchment.step(date2, drivers2)
        swe2 = catchment.outputs['swe_mm']

        # SWE should increase
        assert swe2 > swe1

        # Timestep 3: Warm, melt
        date3 = datetime(2020, 1, 17)
        drivers3 = MockDriverRegistry(
            precipitation=0.0,
            temperature=10.0,
            et=2.0
        )
        catchment.step(date3, drivers3)
        swe3 = catchment.outputs['swe_mm']

        # SWE should decrease due to melt
        assert swe3 < swe2
