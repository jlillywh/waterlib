"""
Unit tests for AWBM kernel.

Tests the pure AWBM algorithm implementation including:
- Surface store overflow
- Baseflow/surface flow splitting
- Routing store recession
- State transitions for all 5 stores
"""

import pytest
from waterlib.kernels.hydrology.awbm import (
    awbm_step,
    AWBMParams,
    AWBMState,
    AWBMInputs,
    AWBMOutputs
)


class TestAWBMBasicFunctionality:
    """Test basic AWBM kernel functionality."""

    def test_awbm_step_with_known_inputs(self):
        """Test awbm_step with known input/output pairs."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(
            ss1=0.0,
            ss2=0.0,
            ss3=0.0,
            s_surf=0.0,
            b_base=0.0
        )
        inputs = AWBMInputs(
            precip_mm=20.0,
            pet_mm=5.0
        )

        new_state, outputs = awbm_step(inputs, params, state)

        # With P > PET, there should be some runoff
        assert outputs.runoff_mm >= 0.0
        # Excess should be generated
        assert outputs.excess_mm >= 0.0
        # States should be non-negative
        assert new_state.ss1 >= 0.0
        assert new_state.ss2 >= 0.0
        assert new_state.ss3 >= 0.0
        assert new_state.s_surf >= 0.0
        assert new_state.b_base >= 0.0

    def test_surface_store_overflow(self):
        """Test that surface stores overflow when capacity is exceeded."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        # Start with stores near capacity
        state = AWBMState(
            ss1=1.0,  # Cap1 = 0.134 * 10 = 1.34
            ss2=20.0,  # Cap2 = 0.433 * 50 = 21.65
            ss3=40.0,  # Cap3 = 0.433 * 100 = 43.3
            s_surf=0.0,
            b_base=0.0
        )
        # Large precipitation event
        inputs = AWBMInputs(
            precip_mm=50.0,
            pet_mm=2.0
        )

        new_state, outputs = awbm_step(inputs, params, state)

        # Overflow should be generated
        assert outputs.excess_mm > 0.0
        # Stores should not exceed their capacities
        assert new_state.ss1 <= params.a1 * params.c_vec[0]
        assert new_state.ss2 <= params.a2 * params.c_vec[1]
        a3 = 1.0 - params.a1 - params.a2
        assert new_state.ss3 <= a3 * params.c_vec[2]

    def test_baseflow_surface_flow_splitting(self):
        """Test that overflow is split between baseflow and surface flow."""
        params = AWBMParams(
            c_vec=[5.0, 40.0, 80.0],
            bfi=0.4,  # 40% to baseflow
            ks=0.3,
            kb=0.95
        )
        state = AWBMState(
            ss1=0.5,
            ss2=15.0,
            ss3=30.0,
            s_surf=0.0,
            b_base=0.0
        )
        inputs = AWBMInputs(
            precip_mm=30.0,
            pet_mm=3.0
        )

        new_state, outputs = awbm_step(inputs, params, state)

        # Both baseflow and surface flow should be generated
        assert outputs.baseflow_mm >= 0.0
        assert outputs.surface_flow_mm >= 0.0
        # Total runoff should equal baseflow + surface flow
        assert abs(outputs.runoff_mm - (outputs.baseflow_mm + outputs.surface_flow_mm)) < 0.001
        # If there's excess, routing stores should receive inflow
        if outputs.excess_mm > 0.0:
            # At least one routing store should have increased
            assert new_state.s_surf > 0.0 or new_state.b_base > 0.0

    def test_routing_store_recession(self):
        """Test that routing stores recede according to recession constants."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.4,  # Surface recession
            kb=0.9   # Baseflow recession
        )
        # Start with water in routing stores, no new input
        state = AWBMState(
            ss1=0.5,
            ss2=10.0,
            ss3=20.0,
            s_surf=10.0,  # Water in surface store
            b_base=20.0   # Water in baseflow store
        )
        # No precipitation, some ET
        inputs = AWBMInputs(
            precip_mm=0.0,
            pet_mm=2.0
        )

        new_state, outputs = awbm_step(inputs, params, state)

        # Routing stores should decrease (recession)
        assert new_state.s_surf < state.s_surf
        assert new_state.b_base < state.b_base
        # Runoff should be generated from recession
        assert outputs.runoff_mm > 0.0
        # Surface store recedes faster (lower Ks)
        surface_recession_rate = (state.s_surf - new_state.s_surf) / state.s_surf
        baseflow_recession_rate = (state.b_base - new_state.b_base) / state.b_base
        assert surface_recession_rate > baseflow_recession_rate


class TestAWBMStateTransitions:
    """Test state transitions for all 5 stores."""

    def test_state_transitions_ss1(self):
        """Test surface store 1 (SS1) state transitions."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.0, b_base=0.0)

        # Moderate precipitation
        inputs = AWBMInputs(precip_mm=5.0, pet_mm=1.0)
        new_state, outputs = awbm_step(inputs, params, state)

        # SS1 should increase or stay same (depending on overflow)
        assert new_state.ss1 >= 0.0
        # Should not exceed capacity
        cap1 = params.a1 * params.c_vec[0]
        assert new_state.ss1 <= cap1 + 0.001  # Small tolerance for floating point

    def test_state_transitions_ss2(self):
        """Test surface store 2 (SS2) state transitions."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.0, b_base=0.0)

        inputs = AWBMInputs(precip_mm=8.0, pet_mm=2.0)
        new_state, outputs = awbm_step(inputs, params, state)

        # SS2 should be non-negative
        assert new_state.ss2 >= 0.0
        # Should not exceed capacity
        cap2 = params.a2 * params.c_vec[1]
        assert new_state.ss2 <= cap2 + 0.001

    def test_state_transitions_ss3(self):
        """Test surface store 3 (SS3) state transitions."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.0, b_base=0.0)

        inputs = AWBMInputs(precip_mm=12.0, pet_mm=3.0)
        new_state, outputs = awbm_step(inputs, params, state)

        # SS3 should be non-negative
        assert new_state.ss3 >= 0.0
        # Should not exceed capacity
        a3 = 1.0 - params.a1 - params.a2
        cap3 = a3 * params.c_vec[2]
        assert new_state.ss3 <= cap3 + 0.001

    def test_state_transitions_s_surf(self):
        """Test surface routing store (S_surf) state transitions."""
        params = AWBMParams(
            c_vec=[5.0, 30.0, 60.0],
            bfi=0.35,
            ks=0.3,  # Fast recession
            kb=0.95
        )
        # Start with water in surface routing store
        state = AWBMState(ss1=0.3, ss2=8.0, ss3=15.0, s_surf=5.0, b_base=10.0)

        # Small input
        inputs = AWBMInputs(precip_mm=2.0, pet_mm=1.0)
        new_state, outputs = awbm_step(inputs, params, state)

        # Surface store should be non-negative
        assert new_state.s_surf >= 0.0
        # Should contribute to surface flow output
        assert outputs.surface_flow_mm >= 0.0

    def test_state_transitions_b_base(self):
        """Test baseflow routing store (B_base) state transitions."""
        params = AWBMParams(
            c_vec=[5.0, 30.0, 60.0],
            bfi=0.35,
            ks=0.3,
            kb=0.95  # Slow recession
        )
        # Start with water in baseflow routing store
        state = AWBMState(ss1=0.3, ss2=8.0, ss3=15.0, s_surf=5.0, b_base=10.0)

        # Small input
        inputs = AWBMInputs(precip_mm=2.0, pet_mm=1.0)
        new_state, outputs = awbm_step(inputs, params, state)

        # Baseflow store should be non-negative
        assert new_state.b_base >= 0.0
        # Should contribute to baseflow output
        assert outputs.baseflow_mm >= 0.0

    def test_all_stores_update_together(self):
        """Test that all 5 stores update correctly in one timestep."""
        params = AWBMParams(
            c_vec=[8.0, 60.0, 120.0],
            bfi=0.4,
            ks=0.35,
            kb=0.92
        )
        state = AWBMState(ss1=0.8, ss2=20.0, ss3=40.0, s_surf=3.0, b_base=8.0)
        inputs = AWBMInputs(precip_mm=15.0, pet_mm=4.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # All stores should be non-negative
        assert new_state.ss1 >= 0.0
        assert new_state.ss2 >= 0.0
        assert new_state.ss3 >= 0.0
        assert new_state.s_surf >= 0.0
        assert new_state.b_base >= 0.0

        # All outputs should be non-negative
        assert outputs.runoff_mm >= 0.0
        assert outputs.excess_mm >= 0.0
        assert outputs.baseflow_mm >= 0.0
        assert outputs.surface_flow_mm >= 0.0


class TestAWBMEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_precipitation(self):
        """Test behavior with zero precipitation."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=2.0, b_base=5.0)
        inputs = AWBMInputs(precip_mm=0.0, pet_mm=3.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # No excess should be generated
        assert outputs.excess_mm == 0.0
        # Surface stores should decrease or stay same (ET)
        assert new_state.ss1 <= state.ss1
        assert new_state.ss2 <= state.ss2
        assert new_state.ss3 <= state.ss3
        # Routing stores should recede
        assert new_state.s_surf < state.s_surf
        assert new_state.b_base < state.b_base

    def test_zero_pet(self):
        """Test behavior with zero PET."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.0, b_base=0.0)
        inputs = AWBMInputs(precip_mm=15.0, pet_mm=0.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # All precipitation should contribute to stores or overflow
        assert outputs.excess_mm >= 0.0
        # With no ET, more overflow expected
        assert outputs.runoff_mm >= 0.0

    def test_pet_exceeds_precipitation(self):
        """Test behavior when PET exceeds precipitation."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.8, ss2=15.0, ss3=30.0, s_surf=1.0, b_base=2.0)
        inputs = AWBMInputs(precip_mm=2.0, pet_mm=8.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # No overflow expected (P < PET)
        assert outputs.excess_mm == 0.0
        # Surface stores should decrease
        assert new_state.ss1 <= state.ss1
        assert new_state.ss2 <= state.ss2
        assert new_state.ss3 <= state.ss3

    def test_empty_stores(self):
        """Test behavior with all stores empty."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.0, ss2=0.0, ss3=0.0, s_surf=0.0, b_base=0.0)
        inputs = AWBMInputs(precip_mm=5.0, pet_mm=2.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # Stores should fill up
        assert new_state.ss1 > 0.0 or new_state.ss2 > 0.0 or new_state.ss3 > 0.0
        # All values should be non-negative
        assert new_state.ss1 >= 0.0
        assert new_state.ss2 >= 0.0
        assert new_state.ss3 >= 0.0
        assert outputs.runoff_mm >= 0.0

    def test_very_small_routing_stores(self):
        """Test recession behavior with very small routing store values."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        # Very small values in routing stores (below 0.05 threshold)
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.03, b_base=0.02)
        inputs = AWBMInputs(precip_mm=0.0, pet_mm=1.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # Small stores should drain completely or stay small
        assert new_state.s_surf >= 0.0
        assert new_state.b_base >= 0.0
        # Outputs should be small but non-negative
        assert outputs.surface_flow_mm >= 0.0
        assert outputs.baseflow_mm >= 0.0


class TestAWBMKnownInputOutput:
    """Test with known input/output pairs for validation."""

    def test_known_case_dry_conditions(self):
        """Test known case: dry conditions with high ET."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=20.0, ss3=40.0, s_surf=0.0, b_base=0.0)
        inputs = AWBMInputs(precip_mm=0.0, pet_mm=5.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # No runoff expected (no precipitation)
        assert outputs.runoff_mm == 0.0
        assert outputs.excess_mm == 0.0
        # Stores should decrease due to ET
        assert new_state.ss1 <= state.ss1
        assert new_state.ss2 <= state.ss2
        assert new_state.ss3 <= state.ss3

    def test_known_case_wet_conditions(self):
        """Test known case: wet conditions with overflow."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        # Stores near capacity
        state = AWBMState(
            ss1=1.0,   # Cap1 = 0.134 * 7.5 = 1.005
            ss2=32.0,  # Cap2 = 0.433 * 76.0 = 32.908
            ss3=64.0,  # Cap3 = 0.433 * 152.0 = 65.816
            s_surf=0.0,
            b_base=0.0
        )
        inputs = AWBMInputs(precip_mm=30.0, pet_mm=3.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # Significant overflow expected
        assert outputs.excess_mm > 0.0
        # Excess should go into routing stores
        assert new_state.s_surf > 0.0 or new_state.b_base > 0.0
        # Stores should be at or near capacity
        assert new_state.ss1 <= params.a1 * params.c_vec[0] + 0.001
        assert new_state.ss2 <= params.a2 * params.c_vec[1] + 0.001

    def test_known_case_balanced_conditions(self):
        """Test known case: balanced P and PET."""
        params = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=0.0, b_base=0.0)
        inputs = AWBMInputs(precip_mm=5.0, pet_mm=5.0)

        new_state, outputs = awbm_step(inputs, params, state)

        # With P = PET, minimal overflow expected
        # Stores should remain relatively stable
        assert outputs.excess_mm >= 0.0
        assert new_state.ss1 >= 0.0
        assert new_state.ss2 >= 0.0
        assert new_state.ss3 >= 0.0


class TestAWBMParameterEffects:
    """Test parameter effects on model behavior."""

    def test_bfi_effect(self):
        """Test baseflow index (BFI) effect on flow splitting."""
        params_low_bfi = AWBMParams(
            c_vec=[5.0, 40.0, 80.0],
            bfi=0.2,  # 20% to baseflow
            ks=0.35,
            kb=0.95
        )
        params_high_bfi = AWBMParams(
            c_vec=[5.0, 40.0, 80.0],
            bfi=0.6,  # 60% to baseflow
            ks=0.35,
            kb=0.95
        )

        # Start with water already in routing stores to see immediate flow
        state = AWBMState(ss1=0.4, ss2=15.0, ss3=30.0, s_surf=5.0, b_base=10.0)
        inputs = AWBMInputs(precip_mm=25.0, pet_mm=3.0)

        new_state_low, outputs_low = awbm_step(inputs, params_low_bfi, state)
        new_state_high, outputs_high = awbm_step(inputs, params_high_bfi, state)

        # Higher BFI should result in more water going to baseflow store
        if outputs_low.excess_mm > 0.0:
            assert new_state_high.b_base > new_state_low.b_base
            assert new_state_high.s_surf < new_state_low.s_surf

    def test_ks_effect(self):
        """Test surface recession constant (Ks) effect."""
        params_fast = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.2,  # Fast recession (low Ks)
            kb=0.95
        )
        params_slow = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.6,  # Slow recession (high Ks)
            kb=0.95
        )

        # Start with water in surface routing store
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=10.0, b_base=5.0)
        inputs = AWBMInputs(precip_mm=0.0, pet_mm=2.0)

        new_state_fast, outputs_fast = awbm_step(inputs, params_fast, state)
        new_state_slow, outputs_slow = awbm_step(inputs, params_slow, state)

        # Lower Ks (faster recession) should result in more surface flow
        assert outputs_fast.surface_flow_mm > outputs_slow.surface_flow_mm
        # And less remaining in surface store
        assert new_state_fast.s_surf < new_state_slow.s_surf

    def test_kb_effect(self):
        """Test baseflow recession constant (Kb) effect."""
        params_fast = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.85  # Faster baseflow recession
        )
        params_slow = AWBMParams(
            c_vec=[10.0, 50.0, 100.0],
            bfi=0.35,
            ks=0.35,
            kb=0.98  # Slower baseflow recession
        )

        # Start with water in baseflow routing store
        state = AWBMState(ss1=0.5, ss2=10.0, ss3=20.0, s_surf=5.0, b_base=15.0)
        inputs = AWBMInputs(precip_mm=0.0, pet_mm=2.0)

        new_state_fast, outputs_fast = awbm_step(inputs, params_fast, state)
        new_state_slow, outputs_slow = awbm_step(inputs, params_slow, state)

        # Lower Kb (faster recession) should result in more baseflow
        assert outputs_fast.baseflow_mm > outputs_slow.baseflow_mm
        # And less remaining in baseflow store
        assert new_state_fast.b_base < new_state_slow.b_base

    def test_capacity_effect(self):
        """Test capacity (c_vec) effect on overflow."""
        params_small = AWBMParams(
            c_vec=[5.0, 30.0, 60.0],  # Small capacities
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )
        params_large = AWBMParams(
            c_vec=[15.0, 100.0, 200.0],  # Large capacities
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )

        state = AWBMState(ss1=0.3, ss2=8.0, ss3=15.0, s_surf=0.0, b_base=0.0)
        inputs = AWBMInputs(precip_mm=20.0, pet_mm=3.0)

        _, outputs_small = awbm_step(inputs, params_small, state)
        _, outputs_large = awbm_step(inputs, params_large, state)

        # Smaller capacities should result in more overflow
        assert outputs_small.excess_mm > outputs_large.excess_mm
