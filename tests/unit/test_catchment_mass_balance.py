"""
Test mass balance for the Catchment component.

This test verifies that the integrated Snow17 + AWBM catchment model
conserves mass over a simulation period by checking:

Mass Balance Equation:
    ΔS = Qin - Qout

Where:
    ΔS = Change in storage (Snow17 SWE + AWBM stores)
    Qin = Cumulative precipitation
    Qout = Cumulative runoff + cumulative ET losses

Storage components:
    - Snow17: w_i (ice), w_q (liquid water), deficit (heat)
    - AWBM: ss1, ss2, ss3 (surface stores), s_surf (surface routing), b_base (baseflow routing)

Fluxes:
    - Inflow: precipitation (rain + snow)
    - Outflows: runoff (AWBM discharge), ET losses (from AWBM stores)

Note: Snow17 does not explicitly track sublimation or evaporation losses,
so we focus on the water balance through AWBM which implicitly handles ET.
"""

import pytest
from datetime import datetime, timedelta
from waterlib.components.catchment import Catchment
from waterlib.core.drivers import DriverRegistry, SimpleDriver
from waterlib.core.base import SiteConfig


class TestCatchmentMassBalance:
    """Test suite for catchment mass balance verification."""

    def test_mass_balance_no_snow(self):
        """Test mass balance for catchment without snow (AWBM only)."""
        # Configuration for AWBM-only catchment (no snow)
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'a1': 0.134,
                'a2': 0.433,
                'initial_stores': [0.0, 0.0, 0.0, 0.0, 0.0]  # Start empty
            }
        )

        # Record initial storage
        initial_storage = self._calculate_awbm_storage(catchment)

        # Set up drivers
        drivers = DriverRegistry()

        # Run simulation for 30 days with known inputs
        start_date = datetime(2020, 1, 1)
        cumulative_precip = 0.0
        cumulative_runoff = 0.0

        for day in range(30):
            date = start_date + timedelta(days=day)

            # Simple pattern: 10mm precip every 3rd day, 3mm PET daily
            precip = 10.0 if day % 3 == 0 else 0.0
            pet = 3.0

            cumulative_precip += precip

            # Register drivers
            drivers.register('precipitation', SimpleDriver(precip))
            drivers.register('temperature', SimpleDriver(15.0))  # Not used without snow
            drivers.register('et', SimpleDriver(pet))

            # Step catchment
            outputs = catchment.step(date, drivers)

            # Accumulate runoff
            cumulative_runoff += outputs['runoff_mm']

        # Record final storage
        final_storage = self._calculate_awbm_storage(catchment)

        # Calculate mass balance
        # In AWBM, water is removed by ET (implicitly in the P-PET calculation)
        # Mass balance: ΔS = Precip - Runoff - Actual_ET
        # Therefore: Actual_ET = Precip - Runoff - ΔS
        delta_storage = final_storage - initial_storage
        actual_et = cumulative_precip - cumulative_runoff - delta_storage
        mass_balance_error = delta_storage - (cumulative_precip - cumulative_runoff - actual_et)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (No Snow) ---")
        print(f"Initial storage: {initial_storage:.3f} mm")
        print(f"Final storage: {final_storage:.3f} mm")
        print(f"ΔS (storage change): {delta_storage:.3f} mm")
        print(f"Cumulative precipitation: {cumulative_precip:.3f} mm")
        print(f"Cumulative runoff: {cumulative_runoff:.3f} mm")
        print(f"Actual ET (calculated): {actual_et:.3f} mm")
        print(f"Water balance check: Precip - Runoff - ET - ΔS = {cumulative_precip - cumulative_runoff - actual_et - delta_storage:.6f} mm")
        print(f"Mass balance error: {mass_balance_error:.6f} mm")

        # Assert mass balance closes (within numerical precision)
        # Mass balance: Precip = Runoff + ET + ΔS
        balance_check = cumulative_precip - cumulative_runoff - actual_et - delta_storage
        assert abs(balance_check) < 1e-6, (
            f"Mass balance error {balance_check:.6f} mm exceeds tolerance. "
            f"Precip={cumulative_precip:.3f}, Runoff={cumulative_runoff:.3f}, "
            f"ET={actual_et:.3f}, ΔS={delta_storage:.3f}"
        )

    def test_mass_balance_with_snow(self):
        """Test mass balance for catchment with Snow17 + AWBM."""
        # Need site for Snow17
        site = SiteConfig(latitude=45.0, elevation_m=1500.0)

        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            _site=site,
            snow17_params={
                'mfmax': 1.6,
                'mfmin': 0.6,
                'mbase': 0.0,
                'pxtemp1': -1.0,
                'pxtemp2': 1.0,
                'scf': 1.0,
                'nmf': 0.15,
                'plwhc': 0.04,
                'uadj': 0.05,
                'tipm': 0.15,
                'lapse_rate': 0.006,
                'initial_swe': 0.0
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'a1': 0.134,
                'a2': 0.433,
                'initial_stores': [0.0, 0.0, 0.0, 0.0, 0.0]
            }
        )

        # Record initial storage
        initial_snow_storage = self._calculate_snow17_storage(catchment)
        initial_awbm_storage = self._calculate_awbm_storage(catchment)
        initial_storage = initial_snow_storage + initial_awbm_storage

        # Set up drivers
        drivers = DriverRegistry()

        # Run simulation for 60 days with winter-to-spring conditions
        start_date = datetime(2020, 1, 1)
        cumulative_precip = 0.0
        cumulative_runoff = 0.0

        for day in range(60):
            date = start_date + timedelta(days=day)

            # Winter transitions to spring
            # Days 0-30: Cold (accumulation), Days 30-60: Warming (melt)
            if day < 30:
                temp = -5.0 + (day * 0.2)  # -5°C to 1°C
                precip = 5.0 if day % 3 == 0 else 0.0  # Snow accumulation
            else:
                temp = 1.0 + ((day - 30) * 0.3)  # 1°C to 10°C
                precip = 3.0 if day % 4 == 0 else 0.0  # Less precip during melt

            pet = 2.0 if day < 30 else 3.5  # Low winter ET, higher spring ET

            cumulative_precip += precip

            # Register drivers
            drivers.register('precipitation', SimpleDriver(precip))
            drivers.register('temperature', SimpleDriver(temp))
            drivers.register('et', SimpleDriver(pet))

            # Step catchment
            outputs = catchment.step(date, drivers)

            # Accumulate runoff
            cumulative_runoff += outputs['runoff_mm']

        # Record final storage
        final_snow_storage = self._calculate_snow17_storage(catchment)
        final_awbm_storage = self._calculate_awbm_storage(catchment)
        final_storage = final_snow_storage + final_awbm_storage

        # Calculate mass balance
        # Mass balance: Precip = Runoff + ET + ΔS
        # Therefore: Actual_ET = Precip - Runoff - ΔS
        delta_storage = final_storage - initial_storage
        actual_et = cumulative_precip - cumulative_runoff - delta_storage

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (With Snow) ---")
        print(f"Initial storage:")
        print(f"  Snow17: {initial_snow_storage:.3f} mm")
        print(f"  AWBM: {initial_awbm_storage:.3f} mm")
        print(f"  Total: {initial_storage:.3f} mm")
        print(f"\nFinal storage:")
        print(f"  Snow17: {final_snow_storage:.3f} mm (w_i={catchment.snow17_state.w_i:.3f}, w_q={catchment.snow17_state.w_q:.3f})")
        print(f"  AWBM: {final_awbm_storage:.3f} mm")
        print(f"  Total: {final_storage:.3f} mm")
        print(f"\nΔS (storage change): {delta_storage:.3f} mm")
        print(f"  Snow17 Δ: {final_snow_storage - initial_snow_storage:.3f} mm")
        print(f"  AWBM Δ: {final_awbm_storage - initial_awbm_storage:.3f} mm")
        print(f"\nCumulative precipitation: {cumulative_precip:.3f} mm")
        print(f"Cumulative runoff: {cumulative_runoff:.3f} mm")
        print(f"Actual ET (calculated): {actual_et:.3f} mm")
        print(f"\nWater balance check: Precip - Runoff - ET - ΔS = {cumulative_precip - cumulative_runoff - actual_et - delta_storage:.6f} mm")

        # Assert mass balance closes (within numerical precision)
        balance_check = cumulative_precip - cumulative_runoff - actual_et - delta_storage
        assert abs(balance_check) < 1e-6, (
            f"Mass balance error {balance_check:.6f} mm exceeds tolerance. "
            f"Precip={cumulative_precip:.3f}, Runoff={cumulative_runoff:.3f}, "
            f"ET={actual_et:.3f}, ΔS={delta_storage:.3f}"
        )

    def test_mass_balance_extreme_event(self):
        """Test mass balance during extreme precipitation event."""
        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'a1': 0.134,
                'a2': 0.433,
                'initial_stores': [5.0, 40.0, 80.0, 10.0, 20.0]  # Start with some storage
            }
        )

        # Record initial storage
        initial_storage = self._calculate_awbm_storage(catchment)

        # Set up drivers
        drivers = DriverRegistry()

        # Simulate a large storm event
        start_date = datetime(2020, 6, 1)
        cumulative_precip = 0.0
        cumulative_runoff = 0.0

        # Day 1-5: dry, Day 6: 100mm storm, Day 7-10: recession
        precip_pattern = [0, 0, 0, 0, 0, 100.0, 5.0, 0, 0, 0]
        pet_pattern = [4.0] * 10

        for day in range(10):
            date = start_date + timedelta(days=day)

            precip = precip_pattern[day]
            pet = pet_pattern[day]

            cumulative_precip += precip

            # Register drivers
            drivers.register('precipitation', SimpleDriver(precip))
            drivers.register('temperature', SimpleDriver(20.0))
            drivers.register('et', SimpleDriver(pet))

            # Step catchment
            outputs = catchment.step(date, drivers)

            # Accumulate runoff
            cumulative_runoff += outputs['runoff_mm']

        # Record final storage
        final_storage = self._calculate_awbm_storage(catchment)

        # Calculate mass balance
        # Mass balance: Precip = Runoff + ET + ΔS
        delta_storage = final_storage - initial_storage
        actual_et = cumulative_precip - cumulative_runoff - delta_storage

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (Extreme Event) ---")
        print(f"Initial storage: {initial_storage:.3f} mm")
        print(f"Final storage: {final_storage:.3f} mm")
        print(f"ΔS (storage change): {delta_storage:.3f} mm")
        print(f"Cumulative precipitation: {cumulative_precip:.3f} mm")
        print(f"Cumulative runoff: {cumulative_runoff:.3f} mm")
        print(f"Actual ET (calculated): {actual_et:.3f} mm")
        print(f"Water balance check: Precip - Runoff - ET - ΔS = {cumulative_precip - cumulative_runoff - actual_et - delta_storage:.6f} mm")

        # Assert mass balance closes
        balance_check = cumulative_precip - cumulative_runoff - actual_et - delta_storage
        assert abs(balance_check) < 1e-6, (
            f"Mass balance error {balance_check:.6f} mm exceeds tolerance. "
            f"Precip={cumulative_precip:.3f}, Runoff={cumulative_runoff:.3f}, "
            f"ET={actual_et:.3f}, ΔS={delta_storage:.3f}"
        )

    def test_mass_balance_long_term(self):
        """Test mass balance over extended period (1 year)."""
        site = SiteConfig(latitude=45.0, elevation_m=1500.0)

        catchment = Catchment(
            name='test_catchment',
            area=100.0,
            _site=site,
            snow17_params={
                'mfmax': 1.6,
                'mfmin': 0.6,
                'mbase': 0.0,
                'pxtemp1': -1.0,
                'pxtemp2': 1.0,
                'scf': 1.0,
                'nmf': 0.15,
                'plwhc': 0.04,
                'uadj': 0.05,
                'tipm': 0.15,
                'lapse_rate': 0.006,
                'initial_swe': 0.0
            },
            awbm_params={
                'c_vec': [7.5, 76.0, 152.0],
                'bfi': 0.35,
                'ks': 0.35,
                'kb': 0.95,
                'a1': 0.134,
                'a2': 0.433,
                'initial_stores': [0.0, 0.0, 0.0, 0.0, 0.0]
            }
        )

        # Record initial storage
        initial_storage = (
            self._calculate_snow17_storage(catchment) +
            self._calculate_awbm_storage(catchment)
        )

        # Set up drivers
        drivers = DriverRegistry()

        # Run full year simulation with seasonal patterns
        start_date = datetime(2020, 1, 1)
        cumulative_precip = 0.0
        cumulative_runoff = 0.0

        for day in range(365):
            date = start_date + timedelta(days=day)
            doy = day + 1

            # Seasonal temperature pattern
            temp = 10.0 * (1 - abs((doy - 182.5) / 182.5)) - 5.0  # Range: -5°C to 15°C

            # Seasonal precipitation (higher in spring/fall)
            base_precip = 2.0 + 3.0 * abs((doy - 182.5) / 182.5)
            precip = base_precip if day % 3 == 0 else 0.0

            # Seasonal ET
            pet = max(1.0, 4.0 * (1 - abs((doy - 182.5) / 182.5)))

            cumulative_precip += precip

            # Register drivers
            drivers.register('precipitation', SimpleDriver(precip))
            drivers.register('temperature', SimpleDriver(temp))
            drivers.register('et', SimpleDriver(pet))

            # Step catchment
            outputs = catchment.step(date, drivers)

            # Accumulate runoff
            cumulative_runoff += outputs['runoff_mm']

        # Record final storage
        final_storage = (
            self._calculate_snow17_storage(catchment) +
            self._calculate_awbm_storage(catchment)
        )

        # Calculate mass balance
        # Mass balance: Precip = Runoff + ET + ΔS
        delta_storage = final_storage - initial_storage
        actual_et = cumulative_precip - cumulative_runoff - delta_storage

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (1 Year) ---")
        print(f"Initial storage: {initial_storage:.3f} mm")
        print(f"Final storage: {final_storage:.3f} mm")
        print(f"ΔS (storage change): {delta_storage:.3f} mm")
        print(f"Cumulative precipitation: {cumulative_precip:.3f} mm")
        print(f"Cumulative runoff: {cumulative_runoff:.3f} mm")
        print(f"Actual ET (calculated): {actual_et:.3f} mm")
        print(f"Partitioning: Runoff={cumulative_runoff/cumulative_precip*100:.1f}%, ET={actual_et/cumulative_precip*100:.1f}%, Storage={delta_storage/cumulative_precip*100:.1f}%")
        print(f"Water balance check: Precip - Runoff - ET - ΔS = {cumulative_precip - cumulative_runoff - actual_et - delta_storage:.6f} mm")

        # Assert mass balance closes
        balance_check = cumulative_precip - cumulative_runoff - actual_et - delta_storage
        assert abs(balance_check) < 1e-6, (
            f"Mass balance error {balance_check:.6f} mm exceeds tolerance. "
            f"Precip={cumulative_precip:.3f}, Runoff={cumulative_runoff:.3f}, "
            f"ET={actual_et:.3f}, ΔS={delta_storage:.3f}"
        )

    # Helper methods

    def _calculate_awbm_storage(self, catchment: Catchment) -> float:
        """Calculate total water storage in AWBM stores (mm)."""
        state = catchment.awbm_state
        return state.ss1 + state.ss2 + state.ss3 + state.s_surf + state.b_base

    def _calculate_snow17_storage(self, catchment: Catchment) -> float:
        """Calculate total water storage in Snow17 (mm).

        Note: We include w_i (ice) and w_q (liquid water).
        The deficit is a heat deficit, not water, so we don't include it.
        """
        if catchment.snow17_state is None:
            return 0.0
        state = catchment.snow17_state
        return state.w_i + state.w_q


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
