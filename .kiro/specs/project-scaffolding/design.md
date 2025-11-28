# Design Document: Project Scaffolding

## Overview

The project scaffolding feature provides a programmatic way to create new waterlib projects with proper directory structure and starter files. The feature is implemented as a Python API function `create_project()` that can be called from scripts or notebooks, following waterlib's library-first philosophy.

The scaffolding system creates a complete project structure including:
- Standard directory layout (models/, data/, outputs/, config/)
- Sample model YAML configuration
- Example Python script demonstrating basic usage
- Default WGEN parameter CSV file
- README with project documentation

This eliminates manual setup errors and provides users with working examples they can immediately run and modify.

## Architecture

### Module Structure

```
waterlib/
├── core/
│   ├── scaffold.py          # New module for scaffolding
│   └── __init__.py           # Export scaffold functions
└── __init__.py               # Expose create_project at top level
```

### Design Principles

1. **Library-First**: Implemented as a Python function, not a CLI tool
2. **Fail-Safe**: Validates inputs and cleans up on errors
3. **Flexible**: Supports custom parent directories and optional starter files
4. **Self-Documenting**: Generated files include comments and documentation
5. **Minimal Dependencies**: Uses only Python standard library (pathlib, shutil)

## Components and Interfaces

### Main Function: `create_project()`

```python
def create_project(
    name: str,
    parent_dir: str = ".",
    include_examples: bool = True,
    overwrite: bool = False
) -> Path:
    """
    Create a new waterlib project with directory structure and starter files.

    Parameters
    ----------
    name : str
        Project name (will be used as directory name)
    parent_dir : str, optional
        Parent directory where project will be created (default: current directory)
    include_examples : bool, optional
        Whether to include example files (default: True)
    overwrite : bool, optional
        Whether to overwrite existing project directory (default: False)

    Returns
    -------
    Path
        Absolute path to the created project root directory

    Raises
    ------
    ValueError
        If project name contains invalid filesystem characters
    FileExistsError
        If project directory already exists and overwrite=False
    FileNotFoundError
        If parent directory does not exist
    PermissionError
        If lacking write permissions in parent directory

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
```

### Helper Functions

```python
def _validate_project_name(name: str) -> None:
    """Validate project name for filesystem compatibility."""

def _create_directory_structure(project_root: Path) -> None:
    """Create standard directory layout."""

def _generate_readme(project_root: Path, project_name: str) -> None:
    """Generate README.md with project documentation."""

def _generate_sample_model(project_root: Path) -> None:
    """Generate sample model.yaml configuration."""

def _generate_sample_script(project_root: Path, project_name: str) -> None:
    """Generate sample Python script."""

def _generate_wgen_params(project_root: Path) -> None:
    """Generate default wgen_params.csv in data directory."""

def _generate_climate_timeseries(project_root: Path) -> None:
    """Generate example climate timeseries CSV in data directory."""

def _generate_data_readme(project_root: Path) -> None:
    """Generate README.md in data directory explaining data files."""

def _cleanup_on_error(project_root: Path) -> None:
    """Remove partially created project on error."""
```

## Data Models

### Directory Structure

```
project_name/
├── README.md                 # Project documentation
├── models/
│   └── baseline.yaml         # Sample model configuration
├── data/
│   ├── wgen_params.csv       # Default WGEN parameters
│   ├── climate_timeseries.csv # Example climate timeseries data
│   └── README.md             # Data directory documentation
├── outputs/                  # Empty directory for results
├── config/                   # Empty directory for additional configs
└── run_model.py              # Sample Python script
```

### File Templates

#### README.md Template

```markdown
# {project_name}

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
```

#### Sample Model YAML Template

```yaml
name: "Baseline Water Supply Model"
description: "Simple catchment-reservoir-demand system"

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: stochastic
      seed: 42
      file: ../data/wgen_params.csv
    temperature:
      mode: stochastic
      seed: 42
      params:
        mean_tmin: 5
        mean_tmax: 20
        amplitude_tmin: 10
        amplitude_tmax: 10
        std_tmin: 3
        std_tmax: 3
    et_method: hargreaves
    latitude: 40.5

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
      c1: 0.134
      c2: 0.433
      c3: 0.433
      a1: 0.279
      a2: 0.514
      a3: 0.207
      kbase: 0.95
      ksurf: 0.35
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Catchment'

  reservoir:
    type: Reservoir
    initial_storage_m3: 2000000
    max_storage_m3: 5000000
    surface_area_m2: 500000
    spillway_elevation_m: 245.0
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
```

#### Sample Python Script Template

```python
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
    results = waterlib.run_simulation(model, progress=True)

    print("\\nSimulation complete!")
    print(f"Simulated {len(results.dates)} days")

    # Access component results
    print("\\nReservoir storage statistics:")
    reservoir_storage = results.get_component_data("reservoir", "storage_m3")
    print(f"  Mean: {reservoir_storage.mean():.0f} m³")
    print(f"  Min:  {reservoir_storage.min():.0f} m³")
    print(f"  Max:  {reservoir_storage.max():.0f} m³")

    # Save results
    print("\\nSaving results...")
    results.to_csv(OUTPUT_DIR / "simulation_results.csv")

    # Plot results (if matplotlib available)
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Plot precipitation and runoff
        precip = results.get_climate_data("precipitation_mm")
        runoff = results.get_component_data("catchment", "runoff_m3d")
        axes[0].bar(results.dates, precip, label="Precipitation", alpha=0.7)
        axes[0].set_ylabel("Precipitation (mm)")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        ax_runoff = axes[0].twinx()
        ax_runoff.plot(results.dates, runoff, color='blue', label="Runoff")
        ax_runoff.set_ylabel("Runoff (m³/day)")
        ax_runoff.legend(loc='upper right')

        # Plot reservoir storage
        axes[1].plot(results.dates, reservoir_storage / 1e6, color='royalblue')
        axes[1].set_ylabel("Storage (million m³)")
        axes[1].grid(True, alpha=0.3)
        axes[1].set_title("Reservoir Storage")

        # Plot demand satisfaction
        demand_requested = results.get_component_data("demand", "demand_m3d")
        demand_supplied = results.get_component_data("demand", "supplied_m3d")
        axes[2].plot(results.dates, demand_requested, label="Requested", linestyle='--')
        axes[2].plot(results.dates, demand_supplied, label="Supplied")
        axes[2].set_ylabel("Demand (m³/day)")
        axes[2].set_xlabel("Date")
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        axes[2].set_title("Municipal Demand")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "simulation_plots.png", dpi=300)
        print(f"Plots saved to: {OUTPUT_DIR / 'simulation_plots.png'}")

    except ImportError:
        print("Matplotlib not available - skipping plots")

    print("\\nDone!")

if __name__ == "__main__":
    main()
```

#### WGEN Parameters CSV Template

```csv
# WGEN Monthly Weather Generator Parameters
# These are example values for a temperate climate (latitude ~40°N)
# Adjust these parameters for your specific location
#
# Column descriptions:
# - month: Month number (1-12)
# - p_wet_wet: Probability of wet day following wet day (0-1)
# - p_wet_dry: Probability of wet day following dry day (0-1)
# - precip_mean: Mean precipitation on wet days (mm)
# - precip_std: Standard deviation of precipitation (mm)
# - tmax_mean: Mean maximum temperature (°C)
# - tmax_std: Standard deviation of max temperature (°C)
# - tmin_mean: Mean minimum temperature (°C)
# - tmin_std: Standard deviation of min temperature (°C)
# - solar_mean: Mean solar radiation (MJ/m²/day)
# - solar_std: Standard deviation of solar radiation (MJ/m²/day)
month,p_wet_wet,p_wet_dry,precip_mean,precip_std,tmax_mean,tmax_std,tmin_mean,tmin_std,solar_mean,solar_std
1,0.60,0.25,8.5,6.2,5.0,3.5,-2.0,2.8,8.0,2.5
2,0.58,0.28,9.2,6.8,7.5,3.8,0.0,3.0,11.0,3.0
3,0.55,0.30,10.5,7.5,12.0,4.2,3.0,3.2,15.0,3.5
4,0.52,0.32,11.8,8.2,17.0,4.5,7.0,3.5,19.0,4.0
5,0.48,0.28,12.5,9.0,22.0,4.8,11.0,3.8,23.0,4.5
6,0.45,0.25,10.2,7.8,27.0,5.0,15.0,4.0,25.0,4.8
7,0.42,0.22,8.5,6.5,30.0,5.2,18.0,4.2,24.0,4.5
8,0.44,0.24,9.0,7.0,29.0,5.0,17.0,4.0,21.0,4.2
9,0.48,0.26,10.5,7.5,24.0,4.8,13.0,3.8,17.0,3.8
10,0.52,0.30,11.2,8.0,18.0,4.5,8.0,3.5,13.0,3.2
11,0.56,0.32,10.0,7.2,11.0,4.0,3.0,3.2,9.0,2.8
12,0.62,0.28,9.0,6.5,6.0,3.5,0.0,2.8,7.0,2.5
```

#### Climate Timeseries CSV Template

Example timeseries data for one year (365 days). This demonstrates the format for users who want to use historical climate data instead of stochastic generation.

```csv
date,precip_mm,tmin_c,tmax_c,et_mm
2020-01-01,2.5,1.2,6.8,1.2
2020-01-02,0.0,0.5,7.5,1.3
2020-01-03,5.8,-0.2,5.2,1.1
2020-01-04,12.3,-1.5,3.8,0.9
2020-01-05,8.5,0.8,6.5,1.0
# ... (continues for 365 days with realistic seasonal patterns)
# Data should show:
# - Seasonal temperature variation
# - Realistic precipitation patterns (clustered wet days)
# - ET following temperature patterns
# - Winter: lower temps, moderate precip
# - Spring: warming temps, increasing precip
# - Summer: high temps, lower precip, high ET
# - Fall: cooling temps, increasing precip
```

Note: The actual template will include all 365 days with realistic seasonal patterns.

#### Data Directory README Template

```markdown
# Data Directory

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
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Directory creation for valid names

*For any* valid project name, calling create_project should result in a directory with that name being created.

**Validates: Requirements 1.1**

### Property 2: Existing directory protection

*For any* project name where a directory already exists, calling create_project with overwrite=False should raise FileExistsError and leave the existing directory unchanged.

**Validates: Requirements 1.2**

### Property 3: Standard subdirectory structure

*For any* successful create_project execution, the created project should contain subdirectories named "models", "data", "outputs", and "config".

**Validates: Requirements 1.3**

### Property 4: Absolute path return value

*For any* successful create_project execution, the returned path should be absolute and point to the created project directory.

**Validates: Requirements 1.4**

### Property 5: Custom parent directory placement

*For any* valid parent directory and project name, calling create_project with parent_dir parameter should create the project as a subdirectory of the specified parent.

**Validates: Requirements 1.5**

### Property 6: README generation

*For any* successful create_project execution with include_examples=True, a README.md file should exist in the project root and contain non-empty content.

**Validates: Requirements 2.1**

### Property 7: Model configuration generation

*For any* successful create_project execution with include_examples=True, a YAML file should exist in the models directory and be parseable as valid YAML.

**Validates: Requirements 2.2**

### Property 8: Python script generation

*For any* successful create_project execution with include_examples=True, a Python script should exist in the project root and be syntactically valid Python code.

**Validates: Requirements 2.3**

### Property 9: WGEN parameters generation

*For any* successful create_project execution with include_examples=True, a wgen_params.csv file should exist in the data directory and contain 12 rows of valid parameter data.

**Validates: Requirements 2.4**

### Property 10: Climate timeseries generation

*For any* successful create_project execution with include_examples=True, a climate_timeseries.csv file should exist in the data directory and contain valid daily climate data with date, precipitation, temperature, and ET columns.

**Validates: Requirements 2.5**

### Property 11: Data directory README generation

*For any* successful create_project execution with include_examples=True, a README.md file should exist in the data directory explaining the data files and their usage.

**Validates: Requirements 2.5**

### Property 12: Generated file validity

*For any* successful create_project execution with include_examples=True, all generated files (YAML, Python, CSV) should be parseable by their respective parsers without errors.

**Validates: Requirements 2.6**

### Property 13: Minimal structure without examples

*For any* successful create_project execution with include_examples=False, only the directory structure should exist with no starter files in the project root or subdirectories.

**Validates: Requirements 2.7**

### Property 14: Invalid character rejection

*For any* project name containing filesystem-invalid characters (e.g., /, \, :, *, ?, ", <, >, |), calling create_project should raise ValueError with a message describing the invalid characters.

**Validates: Requirements 4.1**

### Property 15: Non-existent parent directory error

*For any* non-existent parent directory path, calling create_project should raise FileNotFoundError with a message containing the missing path.

**Validates: Requirements 4.2**

### Property 16: Cleanup on error

*For any* error that occurs during create_project execution, no partial project directory should remain in the filesystem after the error is raised.

**Validates: Requirements 4.4**

### Property 17: Error message completeness

*For any* error raised by create_project, the error message should contain both the project name and the attempted path.

**Validates: Requirements 4.5**

### Property 18: Function signature compliance

*For any* call to create_project, the function should accept a required name parameter and optional parent_dir and include_examples parameters.

**Validates: Requirements 3.2, 3.3, 3.4**

### Property 19: Docstring completeness

*For any* public function in the scaffold module, the function should have a docstring containing parameter descriptions and at least one example.

**Validates: Requirements 5.4**

## Error Handling

### Input Validation Errors

**Invalid Project Name**
- **Trigger**: Project name contains filesystem-invalid characters
- **Response**: Raise `ValueError` with message listing invalid characters
- **Example**: `ValueError: Project name 'my/project' contains invalid characters: /`

**Existing Directory**
- **Trigger**: Project directory already exists and overwrite=False
- **Response**: Raise `FileExistsError` with path to existing directory
- **Example**: `FileExistsError: Project directory already exists: /home/user/my_project`

**Non-Existent Parent**
- **Trigger**: Specified parent_dir does not exist
- **Response**: Raise `FileNotFoundError` with missing path
- **Example**: `FileNotFoundError: Parent directory does not exist: /nonexistent/path`

**Permission Denied**
- **Trigger**: Insufficient write permissions in parent directory
- **Response**: Raise `PermissionError` with clear explanation
- **Example**: `PermissionError: Cannot create project in /protected/path: Permission denied`

### Runtime Errors

**File Creation Failure**
- **Trigger**: Error writing starter files (disk full, I/O error)
- **Response**: Clean up partial project and raise original exception
- **Cleanup**: Remove project directory and all created subdirectories

**Template Copy Failure**
- **Trigger**: Cannot locate or read wgen_params template
- **Response**: Raise `FileNotFoundError` with template path
- **Example**: `FileNotFoundError: Cannot find WGEN template: waterlib/templates/wgen_params_template.csv`

### Error Recovery

All errors follow this pattern:
1. Detect error condition
2. Log error details
3. Clean up any partially created directories/files
4. Raise appropriate exception with descriptive message

The cleanup function `_cleanup_on_error()` ensures no partial projects remain:
```python
def _cleanup_on_error(project_root: Path) -> None:
    """Remove partially created project directory."""
    if project_root.exists():
        shutil.rmtree(project_root)
        logger.info(f"Cleaned up partial project: {project_root}")
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases:

**Input Validation Tests**
- Test valid project names (alphanumeric, underscores, hyphens)
- Test invalid project names (special characters, empty strings)
- Test various parent directory specifications
- Test boolean flag combinations

**Directory Creation Tests**
- Test standard directory structure creation
- Test creation in custom parent directories
- Test handling of existing directories
- Test cleanup on errors

**File Generation Tests**
- Test README content includes project name
- Test YAML file is valid and loadable
- Test Python script is syntactically valid
- Test WGEN CSV has correct structure (12 monthly rows)
- Test climate timeseries CSV has correct structure (365 daily rows with required columns)
- Test data directory README exists and contains documentation
- Test file generation can be disabled

**Error Handling Tests**
- Test ValueError for invalid names
- Test FileExistsError for existing directories
- Test FileNotFoundError for missing parents
- Test cleanup removes partial directories

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using the Hypothesis library:

**Property Tests**
- Generate random valid project names and verify directory creation
- Generate random invalid names and verify ValueError
- Generate random parent directories and verify correct placement
- Verify all required subdirectories exist for any valid input
- Verify cleanup occurs for any error condition
- Verify return value is always absolute path
- Verify generated files are always valid for their format

**Test Configuration**
- Minimum 100 iterations per property test
- Use temporary directories for all tests
- Clean up test projects after each test
- Use Hypothesis strategies for generating valid/invalid names

### Integration Testing

Integration tests will verify end-to-end workflows:

**Complete Workflow Test**
- Create project with all defaults
- Verify all files and directories exist
- Load and validate the generated YAML
- Execute the generated Python script
- Verify script runs without errors

**Custom Configuration Test**
- Create project with custom parent directory
- Create project without examples
- Verify correct behavior for each configuration

**Error Recovery Test**
- Simulate various error conditions
- Verify cleanup occurs correctly
- Verify no partial projects remain

### Test Organization

```
tests/
├── unit/
│   ├── test_scaffold_validation.py    # Input validation tests
│   ├── test_scaffold_creation.py      # Directory/file creation tests
│   └── test_scaffold_errors.py        # Error handling tests
└── property/
    └── test_scaffold_properties.py    # Property-based tests
```

### Testing Dependencies

- **pytest**: Test framework
- **hypothesis**: Property-based testing library
- **pytest-tmp-path**: Temporary directory fixtures
- **pyyaml**: YAML validation in tests

## Implementation Notes

### Platform Compatibility

The implementation must work across Windows, macOS, and Linux:
- Use `pathlib.Path` for all path operations (cross-platform)
- Use `Path.mkdir(parents=True, exist_ok=True)` for directory creation
- Validate project names against platform-specific invalid characters
- Use forward slashes in templates (pathlib handles conversion)

### Invalid Characters by Platform

```python
INVALID_CHARS = {
    'windows': r'<>:"/\|?*',
    'posix': '/',
}
```

### Template Storage

Templates are stored as string constants in the module for simplicity:
- No external template files to manage
- Templates are part of the installed package
- Easy to version control and modify
- All data files (WGEN params, climate timeseries, data README) are generated from constants
- Climate timeseries includes 365 days of realistic seasonal data

### Logging

The module uses Python's logging module:
```python
import logging
logger = logging.getLogger(__name__)

# Log key operations
logger.info(f"Creating project '{name}' in {parent_dir}")
logger.info(f"Created directory structure: {subdirs}")
logger.info(f"Generated starter files: {files}")
```

### Future Enhancements

Potential future additions (not in current scope):
- CLI wrapper for command-line usage
- Custom templates support
- Interactive project setup wizard
- Git repository initialization
- Virtual environment creation
- Additional example models (multi-catchment, irrigation, etc.)
