# test_logging

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
