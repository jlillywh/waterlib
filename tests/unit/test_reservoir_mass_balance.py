"""
Test mass balance for the Reservoir component.

This test verifies that the reservoir component conserves mass over a
simulation period by checking:

Mass Balance Equation:
    ΔS = Qin - Qout

Where:
    ΔS = Change in storage (final storage - initial storage)
    Qin = Cumulative inflows (all inflow sources)
    Qout = Cumulative outflows (releases + spillway + evaporation)

Storage:
    - Reservoir storage (m³)

Fluxes:
    - Inflows: inflow (controlled/natural inflow)
    - Outflows: release (controlled discharge), spill (spillway overflow), evaporation_loss

The test validates that:
    Initial Storage + Cumulative Inflow - Cumulative Outflow = Final Storage

This ensures water is conserved through all reservoir operations including:
    - Normal storage operations
    - Spillway activation during high flows
    - Evaporation losses from lake surface
    - Controlled releases for demand
"""

import pytest
import random
from datetime import datetime, timedelta
from waterlib.components.reservoir import Reservoir
from waterlib.core.drivers import DriverRegistry, SimpleDriver


class TestReservoirMassBalance:
    """Test suite for reservoir mass balance verification."""

    def test_mass_balance_simple_no_spillway(self):
        """Test mass balance for simple reservoir with spillway (starts near capacity)."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=4500000.0,  # 4.5 million m³ (90% full - close to spillway)
            max_storage=5000000.0,       # 5 million m³ capacity
            surface_area=500000.0        # 0.5 km² = 500,000 m²
        )

        # Record initial storage
        initial_storage = reservoir.storage

        # Track cumulative fluxes
        cumulative_inflow = 0.0
        cumulative_release = 0.0
        cumulative_spill = 0.0
        cumulative_evap = 0.0

        # Random seed for reproducibility
        random.seed(42)

        # Run simulation for 60 days with random inflows and releases
        start_date = datetime(2020, 6, 1)
        for day in range(60):
            date = start_date + timedelta(days=day)

            # Random inflow: 5,000 to 50,000 m³/day
            inflow = random.uniform(5000, 50000)

            # Random release: 5,000 to 25,000 m³/day
            release = random.uniform(5000, 25000)

            # Evaporation rate: 5 mm/day
            evap_rate_mm = 5.0

            # Set up inputs and drivers
            reservoir.inputs['inflow'] = inflow
            reservoir.inputs['release'] = release

            drivers = DriverRegistry()
            drivers.register('et', SimpleDriver(evap_rate_mm))

            # Track cumulative fluxes
            cumulative_inflow += inflow
            cumulative_release += release

            # Step reservoir
            outputs = reservoir.step(date, drivers)

            # Accumulate actual outflows
            cumulative_spill += outputs['spill']
            cumulative_evap += outputs['evaporation_loss']

        # Record final storage
        final_storage = reservoir.storage

        # Calculate mass balance
        delta_storage = final_storage - initial_storage
        total_inflow = cumulative_inflow
        total_outflow = cumulative_release + cumulative_spill + cumulative_evap

        # Mass balance check: ΔS = In - Out
        balance_error = delta_storage - (total_inflow - total_outflow)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (Simple Reservoir) ---")
        print(f"Initial storage: {initial_storage:,.0f} m³")
        print(f"Final storage: {final_storage:,.0f} m³")
        print(f"ΔS (storage change): {delta_storage:,.0f} m³")
        print(f"\nCumulative inflows: {total_inflow:,.0f} m³")
        print(f"Cumulative outflows: {total_outflow:,.0f} m³")
        print(f"  - Releases: {cumulative_release:,.0f} m³")
        print(f"  - Spillway: {cumulative_spill:,.0f} m³")
        print(f"  - Evaporation: {cumulative_evap:,.0f} m³")
        print(f"\nMass balance check: Initial + In - Out - Final = {balance_error:.6f} m³")
        print(f"Relative error: {abs(balance_error / total_inflow * 100):.9f}%")

        # Assert mass balance closes (within numerical precision)
        assert abs(balance_error) < 1e-6, (
            f"Mass balance error {balance_error:.6f} m³ exceeds tolerance. "
            f"Initial={initial_storage}, Final={final_storage}, "
            f"In={total_inflow:.0f}, Out={total_outflow:.0f}"
        )

    def test_mass_balance_with_spillway(self):
        """Test mass balance for reservoir with spillway activation."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=4700000.0,  # Start very close to capacity (94% full)
            max_storage=5000000.0,      # 5 million m³
            surface_area=500000.0       # 0.5 km²
        )

        # Record initial storage
        initial_storage = reservoir.storage

        # Track cumulative fluxes
        cumulative_inflow = 0.0
        cumulative_release = 0.0
        cumulative_spill = 0.0
        cumulative_evap = 0.0

        # Run simulation with high inflows to trigger spillway
        start_date = datetime(2020, 6, 1)
        for day in range(30):
            date = start_date + timedelta(days=day)

            # Flood event: Days 5-10 have very high inflow
            if 5 <= day <= 10:
                inflow = 200000.0  # High inflow to trigger spillway
            else:
                inflow = 15000.0   # Normal inflow

            # Constant release
            release = 10000.0

            # Evaporation rate
            evap_rate_mm = 5.0

            # Set up inputs and drivers
            reservoir.inputs['inflow'] = inflow
            reservoir.inputs['release'] = release

            drivers = DriverRegistry()
            drivers.register('et', SimpleDriver(evap_rate_mm))

            # Track cumulative fluxes
            cumulative_inflow += inflow
            cumulative_release += release

            # Step reservoir
            outputs = reservoir.step(date, drivers)

            # Accumulate actual outflows
            cumulative_spill += outputs['spill']
            cumulative_evap += outputs['evaporation_loss']

        # Record final storage
        final_storage = reservoir.storage

        # Calculate mass balance
        delta_storage = final_storage - initial_storage
        total_inflow = cumulative_inflow
        total_outflow = cumulative_release + cumulative_spill + cumulative_evap

        balance_error = delta_storage - (total_inflow - total_outflow)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (With Spillway) ---")
        print(f"Initial storage: {initial_storage:,.0f} m³ ({initial_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"Final storage: {final_storage:,.0f} m³ ({final_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"ΔS (storage change): {delta_storage:,.0f} m³")
        print(f"\nCumulative inflows: {total_inflow:,.0f} m³")
        print(f"Cumulative outflows: {total_outflow:,.0f} m³")
        print(f"  - Releases: {cumulative_release:,.0f} m³ ({cumulative_release/total_outflow*100:.1f}%)")
        print(f"  - Spillway: {cumulative_spill:,.0f} m³ ({cumulative_spill/total_outflow*100:.1f}%)")
        print(f"  - Evaporation: {cumulative_evap:,.0f} m³ ({cumulative_evap/total_outflow*100:.1f}%)")
        print(f"\nMass balance check: Initial + In - Out - Final = {balance_error:.6f} m³")

        # Assert mass balance closes
        assert abs(balance_error) < 1e-6, (
            f"Mass balance error {balance_error:.6f} m³ exceeds tolerance"
        )

        # Verify spillway was activated
        assert cumulative_spill > 0, "Spillway should have been activated during flood event"

    def test_mass_balance_multiple_inflows(self):
        """Test mass balance with multiple inflow sources (e.g., multiple catchments)."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=2000000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        # Record initial storage
        initial_storage = reservoir.storage

        # Track cumulative fluxes
        cumulative_inflow = 0.0
        cumulative_release = 0.0
        cumulative_spill = 0.0
        cumulative_evap = 0.0

        random.seed(123)

        # Run simulation with multiple inflow sources
        start_date = datetime(2020, 3, 1)
        for day in range(45):
            date = start_date + timedelta(days=day)

            # Multiple inflow sources (e.g., from different catchments)
            inflow_1 = random.uniform(5000, 20000)
            inflow_2 = random.uniform(3000, 15000)
            inflow_3 = random.uniform(2000, 10000)

            total_inflow = inflow_1 + inflow_2 + inflow_3

            # Variable release
            release = random.uniform(10000, 30000)

            # Evaporation
            evap_rate_mm = 4.0

            # Set up inputs (indexed inflows)
            reservoir.inputs['inflow_1'] = inflow_1
            reservoir.inputs['inflow_2'] = inflow_2
            reservoir.inputs['inflow_3'] = inflow_3
            reservoir.inputs['release'] = release

            drivers = DriverRegistry()
            drivers.register('et', SimpleDriver(evap_rate_mm))

            # Track cumulative fluxes
            cumulative_inflow += total_inflow
            cumulative_release += release

            # Step reservoir
            outputs = reservoir.step(date, drivers)

            # Accumulate actual outflows
            cumulative_spill += outputs['spill']
            cumulative_evap += outputs['evaporation_loss']

        # Record final storage
        final_storage = reservoir.storage

        # Calculate mass balance
        delta_storage = final_storage - initial_storage
        total_outflow = cumulative_release + cumulative_spill + cumulative_evap

        balance_error = delta_storage - (cumulative_inflow - total_outflow)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (Multiple Inflows) ---")
        print(f"Initial storage: {initial_storage:,.0f} m³")
        print(f"Final storage: {final_storage:,.0f} m³")
        print(f"ΔS (storage change): {delta_storage:,.0f} m³")
        print(f"\nCumulative inflows (3 sources): {cumulative_inflow:,.0f} m³")
        print(f"Cumulative outflows: {total_outflow:,.0f} m³")
        print(f"  - Releases: {cumulative_release:,.0f} m³")
        print(f"  - Spillway: {cumulative_spill:,.0f} m³")
        print(f"  - Evaporation: {cumulative_evap:,.0f} m³")
        print(f"\nMass balance check: Initial + In - Out - Final = {balance_error:.6f} m³")

        # Assert mass balance closes
        assert abs(balance_error) < 1e-6, (
            f"Mass balance error {balance_error:.6f} m³ exceeds tolerance"
        )

    def test_mass_balance_long_term(self):
        """Test mass balance over extended period (1 year) with seasonal patterns."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=3000000.0,
            max_storage=5000000.0,
            surface_area=500000.0
        )

        # Record initial storage
        initial_storage = reservoir.storage

        # Track cumulative fluxes
        cumulative_inflow = 0.0
        cumulative_release = 0.0
        cumulative_spill = 0.0
        cumulative_evap = 0.0

        # Run full year simulation with seasonal patterns
        start_date = datetime(2020, 1, 1)
        for day in range(365):
            date = start_date + timedelta(days=day)
            doy = day + 1

            # Seasonal inflow pattern (higher in spring, lower in summer)
            base_inflow = 20000.0
            seasonal_factor = 1.5 + 0.5 * abs((doy - 182.5) / 182.5)  # Range: 1.5 to 2.0
            inflow = base_inflow * seasonal_factor

            # Seasonal release pattern (higher demand in summer)
            base_release = 15000.0
            seasonal_release_factor = 1.0 + 0.4 * (1 - abs((doy - 182.5) / 182.5))  # Range: 1.0 to 1.4
            release = base_release * seasonal_release_factor

            # Seasonal evaporation (higher in summer)
            evap_rate_mm = 2.0 + 4.0 * (1 - abs((doy - 182.5) / 182.5))  # Range: 2-6 mm/day

            # Set up inputs and drivers
            reservoir.inputs['inflow'] = inflow
            reservoir.inputs['release'] = release

            drivers = DriverRegistry()
            drivers.register('et', SimpleDriver(evap_rate_mm))

            # Track cumulative fluxes
            cumulative_inflow += inflow
            cumulative_release += release

            # Step reservoir
            outputs = reservoir.step(date, drivers)

            # Accumulate actual outflows
            cumulative_spill += outputs['spill']
            cumulative_evap += outputs['evaporation_loss']

        # Record final storage
        final_storage = reservoir.storage

        # Calculate mass balance
        delta_storage = final_storage - initial_storage
        total_outflow = cumulative_release + cumulative_spill + cumulative_evap

        balance_error = delta_storage - (cumulative_inflow - total_outflow)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (1 Year) ---")
        print(f"Initial storage: {initial_storage:,.0f} m³ ({initial_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"Final storage: {final_storage:,.0f} m³ ({final_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"ΔS (storage change): {delta_storage:,.0f} m³")
        print(f"\nCumulative inflows: {cumulative_inflow:,.0f} m³")
        print(f"Cumulative outflows: {total_outflow:,.0f} m³")
        print(f"  - Releases: {cumulative_release:,.0f} m³ ({cumulative_release/total_outflow*100:.1f}%)")
        print(f"  - Spillway: {cumulative_spill:,.0f} m³ ({cumulative_spill/total_outflow*100:.1f}%)")
        print(f"  - Evaporation: {cumulative_evap:,.0f} m³ ({cumulative_evap/total_outflow*100:.1f}%)")
        print(f"\nWater budget partitioning:")
        print(f"  Releases/Inflow: {cumulative_release/cumulative_inflow*100:.1f}%")
        print(f"  Spill/Inflow: {cumulative_spill/cumulative_inflow*100:.1f}%")
        print(f"  Evap/Inflow: {cumulative_evap/cumulative_inflow*100:.1f}%")
        print(f"  Storage Change/Inflow: {delta_storage/cumulative_inflow*100:.1f}%")
        print(f"\nMass balance check: Initial + In - Out - Final = {balance_error:.6f} m³")

        # Assert mass balance closes
        assert abs(balance_error) < 1e-6, (
            f"Mass balance error {balance_error:.6f} m³ exceeds tolerance"
        )

    def test_mass_balance_extreme_drawdown(self):
        """Test mass balance during extreme drawdown (releases exceed inflows)."""
        reservoir = Reservoir(
            name='test_reservoir',
            initial_storage=4000000.0,  # Start with good storage
            max_storage=5000000.0,
            surface_area=500000.0
        )

        # Record initial storage
        initial_storage = reservoir.storage

        # Track cumulative fluxes
        cumulative_inflow = 0.0
        cumulative_release = 0.0
        cumulative_spill = 0.0
        cumulative_evap = 0.0

        # Simulate drought with low inflows and high demand
        start_date = datetime(2020, 7, 1)
        for day in range(60):
            date = start_date + timedelta(days=day)

            # Low inflow during drought
            inflow = 5000.0

            # High release demand
            release = 40000.0  # Exceeds inflow - will drain reservoir

            # High summer evaporation
            evap_rate_mm = 6.0

            # Set up inputs and drivers
            reservoir.inputs['inflow'] = inflow
            reservoir.inputs['release'] = release

            drivers = DriverRegistry()
            drivers.register('et', SimpleDriver(evap_rate_mm))

            # Track cumulative fluxes
            cumulative_inflow += inflow
            cumulative_release += release

            # Step reservoir
            outputs = reservoir.step(date, drivers)

            # Accumulate actual outflows (note: actual release may be less than requested)
            actual_outflow = outputs['outflow']
            cumulative_spill += outputs['spill']
            cumulative_evap += outputs['evaporation_loss']

        # Record final storage
        final_storage = reservoir.storage

        # Calculate mass balance
        delta_storage = final_storage - initial_storage
        total_outflow = cumulative_release + cumulative_spill + cumulative_evap

        balance_error = delta_storage - (cumulative_inflow - total_outflow)

        # Print diagnostic info
        print(f"\n--- Mass Balance Summary (Extreme Drawdown) ---")
        print(f"Initial storage: {initial_storage:,.0f} m³ ({initial_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"Final storage: {final_storage:,.0f} m³ ({final_storage/reservoir.max_storage*100:.1f}% full)")
        print(f"ΔS (storage change): {delta_storage:,.0f} m³")
        print(f"\nCumulative inflows: {cumulative_inflow:,.0f} m³")
        print(f"Cumulative outflows: {total_outflow:,.0f} m³")
        print(f"  - Releases: {cumulative_release:,.0f} m³")
        print(f"  - Spillway: {cumulative_spill:,.0f} m³")
        print(f"  - Evaporation: {cumulative_evap:,.0f} m³")
        print(f"\nDrawdown: {(initial_storage - final_storage):,.0f} m³ ({(initial_storage - final_storage)/initial_storage*100:.1f}%)")
        print(f"Mass balance check: Initial + In - Out - Final = {balance_error:.6f} m³")

        # Assert mass balance closes
        assert abs(balance_error) < 1e-6, (
            f"Mass balance error {balance_error:.6f} m³ exceeds tolerance"
        )

        # Verify significant drawdown occurred
        assert delta_storage < -500000, "Expected significant drawdown during drought"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
