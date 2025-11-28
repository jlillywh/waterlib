"""
Project scaffolding module for waterlib.

This module provides functionality to create new waterlib projects with proper
directory structure and starter files. The main entry point is the create_project()
function, which creates a complete project layout including:

- Standard directory structure (models/, data/, outputs/, config/)
- Sample model YAML configuration
- Example Python script demonstrating basic usage
- Default WGEN parameter CSV file
- README with project documentation

The scaffolding system validates inputs, handles errors gracefully, and cleans up
partial projects if any error occurs during creation.

Examples
--------
>>> import waterlib
>>> project_path = waterlib.create_project("my_water_model")
>>> print(f"Created project at: {project_path}")
Created project at: /home/user/my_water_model

>>> # Create in specific location without examples
>>> project_path = waterlib.create_project(
...     "test_model",
...     parent_dir="/projects",
...     include_examples=False
... )
"""

import logging
import platform
from pathlib import Path
from typing import Set

# Configure logging
logger = logging.getLogger(__name__)


# Template constants
README_TEMPLATE = """# {project_name}

A waterlib water resources modeling project.

## Project Structure

- `models/` - Model configuration files (YAML)
- `data/` - Input data files (CSV, etc.)
- `outputs/` - Simulation results and plots
- `config/` - Additional configuration files

## Getting Started

1. Review and modify the sample model: `models/baseline.yaml`
2. Run the sample script: `python run_model.py`
3. View results in the `outputs/` directory

## Model Configuration

The baseline model includes:
- Stochastic climate generation (WGEN)
- Simple catchment with Snow17 + AWBM
- Reservoir storage
- Municipal demand

Modify `models/baseline.yaml` to customize the model for your watershed.

## WGEN Parameters

The file `data/wgen_params.csv` contains monthly weather generator parameters.
These are example values for a temperate climate (latitude ~40°N).

**Important**: Adjust these parameters for your specific location:
- Obtain local precipitation statistics
- Calibrate to historical weather data
- Ensure beta values are in millimeters (mm)

See the CSV file header for detailed parameter descriptions.

## Documentation

- [waterlib Documentation](https://github.com/yourusername/waterlib)
- [YAML Schema Reference](https://github.com/yourusername/waterlib/blob/main/docs/YAML_SCHEMA.md)
- [Component Reference](https://github.com/yourusername/waterlib/blob/main/COMPONENTS.md)

## Next Steps

1. Customize catchment parameters for your watershed
2. Add additional components (pumps, diversions, etc.)
3. Configure climate drivers (stochastic or timeseries)
4. Run sensitivity analysis or scenario testing
"""

SAMPLE_MODEL_TEMPLATE = """name: "Baseline Water Supply Model"
description: "Simple catchment-reservoir-demand system"

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: wgen
    temperature:
      mode: wgen
    solar_radiation:
      mode: wgen
    et_method: hargreaves
    latitude: 40.5
    wgen_config:
      param_file: ../data/wgen_params.csv
      latitude: 40.5
      elevation_m: 500
      txmd: 18.5
      txmw: 15.3
      tn: 4.7
      atx: 15.1
      atn: 11.7
      cvtx: 0.01675
      acvtx: -0.00383
      cvtn: 0.01605
      acvtn: -0.00345
      dt_day: 200
      rs_mean: 12.9
      rs_amplitude: 10.2
      rs_cv: 0.3
      rs_wet_factor: 0.7
      min_rain_mm: 0.254
      seed: 42

components:
  catchment:
    type: Catchment
    area_km2: 100.0
    snow17_params:
      scf: 1.0
      mfmax: 1.5
      mfmin: 0.5
      uadj: 0.04
      si: 1000.0
      pxtemp: 1.0
      nmf: 0.15
      tipm: 0.1
      mbase: 1.0
      plwhc: 0.04
      daygm: 0.05
    awbm_params:
      c_vec: [0.134, 0.433, 0.433]
      a_vec: [0.279, 0.514, 0.207]
      kbase: 0.95
      ksurf: 0.35
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Catchment'

  reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    surface_area: 500000
    inflows:
      - catchment.runoff_m3d
    meta:
      x: 0.5
      y: 0.5
      color: '#4169E1'
      label: 'Reservoir'

  demand:
    type: Demand
    source: reservoir
    mode: municipal
    population: 50000
    per_capita_demand_lpd: 200
    meta:
      x: 0.5
      y: 0.2
      color: '#FF6347'
      label: 'City'
"""

SAMPLE_SCRIPT_TEMPLATE = '''"""
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

    print("\\nSimulation complete!")
    print(f"Simulated {results.num_timesteps} days")

    # Access component results from dataframe
    print("\\nReservoir storage statistics:")
    reservoir_storage = results.dataframe["reservoir.storage"]
    print(f"  Mean: {reservoir_storage.mean():.0f} m³")
    print(f"  Min:  {reservoir_storage.min():.0f} m³")
    print(f"  Max:  {reservoir_storage.max():.0f} m³")

    print("\\nCatchment runoff statistics:")
    runoff_mm = results.dataframe["catchment.runoff_mm"]
    print(f"  Total runoff: {runoff_mm.sum():.1f} mm")
    print(f"  Mean daily runoff: {runoff_mm.mean():.2f} mm")

    print("\\nDemand fulfillment:")
    demand = results.dataframe["demand.demand"]
    supplied = results.dataframe["demand.supplied"]
    fulfillment = (supplied.sum() / demand.sum()) * 100
    print(f"  Total demand: {demand.sum():.0f} m³")
    print(f"  Total supplied: {supplied.sum():.0f} m³")
    print(f"  Fulfillment: {fulfillment:.1f}%")

    # Save results (already saved by run_simulation)
    print(f"\\nResults saved to: {results.csv_path}")

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

    print("\\nDone!")

if __name__ == "__main__":
    main()
'''


def _get_invalid_chars() -> Set[str]:
    """
    Get platform-specific invalid filesystem characters.

    Returns
    -------
    Set[str]
        Set of characters that are invalid in filenames for the current platform
    """
    system = platform.system()

    if system == 'Windows':
        # Windows has more restrictive filename rules
        return set(r'<>:"/\|?*')
    else:
        # POSIX systems (Linux, macOS, etc.)
        # Only forward slash is universally invalid, but we also exclude
        # null byte and some other problematic characters
        return set('/\0')


def _validate_project_name(name: str) -> None:
    """
    Validate project name for filesystem compatibility.

    Checks that the project name:
    - Is not empty
    - Does not contain platform-specific invalid characters
    - Is not a reserved name (., .., etc.)

    Parameters
    ----------
    name : str
        The proposed project name

    Raises
    ------
    ValueError
        If the project name is invalid, with a descriptive message explaining
        which characters are invalid or what the issue is

    Examples
    --------
    >>> _validate_project_name("my_project")  # Valid - no error
    >>> _validate_project_name("my/project")  # Raises ValueError
    Traceback (most recent call last):
        ...
    ValueError: Project name 'my/project' contains invalid characters: /
    """
    if not name:
        raise ValueError("Project name cannot be empty")

    if not name.strip():
        raise ValueError("Project name cannot be only whitespace")

    # Check for reserved names
    if name in ('.', '..'):
        raise ValueError(f"Project name cannot be '{name}' (reserved name)")

    # Check for invalid characters
    invalid_chars = _get_invalid_chars()
    found_invalid = set(name) & invalid_chars

    if found_invalid:
        # Sort for consistent error messages
        invalid_list = ', '.join(sorted(found_invalid))
        raise ValueError(
            f"Project name '{name}' contains invalid characters: {invalid_list}"
        )

    logger.debug(f"Project name '{name}' validated successfully")


def _create_directory_structure(project_root: Path) -> None:
    """
    Create standard waterlib project directory structure.

    Creates the following subdirectories within the project root:
    - models/: For model configuration YAML files
    - data/: For input data files (CSV, etc.)
    - outputs/: For simulation results and plots
    - config/: For additional configuration files

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where subdirectories will be created

    Raises
    ------
    OSError
        If directory creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> project_path = Path("/tmp/my_project")
    >>> project_path.mkdir()
    >>> _create_directory_structure(project_path)
    >>> list(sorted(d.name for d in project_path.iterdir()))
    ['config', 'data', 'models', 'outputs']
    """
    subdirs = ['models', 'data', 'outputs', 'config']

    for subdir in subdirs:
        subdir_path = project_root / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {subdir_path}")

    logger.info(f"Created directory structure: {', '.join(subdirs)}")


def _cleanup_on_error(project_root: Path) -> None:
    """
    Remove partially created project directory on error.

    This function is called when an error occurs during project creation to ensure
    no partial or incomplete project directories remain in the filesystem. It safely
    removes the project directory and all its contents.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory to be removed

    Notes
    -----
    This function will not raise an error if the directory doesn't exist or if
    removal fails - it logs the issue and continues. This is intentional to avoid
    masking the original error that triggered the cleanup.

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     (project_path / "test.txt").write_text("test")
    ...     _cleanup_on_error(project_path)
    ...     project_path.exists()
    False
    """
    import shutil

    if project_root.exists():
        try:
            shutil.rmtree(project_root)
            logger.info(f"Cleaned up partial project: {project_root}")
        except Exception as e:
            # Log but don't raise - we don't want to mask the original error
            logger.warning(f"Failed to clean up {project_root}: {e}")
    else:
        logger.debug(f"No cleanup needed - {project_root} does not exist")



def _validate_parent_directory(parent_dir: Path) -> None:
    """
    Validate that the parent directory exists and is writable.

    Parameters
    ----------
    parent_dir : Path
        Path to the parent directory where the project will be created

    Raises
    ------
    FileNotFoundError
        If the parent directory does not exist
    PermissionError
        If the parent directory is not writable

    Examples
    --------
    >>> from pathlib import Path
    >>> _validate_parent_directory(Path.cwd())  # Current directory exists
    >>> _validate_parent_directory(Path("/nonexistent/path"))
    Traceback (most recent call last):
        ...
    FileNotFoundError: Parent directory does not exist: /nonexistent/path
    """
    if not parent_dir.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {parent_dir}")

    if not parent_dir.is_dir():
        raise NotADirectoryError(f"Parent path is not a directory: {parent_dir}")

    # Check if we can write to the parent directory
    # We do this by checking the access permissions
    if not parent_dir.stat().st_mode & 0o200:  # Check write permission
        raise PermissionError(
            f"Cannot create project in {parent_dir}: Permission denied"
        )

    logger.debug(f"Parent directory '{parent_dir}' validated successfully")


def _generate_readme(project_root: Path, project_name: str) -> None:
    """
    Generate README.md file with project documentation.

    Creates a README.md file in the project root with documentation about the
    project structure, getting started instructions, and links to waterlib
    documentation. The project name is interpolated into the template.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where README.md will be created
    project_name : str
        Name of the project to be included in the README

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     _generate_readme(project_path, "test_project")
    ...     readme_path = project_path / "README.md"
    ...     readme_path.exists()
    True
    """
    readme_path = project_root / "README.md"
    readme_content = README_TEMPLATE.format(project_name=project_name)

    readme_path.write_text(readme_content, encoding='utf-8')
    logger.debug(f"Generated README.md at {readme_path}")


def _generate_sample_model(project_root: Path) -> None:
    """
    Generate sample model YAML configuration file.

    Creates a baseline.yaml file in the models/ subdirectory with a complete
    example model configuration including catchment, reservoir, and demand
    components with stochastic climate generation.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where models/baseline.yaml will be created

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     (project_path / "models").mkdir()
    ...     _generate_sample_model(project_path)
    ...     model_path = project_path / "models" / "baseline.yaml"
    ...     model_path.exists()
    True
    """
    model_path = project_root / "models" / "baseline.yaml"

    model_path.write_text(SAMPLE_MODEL_TEMPLATE, encoding='utf-8')
    logger.debug(f"Generated sample model at {model_path}")


def _generate_sample_script(project_root: Path, project_name: str) -> None:
    """
    Generate sample Python script demonstrating basic usage.

    Creates a run_model.py file in the project root with a complete example
    script that loads a model, runs a simulation, and generates plots. The
    script includes error handling and demonstrates accessing results.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where run_model.py will be created
    project_name : str
        Name of the project (currently not used in template but kept for consistency)

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     _generate_sample_script(project_path, "test_project")
    ...     script_path = project_path / "run_model.py"
    ...     script_path.exists()
    True
    """
    script_path = project_root / "run_model.py"

    script_path.write_text(SAMPLE_SCRIPT_TEMPLATE, encoding='utf-8')
    logger.debug(f"Generated sample script at {script_path}")


# WGEN Parameters CSV Template
WGEN_PARAMS_TEMPLATE = """# WGEN Monthly Parameter Template
# This file contains monthly precipitation parameters for the WGEN weather generator
#
# NEW INTERFACE STRUCTURE:
# - Monthly precipitation parameters: PWW, PWD, ALPHA, BETA (12 values each, one per month)
# - Constant temperature/radiation parameters: Specified in YAML configuration
# - Latitude: Specified in YAML configuration for Fourier-based seasonal calculations
#
# IMPORTANT UNIT CONVERSIONS:
# - BETA values MUST be in millimeters (mm), NOT inches
# - If converting from legacy US data: beta_mm = beta_inches × 25.4
# - Temperature parameters in YAML should be in Celsius (°C)
# - Solar radiation should be in MJ/m²/day
#
# PARAMETER DESCRIPTIONS:
# - Month: Month number (1-12)
# - PWW: Probability of wet day following a wet day [0-1]
# - PWD: Probability of wet day following a dry day [0-1]
# - ALPHA: Gamma distribution shape parameter (dimensionless, > 0)
# - BETA: Gamma distribution scale parameter (mm, > 0)
#
# VALIDATION CHECKLIST:
# ✓ BETA values are 3-25 mm for typical climates (not 0.2-1.0 which indicates unconverted inches)
# ✓ Mean precipitation per wet day (ALPHA × BETA) is 3-20 mm for most climates
# ✓ Probabilities (PWW, PWD) are between 0 and 1
# ✓ File has exactly 12 rows (one per month)
#
# EXAMPLE VALUES BELOW:
# These parameters represent a temperate climate station (latitude ~40°N)
# Mean annual precipitation: ~800 mm
# Values are already converted to SI units (mm)
#
Month,PWW,PWD,ALPHA,BETA
1,0.493,0.248,0.860,3.865
2,0.454,0.252,0.897,3.956
3,0.461,0.248,0.945,4.828
4,0.541,0.228,0.834,6.446
5,0.535,0.180,0.830,6.170
6,0.470,0.112,0.760,5.743
7,0.363,0.105,0.691,5.648
8,0.351,0.135,0.720,5.035
9,0.432,0.130,0.677,7.387
10,0.505,0.128,0.836,6.190
11,0.474,0.191,0.817,5.116
12,0.480,0.237,0.849,4.253
"""


# Data Directory README Template
DATA_README_TEMPLATE = """# Data Directory

This directory contains input data files for your waterlib models.

## Files

### wgen_params.csv

Monthly parameters for the WGEN stochastic weather generator. These parameters define the statistical properties of generated climate data including:

- Precipitation occurrence (wet/dry day transitions)
- Precipitation amounts on wet days
- Temperature ranges and variability
- Solar radiation patterns

**Important**: These are example values for a temperate climate (latitude ~40°N). You should calibrate these parameters to your specific location using historical weather data.

See the [WGEN Parameters Guide](../waterlib/templates/WGEN_PARAMETERS_GUIDE.md) for details on parameter estimation.

### climate_timeseries.csv

Example historical climate data showing the required format for timeseries mode. This file contains one year of daily data with:

- `date`: Date in YYYY-MM-DD format
- `precip_mm`: Daily precipitation (mm)
- `tmin_c`: Minimum temperature (°C)
- `tmax_c`: Maximum temperature (°C)
- `et_mm`: Reference evapotranspiration (mm/day) - optional

To use your own climate data:

1. Format your data to match this structure
2. Ensure dates cover your full simulation period
3. Update the model YAML to reference your file:

```yaml
settings:
  climate:
    precipitation:
      mode: timeseries
      file: ../data/your_precip_data.csv
      column: precip_mm
    temperature:
      mode: timeseries
      file: ../data/your_temp_data.csv
      tmin_column: tmin_c
      tmax_column: tmax_c
```

## Adding Your Own Data

You can add additional data files to this directory:

- Reservoir elevation-area-volume curves
- Demand time series
- Observed streamflow for calibration
- Soil parameter datasets
- Land use classifications

Reference these files in your model YAML using relative paths like `../data/your_file.csv`.

## Data Sources

Common sources for climate data:

- **NOAA Climate Data Online**: https://www.ncdc.noaa.gov/cdo-web/
- **PRISM Climate Group**: https://prism.oregonstate.edu/
- **Daymet**: https://daymet.ornl.gov/
- **GridMET**: https://www.climatologylab.org/gridmet.html
- **Local weather stations**: Contact your regional climate center

## Best Practices

1. **Document your data sources** - Add comments or a separate file noting where data came from
2. **Check data quality** - Look for missing values, outliers, and inconsistencies
3. **Use consistent units** - waterlib expects mm for precipitation, °C for temperature
4. **Version control** - Track data files in git if they're small (<10 MB)
5. **Backup large datasets** - Store large files outside the repository
"""


def _generate_climate_timeseries_data() -> str:
    """
    Generate example climate timeseries data for one year (365 days).

    Creates realistic seasonal patterns with:
    - Winter: lower temps, moderate precip
    - Spring: warming temps, increasing precip
    - Summer: high temps, lower precip, high ET
    - Fall: cooling temps, increasing precip

    Returns
    -------
    str
        CSV content with date, precip_mm, tmin_c, tmax_c, et_mm columns
    """
    import math

    lines = ["date,precip_mm,tmin_c,tmax_c,et_mm"]

    # Generate 365 days of data for 2020
    for day in range(1, 366):
        # Calculate date
        # Simple day-of-year to date conversion for 2020 (leap year)
        month_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        cumulative = 0
        month = 1
        for m, days_in_month in enumerate(month_days, 1):
            if day <= cumulative + days_in_month:
                month = m
                day_of_month = day - cumulative
                break
            cumulative += days_in_month

        date_str = f"2020-{month:02d}-{day_of_month:02d}"

        # Seasonal temperature pattern (sinusoidal)
        # Peak in summer (day 180), trough in winter (day 0/365)
        day_angle = 2 * math.pi * (day - 15) / 365  # Offset by 15 days for realistic lag

        # Temperature ranges
        tmax_mean = 17.5 + 12.5 * math.sin(day_angle)  # Range: 5°C to 30°C
        tmin_mean = 7.5 + 7.5 * math.sin(day_angle)    # Range: 0°C to 15°C

        # Add some daily variation (simplified - not truly random but varied)
        tmax_var = 3 * math.sin(day * 0.7)
        tmin_var = 2 * math.sin(day * 0.5)

        tmax = round(tmax_mean + tmax_var, 1)
        tmin = round(tmin_mean + tmin_var, 1)

        # Precipitation pattern (more in spring/fall, less in summer)
        # Use a different phase to create realistic wet/dry periods
        precip_base = 5 + 3 * math.sin(day_angle + math.pi/2)

        # Create clustered wet days (simplified pattern)
        # Use modulo to create periodic wet spells
        if (day % 7) < 3:  # Wet period
            precip = round(precip_base * (1 + 0.5 * math.sin(day * 0.3)), 1)
        else:  # Dry period
            precip = 0.0 if (day % 7) > 4 else round(precip_base * 0.3, 1)

        # ET follows temperature (higher in summer)
        et_base = 1.5 + 2.5 * math.sin(day_angle)  # Range: ~0 to 4 mm/day
        et = round(max(0.5, et_base + 0.5 * math.sin(day * 0.4)), 1)

        lines.append(f"{date_str},{precip},{tmin},{tmax},{et}")

    return "\n".join(lines)


def _generate_wgen_params(project_root: Path) -> None:
    """
    Generate default WGEN parameters CSV file in data directory.

    Creates a wgen_params.csv file in the data/ subdirectory with monthly
    weather generator parameters for a temperate climate. These are example
    values that users should calibrate to their specific location.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where data/wgen_params.csv will be created

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     (project_path / "data").mkdir()
    ...     _generate_wgen_params(project_path)
    ...     wgen_path = project_path / "data" / "wgen_params.csv"
    ...     wgen_path.exists()
    True
    """
    wgen_path = project_root / "data" / "wgen_params.csv"

    wgen_path.write_text(WGEN_PARAMS_TEMPLATE, encoding='utf-8')
    logger.debug(f"Generated WGEN parameters at {wgen_path}")


def _generate_climate_timeseries(project_root: Path) -> None:
    """
    Generate example climate timeseries CSV file in data directory.

    Creates a climate_timeseries.csv file in the data/ subdirectory with one
    year (365 days) of example daily climate data showing realistic seasonal
    patterns. This demonstrates the required format for users who want to use
    historical climate data instead of stochastic generation.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where data/climate_timeseries.csv will be created

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     (project_path / "data").mkdir()
    ...     _generate_climate_timeseries(project_path)
    ...     climate_path = project_path / "data" / "climate_timeseries.csv"
    ...     climate_path.exists()
    True
    """
    climate_path = project_root / "data" / "climate_timeseries.csv"

    # Generate the climate data
    climate_data = _generate_climate_timeseries_data()

    climate_path.write_text(climate_data, encoding='utf-8')
    logger.debug(f"Generated climate timeseries at {climate_path}")


def _generate_data_readme(project_root: Path) -> None:
    """
    Generate README.md file in data directory explaining data files.

    Creates a README.md file in the data/ subdirectory with documentation
    about the data files, their formats, how to use them, and best practices
    for managing input data.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory where data/README.md will be created

    Raises
    ------
    OSError
        If file creation fails due to permissions or other filesystem issues

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     project_path = Path(tmpdir) / "test_project"
    ...     project_path.mkdir()
    ...     (project_path / "data").mkdir()
    ...     _generate_data_readme(project_path)
    ...     readme_path = project_path / "data" / "README.md"
    ...     readme_path.exists()
    True
    """
    readme_path = project_root / "data" / "README.md"

    readme_path.write_text(DATA_README_TEMPLATE, encoding='utf-8')
    logger.debug(f"Generated data README at {readme_path}")


def create_project(
    name: str,
    parent_dir: str = ".",
    include_examples: bool = True,
    overwrite: bool = False
) -> Path:
    """
    Create a new waterlib project with directory structure and starter files.

    This function creates a complete waterlib project with:
    - Standard directory structure (models/, data/, outputs/, config/)
    - Sample model YAML configuration (if include_examples=True)
    - Example Python script demonstrating basic usage (if include_examples=True)
    - Default WGEN parameter CSV file (if include_examples=True)
    - Example climate timeseries data (if include_examples=True)
    - README with project documentation (if include_examples=True)

    The function validates all inputs, handles errors gracefully, and cleans up
    partial projects if any error occurs during creation.

    Parameters
    ----------
    name : str
        Project name (will be used as directory name). Must not contain
        filesystem-invalid characters like /, \\, :, *, ?, ", <, >, |
    parent_dir : str, optional
        Parent directory where project will be created. Defaults to current
        directory ("."). The parent directory must exist and be writable.
    include_examples : bool, optional
        Whether to include example files (README, sample model, sample script,
        data files). If False, only creates the directory structure. Default is True.
    overwrite : bool, optional
        Whether to overwrite existing project directory. If False and the project
        directory already exists, raises FileExistsError. Default is False.

    Returns
    -------
    Path
        Absolute path to the created project root directory

    Raises
    ------
    ValueError
        If project name is empty, contains only whitespace, or contains invalid
        filesystem characters
    FileExistsError
        If project directory already exists and overwrite=False
    FileNotFoundError
        If parent directory does not exist
    PermissionError
        If lacking write permissions in parent directory
    OSError
        If directory or file creation fails for other reasons

    Examples
    --------
    Create a project with all defaults (includes examples):

    >>> import waterlib
    >>> project_path = waterlib.create_project("my_water_model")
    >>> print(f"Created project at: {project_path}")
    Created project at: /home/user/my_water_model

    Create a project in a specific location without examples:

    >>> project_path = waterlib.create_project(
    ...     "test_model",
    ...     parent_dir="/projects",
    ...     include_examples=False
    ... )
    >>> print(f"Created minimal project at: {project_path}")
    Created minimal project at: /projects/test_model

    Create a project with overwrite enabled:

    >>> project_path = waterlib.create_project(
    ...     "existing_project",
    ...     overwrite=True
    ... )

    Notes
    -----
    - The function logs all operations using Python's logging module
    - If any error occurs, partially created directories are cleaned up
    - All file paths use pathlib.Path for cross-platform compatibility
    - Generated files use UTF-8 encoding

    See Also
    --------
    waterlib.load_model : Load a model from YAML configuration
    waterlib.run_simulation : Run a simulation with a loaded model
    """
    # Validate inputs
    _validate_project_name(name)

    # Convert parent_dir to Path and resolve to absolute path
    parent_path = Path(parent_dir).resolve()
    _validate_parent_directory(parent_path)

    # Construct project root path
    project_root = parent_path / name

    # Check if project already exists
    if project_root.exists():
        if not overwrite:
            raise FileExistsError(
                f"Project directory already exists: {project_root}. "
                f"Use overwrite=True to replace it."
            )
        else:
            # Remove existing project
            import shutil
            logger.info(f"Removing existing project at {project_root}")
            shutil.rmtree(project_root)

    # Log the operation
    logger.info(f"Creating project '{name}' in {parent_path}")

    try:
        # Create project root directory
        project_root.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created project root: {project_root}")

        # Create directory structure
        _create_directory_structure(project_root)

        # Generate starter files if requested
        if include_examples:
            logger.info("Generating starter files...")

            # Generate project-level files
            _generate_readme(project_root, name)
            _generate_sample_model(project_root)
            _generate_sample_script(project_root, name)

            # Generate data files
            _generate_wgen_params(project_root)
            _generate_climate_timeseries(project_root)
            _generate_data_readme(project_root)

            logger.info("Generated all starter files")
        else:
            logger.info("Skipped starter files (include_examples=False)")

        # Log success
        logger.info(f"Successfully created project at: {project_root}")

        # Return absolute path
        return project_root.resolve()

    except Exception as e:
        # Clean up on error
        logger.error(f"Error creating project '{name}': {e}")
        _cleanup_on_error(project_root)

        # Re-raise with enhanced error message
        error_msg = f"Failed to create project '{name}' at {project_root}: {e}"

        # Preserve the original exception type when possible
        if isinstance(e, (ValueError, FileExistsError, FileNotFoundError, PermissionError)):
            raise type(e)(error_msg) from e
        else:
            raise OSError(error_msg) from e
