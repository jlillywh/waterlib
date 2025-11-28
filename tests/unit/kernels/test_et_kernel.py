"""
Unit tests for Evapotranspiration (ET) kernels.

Tests the pure ET calculation implementations including:
- Hargreaves-Samani method with known input/output pairs
- ET calculation across different latitudes
- ET calculation across different seasons (day of year)
- Various temperature ranges
- Extraterrestrial radiation calculation
"""

import pytest
import math
from waterlib.kernels.climate.et import (
    hargreaves_et,
    HargreavesETParams,
    HargreavesETInputs,
    ETOutputs,
    _calculate_ra
)


class TestHargreavesETBasicFunctionality:
    """Test basic Hargreaves-Samani ET functionality."""

    def test_hargreaves_et_known_input_output(self):
        """Test Hargreaves ET with known input/output pair."""
        params = HargreavesETParams(
            latitude_deg=45.0,
            coefficient=0.0023
        )
        inputs = HargreavesETInputs(
            tmin_c=10.0,
            tmax_c=25.0,
            day_of_year=180  # Summer solstice area
        )

        outputs = hargreaves_et(inputs, params)

        # ET should be positive
        assert outputs.et0_mm > 0.0
        # For summer at mid-latitude with good temperature range, ET should be reasonable
        # Typical range is 3-15 mm/day for these conditions
        assert 3.0 < outputs.et0_mm < 15.0

    def test_hargreaves_et_zero_temperature_range(self):
        """Test ET calculation when tmin equals tmax."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=20.0,
            tmax_c=20.0,  # Same as tmin
            day_of_year=150
        )

        outputs = hargreaves_et(inputs, params)

        # With zero temperature range, ET should be zero
        assert outputs.et0_mm == 0.0

    def test_hargreaves_et_inverted_temperatures(self):
        """Test ET calculation when tmin > tmax (data error case)."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=25.0,
            tmax_c=20.0,  # Less than tmin
            day_of_year=150
        )

        outputs = hargreaves_et(inputs, params)

        # Should handle gracefully by clamping temperature range to zero
        assert outputs.et0_mm == 0.0

    def test_hargreaves_et_cold_temperatures(self):
        """Test ET calculation with cold temperatures."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=-10.0,
            tmax_c=5.0,
            day_of_year=15  # Winter
        )

        outputs = hargreaves_et(inputs, params)

        # ET should be low in winter with cold temperatures
        # But still positive due to solar radiation
        assert outputs.et0_mm >= 0.0
        assert outputs.et0_mm < 3.0  # Should be relatively low

    def test_hargreaves_et_hot_temperatures(self):
        """Test ET calculation with hot temperatures."""
        params = HargreavesETParams(latitude_deg=35.0)
        inputs = HargreavesETInputs(
            tmin_c=25.0,
            tmax_c=40.0,
            day_of_year=180  # Summer
        )

        outputs = hargreaves_et(inputs, params)

        # ET should be high in summer with hot temperatures
        assert outputs.et0_mm > 5.0
        # But should be reasonable (not infinite)
        assert outputs.et0_mm < 25.0


class TestHargreavesETLatitudeEffects:
    """Test ET calculation across different latitudes."""

    def test_et_equator_vs_midlatitude_summer(self):
        """Test ET at equator vs mid-latitude during summer."""
        inputs = HargreavesETInputs(
            tmin_c=20.0,
            tmax_c=30.0,
            day_of_year=180  # Summer in northern hemisphere
        )

        params_equator = HargreavesETParams(latitude_deg=0.0)
        params_midlat = HargreavesETParams(latitude_deg=45.0)

        outputs_equator = hargreaves_et(inputs, params_equator)
        outputs_midlat = hargreaves_et(inputs, params_midlat)

        # Both should produce positive ET
        assert outputs_equator.et0_mm > 0.0
        assert outputs_midlat.et0_mm > 0.0
        # Mid-latitude should have higher ET in summer due to longer days
        assert outputs_midlat.et0_mm > outputs_equator.et0_mm

    def test_et_equator_vs_midlatitude_winter(self):
        """Test ET at equator vs mid-latitude during winter."""
        inputs = HargreavesETInputs(
            tmin_c=15.0,
            tmax_c=25.0,
            day_of_year=1  # Winter in northern hemisphere
        )

        params_equator = HargreavesETParams(latitude_deg=0.0)
        params_midlat = HargreavesETParams(latitude_deg=45.0)

        outputs_equator = hargreaves_et(inputs, params_equator)
        outputs_midlat = hargreaves_et(inputs, params_midlat)

        # Both should produce positive ET
        assert outputs_equator.et0_mm > 0.0
        assert outputs_midlat.et0_mm > 0.0
        # Equator should have higher ET in winter (shorter days at mid-latitude)
        assert outputs_equator.et0_mm > outputs_midlat.et0_mm

    def test_et_northern_vs_southern_hemisphere(self):
        """Test ET in northern vs southern hemisphere."""
        # Summer in northern hemisphere (day 180)
        inputs_summer = HargreavesETInputs(
            tmin_c=18.0,
            tmax_c=28.0,
            day_of_year=180
        )

        params_north = HargreavesETParams(latitude_deg=40.0)
        params_south = HargreavesETParams(latitude_deg=-40.0)

        outputs_north = hargreaves_et(inputs_summer, params_north)
        outputs_south = hargreaves_et(inputs_summer, params_south)

        # Northern hemisphere should have higher ET during its summer
        assert outputs_north.et0_mm > outputs_south.et0_mm

    def test_et_high_latitude(self):
        """Test ET at high latitude."""
        params = HargreavesETParams(latitude_deg=65.0)

        # Summer at high latitude
        inputs_summer = HargreavesETInputs(
            tmin_c=10.0,
            tmax_c=20.0,
            day_of_year=180
        )

        # Winter at high latitude
        inputs_winter = HargreavesETInputs(
            tmin_c=-15.0,
            tmax_c=-5.0,
            day_of_year=1
        )

        outputs_summer = hargreaves_et(inputs_summer, params)
        outputs_winter = hargreaves_et(inputs_winter, params)

        # Summer should have much higher ET due to very long days
        assert outputs_summer.et0_mm > outputs_winter.et0_mm
        # Winter ET should be very low (short days, cold)
        assert outputs_winter.et0_mm < 1.0


class TestHargreavesETSeasonalEffects:
    """Test ET calculation across different seasons (day of year)."""

    def test_et_seasonal_variation_midlatitude(self):
        """Test seasonal variation in ET at mid-latitude."""
        params = HargreavesETParams(latitude_deg=40.0)

        # Keep temperature constant to isolate seasonal effect
        base_inputs = {
            'tmin_c': 15.0,
            'tmax_c': 25.0
        }

        # Winter solstice (day ~355)
        outputs_winter = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=355),
            params
        )

        # Spring equinox (day ~80)
        outputs_spring = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=80),
            params
        )

        # Summer solstice (day ~172)
        outputs_summer = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=172),
            params
        )

        # Fall equinox (day ~266)
        outputs_fall = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=266),
            params
        )

        # Summer should have highest ET
        assert outputs_summer.et0_mm > outputs_spring.et0_mm
        assert outputs_summer.et0_mm > outputs_fall.et0_mm
        assert outputs_summer.et0_mm > outputs_winter.et0_mm

        # Winter should have lowest ET
        assert outputs_winter.et0_mm < outputs_spring.et0_mm
        assert outputs_winter.et0_mm < outputs_fall.et0_mm

        # Equinoxes should be similar
        assert abs(outputs_spring.et0_mm - outputs_fall.et0_mm) < 0.5

    def test_et_seasonal_variation_equator(self):
        """Test seasonal variation in ET at equator (should be minimal)."""
        params = HargreavesETParams(latitude_deg=0.0)

        base_inputs = {
            'tmin_c': 22.0,
            'tmax_c': 32.0
        }

        outputs_jan = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=15),
            params
        )

        outputs_jul = hargreaves_et(
            HargreavesETInputs(**base_inputs, day_of_year=195),
            params
        )

        # At equator, seasonal variation should be minimal
        # (day length doesn't vary much)
        assert abs(outputs_jan.et0_mm - outputs_jul.et0_mm) < 1.0

    def test_et_all_days_of_year(self):
        """Test that ET can be calculated for all days of year."""
        params = HargreavesETParams(latitude_deg=45.0)

        for day in [1, 50, 100, 150, 200, 250, 300, 350, 365]:
            inputs = HargreavesETInputs(
                tmin_c=10.0,
                tmax_c=20.0,
                day_of_year=day
            )

            outputs = hargreaves_et(inputs, params)

            # Should produce valid ET for all days
            assert outputs.et0_mm >= 0.0
            assert not math.isnan(outputs.et0_mm)
            assert not math.isinf(outputs.et0_mm)


class TestHargreavesETTemperatureRanges:
    """Test ET with various temperature ranges."""

    def test_et_small_temperature_range(self):
        """Test ET with small diurnal temperature range."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=18.0,
            tmax_c=20.0,  # Only 2°C range
            day_of_year=180
        )

        outputs = hargreaves_et(inputs, params)

        # Small temperature range should result in lower ET
        assert outputs.et0_mm > 0.0
        assert outputs.et0_mm < 5.0

    def test_et_large_temperature_range(self):
        """Test ET with large diurnal temperature range."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=10.0,
            tmax_c=35.0,  # 25°C range
            day_of_year=180
        )

        outputs = hargreaves_et(inputs, params)

        # Large temperature range should result in higher ET
        assert outputs.et0_mm > 5.0

    def test_et_temperature_range_effect(self):
        """Test that ET increases with temperature range."""
        params = HargreavesETParams(latitude_deg=40.0)

        # Same mean temperature, different ranges
        inputs_small = HargreavesETInputs(
            tmin_c=18.0,
            tmax_c=22.0,  # 4°C range, mean 20°C
            day_of_year=150
        )

        inputs_large = HargreavesETInputs(
            tmin_c=10.0,
            tmax_c=30.0,  # 20°C range, mean 20°C
            day_of_year=150
        )

        outputs_small = hargreaves_et(inputs_small, params)
        outputs_large = hargreaves_et(inputs_large, params)

        # Larger temperature range should produce higher ET
        assert outputs_large.et0_mm > outputs_small.et0_mm


class TestExtraterrestrialRadiation:
    """Test extraterrestrial radiation calculation."""

    def test_ra_positive_all_latitudes(self):
        """Test that Ra is positive for all reasonable latitudes."""
        for lat in [-60, -30, 0, 30, 60]:
            for doy in [1, 90, 180, 270, 365]:
                ra = _calculate_ra(doy, lat)
                assert ra >= 0.0, f"Ra should be non-negative for lat={lat}, doy={doy}"

    def test_ra_summer_vs_winter_midlatitude(self):
        """Test Ra is higher in summer than winter at mid-latitude."""
        lat = 45.0

        ra_summer = _calculate_ra(180, lat)  # Summer solstice
        ra_winter = _calculate_ra(1, lat)    # Winter solstice

        # Summer should have higher extraterrestrial radiation
        assert ra_summer > ra_winter

    def test_ra_equator_minimal_variation(self):
        """Test Ra has minimal seasonal variation at equator."""
        lat = 0.0

        ra_jan = _calculate_ra(15, lat)
        ra_jul = _calculate_ra(195, lat)

        # At equator, Ra should be similar year-round
        # Allow for some variation due to Earth-Sun distance
        assert abs(ra_jan - ra_jul) < 5.0  # MJ/m²/day

    def test_ra_northern_vs_southern_hemisphere(self):
        """Test Ra is opposite in northern vs southern hemisphere."""
        doy_summer_north = 180  # June 21

        ra_north = _calculate_ra(doy_summer_north, 40.0)
        ra_south = _calculate_ra(doy_summer_north, -40.0)

        # During northern summer, northern hemisphere should have higher Ra
        assert ra_north > ra_south

    def test_ra_reasonable_magnitude(self):
        """Test Ra has reasonable magnitude."""
        # Typical Ra values range from ~2-45 MJ/m²/day
        # (can be very low at high latitudes in winter)
        for lat in [0, 30, 45, 60]:
            for doy in [1, 90, 180, 270]:
                ra = _calculate_ra(doy, lat)
                assert 0.0 <= ra < 50.0, f"Ra out of reasonable range for lat={lat}, doy={doy}"


class TestHargreavesETCoefficientEffect:
    """Test effect of Hargreaves coefficient on ET."""

    def test_coefficient_effect(self):
        """Test that coefficient scales ET linearly."""
        inputs = HargreavesETInputs(
            tmin_c=15.0,
            tmax_c=25.0,
            day_of_year=150
        )

        params_standard = HargreavesETParams(
            latitude_deg=40.0,
            coefficient=0.0023
        )

        params_double = HargreavesETParams(
            latitude_deg=40.0,
            coefficient=0.0046  # Double the standard
        )

        outputs_standard = hargreaves_et(inputs, params_standard)
        outputs_double = hargreaves_et(inputs, params_double)

        # Doubling coefficient should double ET
        assert abs(outputs_double.et0_mm - 2.0 * outputs_standard.et0_mm) < 0.01

    def test_zero_coefficient(self):
        """Test ET with zero coefficient."""
        params = HargreavesETParams(
            latitude_deg=40.0,
            coefficient=0.0
        )
        inputs = HargreavesETInputs(
            tmin_c=15.0,
            tmax_c=25.0,
            day_of_year=150
        )

        outputs = hargreaves_et(inputs, params)

        # Zero coefficient should result in zero ET
        assert outputs.et0_mm == 0.0


class TestHargreavesETEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_et_leap_year_day_366(self):
        """Test ET calculation for day 366 (leap year)."""
        params = HargreavesETParams(latitude_deg=45.0)
        inputs = HargreavesETInputs(
            tmin_c=10.0,
            tmax_c=20.0,
            day_of_year=366
        )

        outputs = hargreaves_et(inputs, params)

        # Should handle day 366 without error
        assert outputs.et0_mm > 0.0
        assert not math.isnan(outputs.et0_mm)

    def test_et_extreme_cold(self):
        """Test ET with extreme cold temperatures."""
        params = HargreavesETParams(latitude_deg=60.0)
        inputs = HargreavesETInputs(
            tmin_c=-40.0,
            tmax_c=-20.0,
            day_of_year=1
        )

        outputs = hargreaves_et(inputs, params)

        # Should handle extreme cold without error
        assert outputs.et0_mm >= 0.0
        assert not math.isnan(outputs.et0_mm)

    def test_et_extreme_heat(self):
        """Test ET with extreme heat."""
        params = HargreavesETParams(latitude_deg=30.0)
        inputs = HargreavesETInputs(
            tmin_c=35.0,
            tmax_c=50.0,
            day_of_year=180
        )

        outputs = hargreaves_et(inputs, params)

        # Should handle extreme heat without error
        assert outputs.et0_mm > 0.0
        assert not math.isnan(outputs.et0_mm)
        # Should be high but not unreasonable
        assert outputs.et0_mm < 30.0

    def test_et_negative_latitude(self):
        """Test ET with negative latitude (southern hemisphere)."""
        params = HargreavesETParams(latitude_deg=-35.0)
        inputs = HargreavesETInputs(
            tmin_c=15.0,
            tmax_c=28.0,
            day_of_year=180
        )

        outputs = hargreaves_et(inputs, params)

        # Should work fine with negative latitude
        assert outputs.et0_mm > 0.0
        assert not math.isnan(outputs.et0_mm)
