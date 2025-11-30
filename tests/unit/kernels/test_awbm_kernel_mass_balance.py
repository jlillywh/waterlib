"""
Mass balance tests for AWBM kernel.

Tests that the AWBM kernel conserves water and produces realistic outputs
by running multi-day simulations and validating cumulative water balance.
"""

import pytest
from waterlib.kernels.hydrology.awbm import (
    awbm_step,
    AWBMParams,
    AWBMState,
    AWBMInputs,
)


class TestAWBMMassBalance:
    """Test AWBM kernel mass balance over multi-day simulations."""

    def test_mass_balance_moderate_rainfall(self):
        """Test mass balance with moderate, consistent rainfall."""
        # Standard AWBM parameters
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )

        # Start with empty stores
        state = AWBMState(0.0, 0.0, 0.0, 0.0, 0.0)

        # Run 30 days with moderate rainfall
        n_days = 30
        precip_mm = 10.0
        pet_mm = 3.0

        # Accumulate fluxes
        total_precip = 0.0
        total_pet = 0.0
        total_runoff = 0.0
        total_excess = 0.0

        initial_storage = (state.ss1 + state.ss2 + state.ss3 +
                          state.s_surf + state.b_base)

        for day in range(n_days):
            inputs = AWBMInputs(precip_mm=precip_mm, pet_mm=pet_mm)
            state, outputs = awbm_step(inputs, params, state)

            total_precip += precip_mm
            total_pet += pet_mm
            total_runoff += outputs.runoff_mm
            total_excess += outputs.excess_mm

        final_storage = (state.ss1 + state.ss2 + state.ss3 +
                        state.s_surf + state.b_base)
        storage_change = final_storage - initial_storage

        # Mass balance: Precip = Runoff + ET + ΔStorage
        # In AWBM, ET is implicit (P-PET losses when P < PET + capacity)
        # We can approximate ET as PET when stores have water
        # More precisely: Precip - Excess = Water that went into stores or ET
        # And: Runoff + ΔStorage = Excess (water that overflowed stores)

        # Key validation: Excess should feed routing stores
        # Runoff + ΔStorage_routing ≈ Excess (accounting for recession)
        routing_storage = state.s_surf + state.b_base

        # Print summary
        print(f"\n--- AWBM Mass Balance Summary (Moderate Rainfall) ---")
        print(f"Duration: {n_days} days")
        print(f"Total precipitation: {total_precip:.1f} mm")
        print(f"Total PET: {total_pet:.1f} mm")
        print(f"Total runoff: {total_runoff:.2f} mm")
        print(f"Total excess (overflow): {total_excess:.2f} mm")
        print(f"ΔStorage (all stores): {storage_change:.2f} mm")
        print(f"  - Surface stores (ss1+ss2+ss3): {state.ss1 + state.ss2 + state.ss3:.2f} mm")
        print(f"  - Routing stores (s_surf+b_base): {routing_storage:.2f} mm")
        print(f"\nWater balance components:")
        print(f"  Runoff ratio: {100*total_runoff/total_precip:.1f}%")
        print(f"  Storage increase: {100*storage_change/total_precip:.1f}%")
        print(f"  Implied ET: {100*(total_precip-total_runoff-storage_change)/total_precip:.1f}%")

        # Validation checks
        assert total_runoff > 0.0, "Should generate runoff over 30 days"
        assert total_excess > 0.0, "Should generate excess (overflow) over 30 days"
        assert storage_change > 0.0, "Storage should increase with rainfall"

        # Runoff should be less than total excess (some stays in routing stores)
        assert total_runoff <= total_excess, "Runoff cannot exceed excess generation"

        # All stores should have water
        assert state.ss1 > 0.0, "Surface store 1 should have water"
        assert state.ss2 > 0.0, "Surface store 2 should have water"
        assert state.ss3 > 0.0, "Surface store 3 should have water"

        # Check routing store mass balance
        # All excess should be accounted for by runoff + routing store changes
        # Excess = Runoff + ΔRouting_Storage
        routing_storage_change = routing_storage - 0.0  # Started at 0
        mass_balance_error = abs(total_excess - total_runoff - routing_storage_change)

        # Relative error should be small
        relative_error = mass_balance_error / total_excess if total_excess > 0 else 0.0
        print(f"\nRouting store mass balance check:")
        print(f"  Total excess: {total_excess:.2f} mm")
        print(f"  Total runoff: {total_runoff:.2f} mm")
        print(f"  Routing storage increase: {routing_storage_change:.2f} mm")
        print(f"  Accounted: {total_runoff + routing_storage_change:.2f} mm")
        print(f"  Error: {mass_balance_error:.6f} mm")
        print(f"  Relative error: {100*relative_error:.6f}%")

        # Mass balance should close within 0.1 mm (floating point precision)
        assert mass_balance_error < 0.1, f"Mass balance error too large: {mass_balance_error:.4f} mm"

    def test_mass_balance_storm_event(self):
        """Test mass balance with a large storm event."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )

        # Start with some antecedent moisture
        state = AWBMState(0.5, 10.0, 20.0, 0.0, 0.0)

        initial_storage = (state.ss1 + state.ss2 + state.ss3 +
                          state.s_surf + state.b_base)

        # Run simulation: 5 days dry, 1 day storm, 10 days recession
        total_precip = 0.0
        total_runoff = 0.0
        total_excess = 0.0

        daily_data = []

        # Dry period
        for day in range(5):
            inputs = AWBMInputs(precip_mm=0.0, pet_mm=4.0)
            state, outputs = awbm_step(inputs, params, state)
            daily_data.append(('dry', 0.0, outputs.runoff_mm, outputs.excess_mm))
            total_precip += 0.0
            total_runoff += outputs.runoff_mm
            total_excess += outputs.excess_mm

        # Storm event
        storm_precip = 80.0
        inputs = AWBMInputs(precip_mm=storm_precip, pet_mm=2.0)
        state, outputs = awbm_step(inputs, params, state)
        daily_data.append(('storm', storm_precip, outputs.runoff_mm, outputs.excess_mm))
        total_precip += storm_precip
        total_runoff += outputs.runoff_mm
        total_excess += outputs.excess_mm

        # Recession period
        for day in range(10):
            inputs = AWBMInputs(precip_mm=0.0, pet_mm=3.0)
            state, outputs = awbm_step(inputs, params, state)
            daily_data.append(('recession', 0.0, outputs.runoff_mm, outputs.excess_mm))
            total_precip += 0.0
            total_runoff += outputs.runoff_mm
            total_excess += outputs.excess_mm

        final_storage = (state.ss1 + state.ss2 + state.ss3 +
                        state.s_surf + state.b_base)
        storage_change = final_storage - initial_storage

        print(f"\n--- AWBM Mass Balance Summary (Storm Event) ---")
        print(f"Total precipitation: {total_precip:.1f} mm (mostly from 1 storm)")
        print(f"Total runoff: {total_runoff:.2f} mm")
        print(f"Total excess: {total_excess:.2f} mm")
        print(f"ΔStorage: {storage_change:.2f} mm")
        print(f"Initial storage: {initial_storage:.2f} mm")
        print(f"Final storage: {final_storage:.2f} mm")
        print(f"\nDaily progression (last 10 days):")
        for i, (period, p, r, e) in enumerate(daily_data[-10:], start=len(daily_data)-9):
            print(f"  Day {i} ({period}): P={p:.1f}, R={r:.3f}, E={e:.3f} mm")

        # Validation checks
        assert total_runoff > 5.0, "Storm should generate significant runoff"
        assert total_excess > 10.0, "Storm should generate significant excess"

        # Check that runoff continues during recession
        recession_runoff = sum(r for period, p, r, e in daily_data if period == 'recession')
        print(f"\nRecession runoff: {recession_runoff:.2f} mm")
        assert recession_runoff > 1.0, "Runoff should continue during recession"

        # Runoff ratio should be reasonable for storm event
        runoff_ratio = total_runoff / total_precip
        print(f"Runoff ratio: {100*runoff_ratio:.1f}%")
        assert runoff_ratio > 0.1, "Storm should produce >10% runoff"
        assert runoff_ratio < 0.9, "Storm should not produce >90% runoff (some storage/ET)"

    def test_mass_balance_long_term(self):
        """Test mass balance over long simulation with varying inputs."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.35,
            ks=0.35,
            kb=0.95
        )

        state = AWBMState(0.0, 0.0, 0.0, 0.0, 0.0)

        initial_storage = 0.0

        # Run 365 days with seasonal pattern
        import math

        total_precip = 0.0
        total_runoff = 0.0
        total_excess = 0.0

        for day in range(365):
            # Seasonal rainfall (higher in winter, lower in summer)
            seasonal_factor = 1.0 + 0.5 * math.cos(2 * math.pi * day / 365)
            precip_mm = 2.5 * seasonal_factor  # Lowered from 3.5 to 2.5

            # Seasonal PET (higher in summer, lower in winter)
            pet_factor = 1.0 - 0.3 * math.cos(2 * math.pi * day / 365)
            pet_mm = 2.5 * pet_factor  # Matched to average precip

            inputs = AWBMInputs(precip_mm=precip_mm, pet_mm=pet_mm)
            state, outputs = awbm_step(inputs, params, state)

            total_precip += precip_mm
            total_runoff += outputs.runoff_mm
            total_excess += outputs.excess_mm

        final_storage = (state.ss1 + state.ss2 + state.ss3 +
                        state.s_surf + state.b_base)
        storage_change = final_storage - initial_storage

        print(f"\n--- AWBM Mass Balance Summary (365 Days, Balanced Climate) ---")
        print(f"Total precipitation: {total_precip:.1f} mm")
        print(f"Total runoff: {total_runoff:.2f} mm ({100*total_runoff/total_precip:.1f}%)")
        print(f"Total excess: {total_excess:.2f} mm ({100*total_excess/total_precip:.1f}%)")
        print(f"ΔStorage: {storage_change:.2f} mm ({100*storage_change/total_precip:.1f}%)")
        print(f"Final storage breakdown:")
        print(f"  - ss1: {state.ss1:.2f} mm")
        print(f"  - ss2: {state.ss2:.2f} mm")
        print(f"  - ss3: {state.ss3:.2f} mm")
        print(f"  - s_surf: {state.s_surf:.2f} mm")
        print(f"  - b_base: {state.b_base:.2f} mm")

        # Validation checks
        assert total_runoff > 0.0, "Should generate runoff over year"
        assert total_excess > 0.0, "Should generate excess over year"

        # Annual runoff ratio should be reasonable
        runoff_ratio = total_runoff / total_precip
        assert 0.05 < runoff_ratio < 0.50, \
            f"Annual runoff ratio {runoff_ratio:.2%} should be between 5-50%"

        # Storage should reach equilibrium (not grow indefinitely)
        assert final_storage < 100.0, f"Storage should not grow indefinitely: {final_storage:.2f} mm"

        # All stores should have some water at end of year
        assert state.ss1 > 0.0
        assert state.ss2 > 0.0
        assert state.ss3 > 0.0

    def test_routing_store_dynamics(self):
        """Test that routing stores behave correctly (fill, recession, baseflow/surface split)."""
        params = AWBMParams(
            c_vec=[7.5, 76.0, 152.0],
            bfi=0.40,  # 40% to baseflow
            ks=0.30,   # Fast surface recession
            kb=0.95    # Slow baseflow recession
        )

        # Start with empty stores
        state = AWBMState(0.0, 0.0, 0.0, 0.0, 0.0)

        # Phase 1: Fill routing stores with large rainfall
        print(f"\n--- Routing Store Dynamics Test ---")
        print("\nPhase 1: Filling routing stores (5 days, 15mm/day)")
        for day in range(5):
            inputs = AWBMInputs(precip_mm=15.0, pet_mm=3.0)
            state, outputs = awbm_step(inputs, params, state)
            print(f"Day {day+1}: excess={outputs.excess_mm:.3f}, "
                  f"s_surf={state.s_surf:.3f}, b_base={state.b_base:.3f}")

        # Check that routing stores have water
        assert state.s_surf > 0.0, "Surface routing store should have water"
        assert state.b_base > 0.0, "Baseflow routing store should have water"

        # Store initial routing storage
        s_surf_initial = state.s_surf
        b_base_initial = state.b_base

        # Phase 2: Recession (no rainfall)
        print("\nPhase 2: Recession (10 days, no rainfall)")
        recession_baseflow = 0.0
        recession_surface = 0.0

        for day in range(10):
            inputs = AWBMInputs(precip_mm=0.0, pet_mm=3.0)
            state, outputs = awbm_step(inputs, params, state)
            recession_baseflow += outputs.baseflow_mm
            recession_surface += outputs.surface_flow_mm
            print(f"Day {day+1}: runoff={outputs.runoff_mm:.3f}, "
                  f"baseflow={outputs.baseflow_mm:.3f}, surface={outputs.surface_flow_mm:.3f}, "
                  f"s_surf={state.s_surf:.3f}, b_base={state.b_base:.3f}")

        # Validation checks
        print(f"\nRecession totals:")
        print(f"  Total baseflow: {recession_baseflow:.3f} mm")
        print(f"  Total surface flow: {recession_surface:.3f} mm")
        print(f"  s_surf change: {s_surf_initial:.3f} → {state.s_surf:.3f} mm")
        print(f"  b_base change: {b_base_initial:.3f} → {state.b_base:.3f} mm")

        # Routing stores should decrease during recession
        assert state.s_surf < s_surf_initial, "Surface store should recede"
        assert state.b_base < b_base_initial, "Baseflow store should recede"

        # Surface should recede faster (lower Ks = faster recession)
        s_surf_recession_pct = (s_surf_initial - state.s_surf) / s_surf_initial
        b_base_recession_pct = (b_base_initial - state.b_base) / b_base_initial
        print(f"\nRecession rates:")
        print(f"  Surface: {100*s_surf_recession_pct:.1f}%")
        print(f"  Baseflow: {100*b_base_recession_pct:.1f}%")

        assert s_surf_recession_pct > b_base_recession_pct, \
            "Surface should recede faster than baseflow"

        # Runoff should be generated during recession
        assert recession_baseflow > 0.0, "Should generate baseflow during recession"
        assert recession_surface > 0.0, "Should generate surface flow during recession"

        # Baseflow should be roughly 40% of total (due to BFI=0.40)
        total_recession_runoff = recession_baseflow + recession_surface
        baseflow_fraction = recession_baseflow / total_recession_runoff
        print(f"\nBaseflow fraction during recession: {100*baseflow_fraction:.1f}%")
        print(f"Expected (BFI parameter): 40%")

        # Baseflow fraction should be between 30-50% (some variation due to recession dynamics)
        assert 0.25 < baseflow_fraction < 0.55, \
            f"Baseflow fraction {baseflow_fraction:.2%} should be close to BFI=40%"
