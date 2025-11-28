"""
Unit tests for Weir kernel.

Tests the pure weir discharge calculation including:
- Discharge with various head values
- Zero discharge when head <= 0
- Discharge increases with head^1.5
- Different weir coefficients and widths
"""

import pytest
from waterlib.kernels.hydraulics.weir import (
    weir_discharge,
    spillway_discharge,
    WeirParams,
    WeirInputs,
    WeirOutputs
)


class TestWeirBasicFunctionality:
    """Test basic weir kernel functionality."""

    def test_weir_discharge_positive_head(self):
        """Test weir discharge with positive head."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.0)

        outputs = weir_discharge(inputs, params)

        # Head should be 1.0 m
        assert outputs.head_m == 1.0
        # Discharge should be positive
        assert outputs.discharge_m3s > 0.0
        assert outputs.discharge_m3d > 0.0
        # m³/d should be m³/s × 86400
        assert abs(outputs.discharge_m3d - outputs.discharge_m3s * 86400.0) < 0.01

    def test_weir_discharge_zero_head(self):
        """Test zero discharge when head = 0."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=100.0)

        outputs = weir_discharge(inputs, params)

        # Head should be 0
        assert outputs.head_m == 0.0
        # Discharge should be zero
        assert outputs.discharge_m3s == 0.0
        assert outputs.discharge_m3d == 0.0

    def test_weir_discharge_negative_head(self):
        """Test zero discharge when water elevation below crest."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=95.0)

        outputs = weir_discharge(inputs, params)

        # Head should be 0 (not negative)
        assert outputs.head_m == 0.0
        # Discharge should be zero
        assert outputs.discharge_m3s == 0.0
        assert outputs.discharge_m3d == 0.0

    def test_discharge_increases_with_head(self):
        """Test that discharge increases with head^1.5."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )

        # Test with increasing head values
        inputs_1m = WeirInputs(water_elevation_m=101.0)
        inputs_2m = WeirInputs(water_elevation_m=102.0)
        inputs_3m = WeirInputs(water_elevation_m=103.0)

        outputs_1m = weir_discharge(inputs_1m, params)
        outputs_2m = weir_discharge(inputs_2m, params)
        outputs_3m = weir_discharge(inputs_3m, params)

        # Discharge should increase
        assert outputs_2m.discharge_m3s > outputs_1m.discharge_m3s
        assert outputs_3m.discharge_m3s > outputs_2m.discharge_m3s

        # Check that relationship follows H^1.5
        # Q2/Q1 should equal (H2/H1)^1.5
        ratio_discharge = outputs_2m.discharge_m3s / outputs_1m.discharge_m3s
        ratio_head = (outputs_2m.head_m / outputs_1m.head_m) ** 1.5
        assert abs(ratio_discharge - ratio_head) < 0.01

    def test_different_coefficients(self):
        """Test discharge with different weir coefficients."""
        params_low = WeirParams(
            coefficient=1.5,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        params_high = WeirParams(
            coefficient=2.0,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.5)

        outputs_low = weir_discharge(inputs, params_low)
        outputs_high = weir_discharge(inputs, params_high)

        # Higher coefficient should give higher discharge
        assert outputs_high.discharge_m3s > outputs_low.discharge_m3s
        # Ratio should match coefficient ratio
        ratio = outputs_high.discharge_m3s / outputs_low.discharge_m3s
        expected_ratio = params_high.coefficient / params_low.coefficient
        assert abs(ratio - expected_ratio) < 0.01

    def test_different_widths(self):
        """Test discharge with different weir widths."""
        params_narrow = WeirParams(
            coefficient=1.8,
            width_m=5.0,
            crest_elevation_m=100.0
        )
        params_wide = WeirParams(
            coefficient=1.8,
            width_m=20.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.0)

        outputs_narrow = weir_discharge(inputs, params_narrow)
        outputs_wide = weir_discharge(inputs, params_wide)

        # Wider weir should give higher discharge
        assert outputs_wide.discharge_m3s > outputs_narrow.discharge_m3s
        # Ratio should match width ratio
        ratio = outputs_wide.discharge_m3s / outputs_narrow.discharge_m3s
        expected_ratio = params_wide.width_m / params_narrow.width_m
        assert abs(ratio - expected_ratio) < 0.01


class TestWeirKnownValues:
    """Test with known input/output pairs for validation."""

    def test_known_case_1(self):
        """Test known case: C=1.8, L=10m, H=1m."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.0)

        outputs = weir_discharge(inputs, params)

        # Q = C × L × H^1.5 = 1.8 × 10 × 1^1.5 = 18 m³/s
        expected_discharge_m3s = 1.8 * 10.0 * (1.0 ** 1.5)
        assert abs(outputs.discharge_m3s - expected_discharge_m3s) < 0.01
        assert abs(outputs.discharge_m3s - 18.0) < 0.01

    def test_known_case_2(self):
        """Test known case: C=2.0, L=15m, H=0.5m."""
        params = WeirParams(
            coefficient=2.0,
            width_m=15.0,
            crest_elevation_m=200.0
        )
        inputs = WeirInputs(water_elevation_m=200.5)

        outputs = weir_discharge(inputs, params)

        # Q = C × L × H^1.5 = 2.0 × 15 × 0.5^1.5
        expected_discharge_m3s = 2.0 * 15.0 * (0.5 ** 1.5)
        assert abs(outputs.discharge_m3s - expected_discharge_m3s) < 0.01
        # 0.5^1.5 ≈ 0.3536
        assert abs(outputs.discharge_m3s - 10.607) < 0.01

    def test_known_case_3(self):
        """Test known case: C=1.7, L=20m, H=2m."""
        params = WeirParams(
            coefficient=1.7,
            width_m=20.0,
            crest_elevation_m=150.0
        )
        inputs = WeirInputs(water_elevation_m=152.0)

        outputs = weir_discharge(inputs, params)

        # Q = C × L × H^1.5 = 1.7 × 20 × 2^1.5
        expected_discharge_m3s = 1.7 * 20.0 * (2.0 ** 1.5)
        assert abs(outputs.discharge_m3s - expected_discharge_m3s) < 0.01
        # 2^1.5 ≈ 2.828
        assert abs(outputs.discharge_m3s - 96.15) < 0.1


class TestWeirEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_head(self):
        """Test with very small head value."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=100.001)

        outputs = weir_discharge(inputs, params)

        # Should have very small positive discharge
        assert outputs.head_m > 0.0
        assert outputs.discharge_m3s > 0.0
        assert outputs.discharge_m3s < 0.1  # Very small

    def test_very_large_head(self):
        """Test with very large head value."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=110.0)

        outputs = weir_discharge(inputs, params)

        # Should have large discharge
        assert outputs.head_m == 10.0
        assert outputs.discharge_m3s > 100.0
        # Q = 1.8 × 10 × 10^1.5 ≈ 569.2 m³/s
        expected = 1.8 * 10.0 * (10.0 ** 1.5)
        assert abs(outputs.discharge_m3s - expected) < 1.0

    def test_zero_width(self):
        """Test with zero width (edge case)."""
        params = WeirParams(
            coefficient=1.8,
            width_m=0.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.0)

        outputs = weir_discharge(inputs, params)

        # Zero width should give zero discharge
        assert outputs.discharge_m3s == 0.0

    def test_zero_coefficient(self):
        """Test with zero coefficient (edge case)."""
        params = WeirParams(
            coefficient=0.0,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.0)

        outputs = weir_discharge(inputs, params)

        # Zero coefficient should give zero discharge
        assert outputs.discharge_m3s == 0.0


class TestSpillwayFunction:
    """Test spillway_discharge function (alias for weir_discharge)."""

    def test_spillway_discharge_same_as_weir(self):
        """Test that spillway_discharge gives same results as weir_discharge."""
        params = WeirParams(
            coefficient=1.7,
            width_m=20.0,
            crest_elevation_m=245.0
        )
        inputs = WeirInputs(water_elevation_m=246.5)

        weir_outputs = weir_discharge(inputs, params)
        spillway_outputs = spillway_discharge(inputs, params)

        # Should be identical
        assert spillway_outputs.discharge_m3s == weir_outputs.discharge_m3s
        assert spillway_outputs.discharge_m3d == weir_outputs.discharge_m3d
        assert spillway_outputs.head_m == weir_outputs.head_m

    def test_spillway_discharge_positive_head(self):
        """Test spillway discharge with positive head."""
        params = WeirParams(
            coefficient=1.7,
            width_m=20.0,
            crest_elevation_m=245.0
        )
        inputs = WeirInputs(water_elevation_m=246.0)

        outputs = spillway_discharge(inputs, params)

        # Should have positive discharge
        assert outputs.head_m == 1.0
        assert outputs.discharge_m3s > 0.0

    def test_spillway_discharge_zero_head(self):
        """Test spillway discharge with zero head."""
        params = WeirParams(
            coefficient=1.7,
            width_m=20.0,
            crest_elevation_m=245.0
        )
        inputs = WeirInputs(water_elevation_m=245.0)

        outputs = spillway_discharge(inputs, params)

        # Should have zero discharge
        assert outputs.head_m == 0.0
        assert outputs.discharge_m3s == 0.0


class TestWeirUnitConversion:
    """Test unit conversion between m³/s and m³/d."""

    def test_m3s_to_m3d_conversion(self):
        """Test conversion from m³/s to m³/d."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )
        inputs = WeirInputs(water_elevation_m=101.5)

        outputs = weir_discharge(inputs, params)

        # m³/d should be m³/s × 86400
        expected_m3d = outputs.discharge_m3s * 86400.0
        assert abs(outputs.discharge_m3d - expected_m3d) < 0.01

    def test_conversion_consistency(self):
        """Test that conversion is consistent across different values."""
        params = WeirParams(
            coefficient=1.8,
            width_m=10.0,
            crest_elevation_m=100.0
        )

        test_elevations = [100.5, 101.0, 102.0, 103.5]

        for elevation in test_elevations:
            inputs = WeirInputs(water_elevation_m=elevation)
            outputs = weir_discharge(inputs, params)

            # Check conversion
            expected_m3d = outputs.discharge_m3s * 86400.0
            assert abs(outputs.discharge_m3d - expected_m3d) < 0.01
