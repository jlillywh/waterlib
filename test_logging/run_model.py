"""
Sample waterlib model execution script

This script demonstrates how to:
1. Load a model from YAML
2. Run a simulation
3. Access and plot results
"""

import waterlib
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent
MODEL_FILE = PROJECT_ROOT / "models" / "baseline.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    print("Loading model...")
    model = waterlib.load_model(MODEL_FILE)

    print("Running simulation...")
    results = waterlib.run_simulation(model, output_dir=OUTPUT_DIR)

    print("\nSimulation complete!")
    print(f"Simulated {results.num_timesteps} days")

    # Access component results from dataframe
    print("\nReservoir storage statistics:")
    reservoir_storage = results.dataframe["reservoir.storage"]
    print(f"  Mean: {reservoir_storage.mean():.0f} m³")
    print(f"  Min:  {reservoir_storage.min():.0f} m³")
    print(f"  Max:  {reservoir_storage.max():.0f} m³")

    print("\nCatchment runoff statistics:")
    runoff_mm = results.dataframe["catchment.runoff_mm"]
    print(f"  Total runoff: {runoff_mm.sum():.1f} mm")
    print(f"  Mean daily runoff: {runoff_mm.mean():.2f} mm")

    print("\nDemand fulfillment:")
    demand = results.dataframe["demand.demand"]
    supplied = results.dataframe["demand.supplied"]
    fulfillment = (supplied.sum() / demand.sum()) * 100
    print(f"  Total demand: {demand.sum():.0f} m³")
    print(f"  Total supplied: {supplied.sum():.0f} m³")
    print(f"  Fulfillment: {fulfillment:.1f}%")

    # Save results (already saved by run_simulation)
    print(f"\nResults saved to: {results.csv_path}")

    # Plot results (if matplotlib available)
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Get dates from dataframe index
        dates = results.dataframe.index

        # Plot catchment runoff
        runoff = results.dataframe["catchment.runoff"]
        runoff_mm = results.dataframe["catchment.runoff_mm"]
        axes[0].bar(dates, runoff_mm, label="Runoff (mm)", alpha=0.7, color='steelblue')
        axes[0].set_ylabel("Runoff (mm/day)")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        axes[0].set_title("Catchment Runoff")

        # Plot reservoir storage
        axes[1].plot(dates, reservoir_storage / 1e6, color='royalblue')
        axes[1].set_ylabel("Storage (million m³)")
        axes[1].grid(True, alpha=0.3)
        axes[1].set_title("Reservoir Storage")

        # Plot demand satisfaction
        demand_requested = results.dataframe["demand.demand"]
        demand_supplied = results.dataframe["demand.supplied"]
        axes[2].plot(dates, demand_requested, label="Requested", linestyle='--')
        axes[2].plot(dates, demand_supplied, label="Supplied")
        axes[2].set_ylabel("Demand (m³/day)")
        axes[2].set_xlabel("Date")
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        axes[2].set_title("Municipal Demand")

        plt.tight_layout()
        plot_path = OUTPUT_DIR / "simulation_plots.png"
        plt.savefig(plot_path, dpi=300)
        print(f"Plots saved to: {plot_path}")

    except ImportError:
        print("Matplotlib not available - skipping plots")

    print("\nDone!")

if __name__ == "__main__":
    main()
