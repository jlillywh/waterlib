"""
Unit tests for Snow17 kernel.

Tests the pure Snow17 algorithm implementation including:
- Snow accumulation at cold temperatures
- Melt at warm temperatures
- Rain-on-snow events
- State transitions
"""

import pytest
from waterlib.kernels.hydrology.snow17 import (
    snow17_step,
    Snow17Params,
    Snow17State,
    Snow17Inputs,
    Snow17Outputs
)


class TestSnow17BasicFunctionality:
    """Test basic Snow17 kernel functionality."""

    def test_snow_accumulation_cold_temperature(self):
        """Test that snow accumulates when temperature is below freezing."""
        params = Snow17Params(
            mfmax=1.6,
            mfmin=0.6,
            pxtemp1=0.0,
            pxtemp2=1.0,
            scf=1.0
        )
        state = Snow17State(w_i=0.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=-5.0,
            precip_mm=10.0,
            elevation_m=1500.0,
            ref_elevation_m=1000.0,
            day_of_year=15,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # At -5°C, all precipitation should be snow
        assert outputs.snow_mm > 0.0
        assert outputs.rain_mm == 0.0
        # Snow should accumulate (SWE increases)
        assert new_state.w_i > state.w_i
        assert outputs.swe_mm > 0.0
        # No melt should occur at cold temperature
        assert outputs.runoff_mm == 0.0

    def test_melt_warm_temperature(self):
        """Test that snow melts when temperature is above freezing."""
        params = Snow17Params(
            mfmax=1.6,
            mfmin=0.6,
            mbase=0.0,
            pxtemp1=0.0,
            pxtemp2=1.0
        )
        # Start with existing snowpack
        state = Snow17State(w_i=50.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=5.0,
            precip_mm=0.0,
            elevation_m=1500.0,
            ref_elevation_m=1000.0,
            day_of_year=150,  # Summer
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Snow should melt (ice content decreases)
        assert new_state.w_i < state.w_i
        # Some runoff should be generated
        assert outputs.runoff_mm > 0.0

    def test_rain_on_snow_event(self):
        """Test rain-on-snow event with enhanced melt."""
        params = Snow17Params(
            mfmax=1.6,
            mfmin=0.6,
            mbase=0.0,
            pxtemp1=0.0,
            pxtemp2=1.0,
            uadj=0.05
        )
        # Start with existing snowpack
        state = Snow17State(w_i=100.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=6.0,  # Warm enough to be rain after lapse rate adjustment
            precip_mm=20.0,  # Significant rain
            elevation_m=1500.0,
            ref_elevation_m=1000.0,
            day_of_year=100,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Rain should be generated (temp above pxtemp2 after adjustment)
        # At 1500m elevation with ref 1000m: adjusted temp = 6.0 - 3.0 = 3.0°C
        assert outputs.rain_mm > 0.0
        # Melt should occur
        assert new_state.w_i < state.w_i
        # Runoff should be generated
        assert outputs.runoff_mm > 0.0

    def test_state_transitions_w_i(self):
        """Test ice content (w_i) state transitions."""
        params = Snow17Params()
        state = Snow17State(w_i=30.0, w_q=0.0, ait=-2.0, deficit=5.0)

        # Cold day with snow
        inputs = Snow17Inputs(
            temp_c=-3.0,
            precip_mm=5.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=50,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Ice should increase with new snow
        assert new_state.w_i > state.w_i
        # Deficit should be affected by new cold snow
        assert new_state.deficit >= 0.0

    def test_state_transitions_w_q(self):
        """Test liquid water (w_q) state transitions."""
        params = Snow17Params(plwhc=0.04)
        # Ripe snowpack (no deficit)
        state = Snow17State(w_i=50.0, w_q=0.0, ait=0.0, deficit=0.0)

        # Warm day causing melt
        inputs = Snow17Inputs(
            temp_c=2.0,
            precip_mm=0.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=120,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Liquid water should be held up to capacity
        max_liquid_capacity = params.plwhc * new_state.w_i
        assert new_state.w_q <= max_liquid_capacity

    def test_state_transitions_ait(self):
        """Test Antecedent Temperature Index (ait) state transitions."""
        params = Snow17Params(tipm=0.15)
        state = Snow17State(w_i=40.0, w_q=0.0, ait=-5.0, deficit=10.0)

        # Warming trend
        inputs = Snow17Inputs(
            temp_c=-1.0,
            precip_mm=0.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=80,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # ATI should warm toward air temperature
        assert new_state.ait > state.ait
        # ATI should not exceed 0
        assert new_state.ait <= 0.0

    def test_state_transitions_deficit(self):
        """Test heat deficit state transitions."""
        params = Snow17Params()
        state = Snow17State(w_i=60.0, w_q=0.0, ait=-3.0, deficit=15.0)

        # Cold day
        inputs = Snow17Inputs(
            temp_c=-8.0,
            precip_mm=3.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=30,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Deficit should be non-negative
        assert new_state.deficit >= 0.0
        # Deficit should be bounded by ice content
        assert new_state.deficit <= 0.33 * new_state.w_i


class TestSnow17EdgeCases:
    """Test edge cases and boundary conditions."""

    def test_no_snowpack_all_rain(self):
        """Test behavior with no snowpack and rain."""
        params = Snow17Params()
        state = Snow17State(w_i=0.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=10.0,
            precip_mm=15.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=180,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # All precipitation should be rain
        assert outputs.rain_mm > 0.0
        assert outputs.snow_mm == 0.0
        # All rain should become runoff (no snowpack to hold it)
        assert outputs.runoff_mm > 0.0
        # No snowpack should remain
        assert new_state.w_i == 0.0
        assert new_state.w_q == 0.0

    def test_complete_snowpack_melt(self):
        """Test complete melting of snowpack."""
        params = Snow17Params(mfmax=3.0)  # High melt factor
        state = Snow17State(w_i=10.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=15.0,  # Very warm
            precip_mm=0.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=150,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Snowpack should be completely or mostly melted
        assert new_state.w_i < state.w_i
        # Runoff should be generated
        assert outputs.runoff_mm > 0.0

    def test_mixed_precipitation(self):
        """Test precipitation in transition temperature range."""
        params = Snow17Params(pxtemp1=0.0, pxtemp2=1.0)
        state = Snow17State(w_i=20.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=0.5,  # Between pxtemp1 and pxtemp2
            precip_mm=10.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=90,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # Should have both rain and snow
        assert outputs.rain_mm > 0.0
        assert outputs.snow_mm > 0.0
        # Total should equal input precipitation (accounting for SCF)
        total_precip = outputs.rain_mm + outputs.snow_mm
        assert abs(total_precip - inputs.precip_mm) < 0.1


class TestSnow17KnownInputOutput:
    """Test with known input/output pairs for validation."""

    def test_known_case_cold_accumulation(self):
        """Test known case: cold day with snow accumulation."""
        params = Snow17Params(
            mfmax=1.6,
            mfmin=0.6,
            scf=1.0,
            pxtemp1=0.0,
            pxtemp2=1.0
        )
        state = Snow17State(w_i=0.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=-10.0,
            precip_mm=20.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=1,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # All precipitation should become snow (SCF=1.0)
        assert abs(outputs.snow_mm - 20.0) < 0.01
        assert outputs.rain_mm == 0.0
        # SWE should equal snow input
        assert abs(outputs.swe_mm - 20.0) < 0.01
        # No runoff at cold temperature
        assert outputs.runoff_mm == 0.0
        # Ice content should equal snow input
        assert abs(new_state.w_i - 20.0) < 0.01

    def test_known_case_warm_rain(self):
        """Test known case: warm day with rain only."""
        params = Snow17Params(pxtemp1=0.0, pxtemp2=1.0)
        state = Snow17State(w_i=0.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=10.0,
            precip_mm=25.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=180,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        new_state, outputs = snow17_step(inputs, params, state)

        # All precipitation should be rain
        assert abs(outputs.rain_mm - 25.0) < 0.01
        assert outputs.snow_mm == 0.0
        # All rain should become runoff (no snowpack)
        assert abs(outputs.runoff_mm - 25.0) < 0.01
        # No snowpack should exist
        assert new_state.w_i == 0.0
        assert outputs.swe_mm == 0.0


class TestSnow17ParameterValidation:
    """Test parameter effects on model behavior."""

    def test_scf_effect(self):
        """Test snow correction factor (SCF) effect."""
        params_scf1 = Snow17Params(scf=1.0, pxtemp1=0.0, pxtemp2=1.0)
        params_scf15 = Snow17Params(scf=1.5, pxtemp1=0.0, pxtemp2=1.0)

        state = Snow17State(w_i=0.0, w_q=0.0, ait=0.0, deficit=0.0)
        inputs = Snow17Inputs(
            temp_c=-5.0,
            precip_mm=10.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=50,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        _, outputs1 = snow17_step(inputs, params_scf1, state)
        _, outputs15 = snow17_step(inputs, params_scf15, state)

        # Higher SCF should result in more snow
        assert outputs15.snow_mm > outputs1.snow_mm
        assert abs(outputs15.snow_mm - 1.5 * outputs1.snow_mm) < 0.01

    def test_lapse_rate_effect(self):
        """Test temperature lapse rate effect."""
        params = Snow17Params(lapse_rate=0.006)
        state = Snow17State(w_i=50.0, w_q=0.0, ait=0.0, deficit=0.0)

        # Same temperature at different elevations
        inputs_low = Snow17Inputs(
            temp_c=2.0,
            precip_mm=0.0,
            elevation_m=1000.0,
            ref_elevation_m=1000.0,
            day_of_year=100,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        inputs_high = Snow17Inputs(
            temp_c=2.0,
            precip_mm=0.0,
            elevation_m=2000.0,  # 1000m higher
            ref_elevation_m=1000.0,
            day_of_year=100,
            days_in_year=365,
            dt_hours=24.0,
            latitude=45.0
        )

        _, outputs_low = snow17_step(inputs_low, params, state)
        _, outputs_high = snow17_step(inputs_high, params, state)

        # Higher elevation should be colder, resulting in less melt
        # (or potentially more snow if precipitation was present)
        # At minimum, runoff should be different
        assert outputs_low.runoff_mm != outputs_high.runoff_mm
