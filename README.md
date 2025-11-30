# waterlib

A Python library for building and simulating water resources models using YAML configuration files.

## Overview

waterlib enables water resources consultants to rapidly build, run, and visualize daily timestep water system models. Define your model in a YAML file, run it with one function call, and get results.

### Architecture

- **Kernels** (`waterlib/kernels/`) - Pure computational algorithms (Snow17, AWBM, weir equations, ET)
- **Components** (`waterlib/components/`) - Graph nodes that orchestrate kernels
- **Drivers** (`waterlib/core/drivers.py`) - Global climate data providers
- **Clear separation** - Kernels are reusable algorithms; components handle integration

### Core Philosophy

1. **Single YAML configuration**: Define your entire model in one file
2. **One-function execution**: Run simulations with `run_simulation(model)`
3. **Built-in climate utilities**: Precipitation, temperature, and ET available globally
4. **Integrated visualization**: Network diagrams and time series plots with minimal code

## Key Features

- **Library-first workflow**: Run models in Jupyter notebooks or scripts
- **Single-file configuration**: YAML contains model structure and simulation settings
- **Global climate utilities**: Stochastic weather generation and ET built-in
- **Integrated components**: Catchment includes Snow17+AWBM, Reservoir includes spillway
- **Publication-quality plotting**: Time series plots with dual-axis support
- **Comprehensive error handling**: Clear, actionable error messages

## Installation

```bash
pip install waterlib
```

For development:

```bash
git clone https://github.com/yourusername/waterlib.git
cd waterlib
pip install -e ".[dev]"
```

For visualization and plotting support:

```bash
pip install waterlib[viz]
# or for development with visualization:
pip install -e ".[dev,viz]"
```

**Requirements:**
- Python 3.8 or higher
- pyyaml >= 6.0
- networkx >= 2.8
- pandas >= 1.5
- numpy >= 1.23

**Optional:**
- matplotlib >= 3.5 (for model visualization and plotting)

## Quick Start

### Option 1: Use Project Scaffolding (Recommended for New Users)

The fastest way to get started is using the project scaffolding feature:

```python
import waterlib

# Create a new project with working examples
project_path = waterlib.create_project("my_water_model")
print(f"Created project at: {project_path}")
```

This creates a complete project structure with:
- A working baseline model (`models/baseline.yaml`)
- Example climate data (`data/wgen_params.csv`, `data/climate_timeseries.csv`)
- A sample Python script (`run_model.py`)
- Documentation (`README.md`)

Navigate to your project and run the example:

```bash
cd my_water_model
python run_model.py
```

You'll see simulation results and plots in the `outputs/` directory. Now you can modify the baseline model to fit your needs!

**Create a minimal project without examples:**

```python
# Just the directory structure, no example files
project_path = waterlib.create_project(
    "my_model",
    include_examples=False
)
```

**Create in a specific location:**

```python
# Create project in a custom directory
project_path = waterlib.create_project(
    "regional_model",
    parent_dir="/projects/water_resources"
)
```

### Option 2: Create a YAML Model from Scratch

Create a file `my_model.yaml`:

```yaml
name: "Simple Catchment-Reservoir System"
description: "Basic example with catchment, reservoir, and demand"

site:
  latitude: 40.5
  elevation_m: 500

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: 'stochastic'
      params:
        mean_annual: 800  # mm/year
        wet_day_prob: 0.3
        wet_wet_prob: 0.6
    temperature:
      mode: 'stochastic'
      params:
        mean_tmin: 5   # °C
        mean_tmax: 20  # °C
    et_method: 'hargreaves'

  visualization:
    figure_size: [12, 8]

components:
  catchment:
    type: Catchment
    area_km2: 100.0
    snow17_params:
      scf: 1.0
      mfmax: 1.5
    awbm_params:
      c1: 0.134
      c2: 0.433
      c3: 0.433
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Mountain Catchment'

  main_reservoir:
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
      label: 'Main Reservoir'

  city_demand:
    type: Demand
    source: main_reservoir
    mode: municipal
    population: 50000
    per_capita_demand_lpd: 200
    meta:
      x: 0.5
      y: 0.2
      color: '#FF6347'
      label: 'City Water Supply'
```

**Note:** Climate parameters for stochastic mode are nested under `params:` as shown above. This keeps the configuration organized and clearly separates mode-specific parameters. See the [Global Climate Utilities](#global-climate-utilities) section for complete documentation.

### Run your simulation

```python
import waterlib

# Load the model
model = waterlib.load_model('my_model.yaml')

# Run the complete simulation
results = waterlib.run_simulation(
    model,
    output_dir='./results',
    generate_plots=True
)

# The simulation automatically creates:
# - results/results.csv (all component outputs)
# - results/simulation.log (detailed execution log)
# - results/network_diagram.png (model structure)
# - results/simulation_plots.png (time series plots)

# Analyze results
print(f"Mean reservoir volume: {results.dataframe['main_reservoir.storage'].mean():,.0f} m³")
print(f"Total demand supplied: {results.dataframe['city_demand.supplied'].sum():,.0f} m³")

# Export to CSV
results.to_csv('./results/simulation_results.csv')
```

### Visualize your model

```python
# Create network diagram
model.visualize(output_path='./results/model_network.png')

# Create custom plots
results.plot(
    outputs=['main_reservoir.storage'],
    secondary_outputs=['catchment.runoff_m3d'],
    title='Reservoir Volume and Catchment Runoff',
    filename='./results/reservoir_analysis.png'
)
```

That's it! Whether you start with scaffolding or build from scratch, you can have a complete water system model running in minutes.

## Project Scaffolding

The `create_project()` function helps you get started quickly by generating a complete project structure with working examples.

### What Gets Created

When you run `waterlib.create_project("my_model")`, you get:

```
my_model/
├── README.md                    # Project documentation with getting started guide
├── models/
│   └── baseline.yaml            # Complete working model (catchment-reservoir-demand)
├── data/
│   ├── wgen_params.csv          # Monthly weather generator parameters
│   ├── climate_timeseries.csv   # One year of example daily climate data
│   └── README.md                # Data directory documentation
├── outputs/                     # Simulation results, plots, and logs
├── config/                      # Empty directory for additional configs
└── run_model.py                 # Sample Python script demonstrating usage
```

### The Baseline Model

The generated `baseline.yaml` includes:

- **Stochastic climate generation** using WGEN parameters
- **Catchment** with Snow17 snow processes and AWBM water balance
- **Reservoir** with 5 million m³ capacity and spillway
- **Municipal demand** serving 50,000 people

This model runs immediately without modification and produces realistic results.

### The Sample Script

The `run_model.py` script demonstrates:

- Loading a model from YAML
- Running a simulation with progress bar
- Accessing and analyzing results
- Creating time series plots
- Exporting results to CSV

Run it to see waterlib in action:

```bash
cd my_model
python run_model.py
```

### Example Data Files

**wgen_params.csv**: Monthly weather generator parameters for a temperate climate (latitude ~40°N). Includes:
- Wet/dry day transition probabilities
- Precipitation amount distributions
- Temperature means and variability
- Solar radiation patterns

**climate_timeseries.csv**: One year of example daily climate data showing the required format for timeseries mode. Includes:
- Daily precipitation (mm)
- Min/max temperature (°C)
- Reference evapotranspiration (mm/day)

Both files are ready to use and include detailed comments explaining the parameters.

### Customizing Your Project

After creating a project, you can:

1. **Modify the baseline model**: Edit `models/baseline.yaml` to match your watershed
2. **Add your own data**: Replace example data files with your actual climate data
3. **Create scenarios**: Copy `baseline.yaml` to create alternative scenarios
4. **Extend the script**: Modify `run_model.py` to add custom analysis

### Use Cases

**For new users:**
- Get started immediately with working examples
- Learn by modifying a complete model
- Understand the YAML structure through examples

**For consultants:**
- Rapidly scaffold new client projects
- Consistent project structure across engagements
- Professional documentation included

**For workshops:**
- Provide identical starting point for all participants
- Focus on modeling, not setup
- Working examples for hands-on exercises

**For testing:**
- Create temporary projects for experimentation
- Test new features in isolated environments
- Quickly prototype model structures

### API Reference

```python
waterlib.create_project(
    name: str,                    # Project name (directory name)
    parent_dir: str = ".",        # Where to create project
    include_examples: bool = True, # Include example files
    overwrite: bool = False       # Overwrite if exists
) -> Path                         # Returns absolute path to project
```

See the [API Reference](docs/API_REFERENCE.md#create_project) for complete documentation.

## Live Model Watcher: The Split-Screen Workflow

**The recommended way to build models** is using the Live Model Watcher notebook, which provides instant visual feedback as you design your system.

### What is the Live Watcher?

The Live Model Watcher (`examples/live_view.ipynb`) monitors your YAML file for changes and automatically reloads and visualizes your model whenever you save. This enables a powerful split-screen workflow:

- **Left side**: Edit your YAML model in your text editor
- **Right side**: Jupyter notebook shows live visualization updates
- **Result**: See your changes instantly without manual reloading

### Why Use the Live Watcher?

This workflow is perfect for:
- **Iterative design**: Quickly experiment with different layouts and configurations
- **Visual debugging**: Immediately see if connections are correct
- **Client presentations**: Build models live during meetings
- **Learning**: Understand how YAML changes affect the model structure

### Getting Started with Live Watcher

1. **Open the notebook**:
   ```bash
   cd examples
   jupyter notebook live_view.ipynb
   ```

2. **Run all cells** to start watching

3. **Open a YAML file** in your text editor (side-by-side with Jupyter)

4. **Edit and save** - watch the visualization update automatically!

### What You Can Do

The Live Watcher automatically updates when you:
- Change component positions (`meta.x`, `meta.y`)
- Modify component colors (`meta.color`)
- Add or remove components
- Change connections between components
- Update component parameters

### Example Workflow

```yaml
# Edit your model.yaml
components:
  reservoir:
    type: Reservoir
    # ... parameters ...
    meta:
      x: 0.5    # Try changing this to 0.3
      y: 0.5    # Try changing this to 0.7
      color: '#4169E1'  # Try '#FF6347' for red
```

Save the file → See the changes instantly in Jupyter!

### Tips for Success

- Use the Live Watcher for **model design and layout**
- Use regular notebooks for **simulation and analysis**
- Start with an example model and modify it incrementally
- Keep your YAML file simple while learning the layout

See [`examples/live_view.ipynb`](examples/live_view.ipynb) for the complete notebook with detailed instructions.

## Component Library

waterlib provides six essential water system components:

### 1. Catchment

Simulates rainfall-runoff with integrated snow processes (Snow17) and water balance (AWBM).

**Parameters:**
- `area_km2`: Catchment area [km²] (required)
- `snow17_params`: Dictionary of Snow17 parameters (required)
- `awbm_params`: Dictionary of AWBM parameters (required)

**Note:** When using Snow17, a top-level `site:` block with `latitude` and `elevation_m` is required.

**Inputs (from climate drivers):**
- Precipitation [mm/day] - accessed via `drivers.get('precipitation')`
- Temperature [°C] - accessed via `drivers.get('temperature')`
- PET [mm/day] - accessed via `drivers.get('et')`

**Outputs:**
- `runoff_m3d`: Daily runoff [m³/day]
- `snow_water_equivalent`: SWE [mm]

**Example:**
```yaml
site:
  latitude: 40.5
  elevation_m: 1200

components:
  catchment:
    type: Catchment
    area_km2: 100.0
    snow17_params:  # Latitude/elevation from site block
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
```

### 2. Reservoir

Models water storage with integrated spillway for passive overflow.

**Parameters:**
- `initial_storage_m3`: Starting storage [m³] (required)
- `max_storage_m3`: Maximum capacity [m³] (required)
- `surface_area_m2`: Surface area for evaporation [m²] (required)
- `spillway_elevation_m`: Spillway crest elevation [m] (required)
- `inflows`: List of inflow connections defining graph topology (required)

**Note on Connections:** The `inflows` parameter (plural) in YAML defines the graph topology by listing which component outputs feed into this reservoir. At runtime, the framework resolves these connections and provides a single aggregated `inflow` (singular) value to the reservoir's `step()` method.

**Inputs:**
- `inflow`: Incoming flow [m³/day]
- `release`: Controlled release [m³/day]
- Evaporation (from global climate) [mm/day]

**Outputs:**
- `storage`: Current storage [m³]
- `outflow`: Total outflow (release + spill) [m³/day]
- `spill`: Spillway overflow [m³/day]
- `elevation`: Water surface elevation [m]

**Example:**
```yaml
main_reservoir:
  type: Reservoir
  initial_storage_m3: 2000000
  max_storage_m3: 5000000
  surface_area_m2: 500000
  spillway_elevation_m: 245.0
  inflows:
    - catchment.runoff_m3d
```

### 3. Pump

Flow control component with constant or variable modes.

**Parameters:**
- `control_mode`: 'deadband' or 'proportional' (required)
- `capacity`: Maximum flow rate [m³/day] (required)
- `process_variable`: Component output to monitor, e.g., 'reservoir.storage' (for feedback control)
- `target`: Target value for control (constant or seasonal lookup table)
- `deadband`: Deadband threshold (for deadband mode)
- `kp`: Proportional gain coefficient (for proportional mode)

**Inputs:**
- `source_flow`: Available flow [m³/day]
- `control`: Control signal (for variable mode)

**Outputs:**
- `pumped_flow_m3d`: Extracted flow [m³/day]

**Example (deadband mode):**
```yaml
pump_station:
  type: Pump
  control_mode: deadband
  capacity: 50000
  process_variable: 'main_reservoir.elevation'
  target: 100.0
  deadband: 2.0
```

**Example (proportional mode with feedback):**
```yaml
pump_station:
  type: Pump
  control_mode: proportional
  capacity: 100000
  process_variable: 'main_reservoir.storage'
  target: 2000000
  kp: 0.00001
```

### 4. Demand

Water extraction component with municipal or agricultural modes.

**Parameters:**
- `source`: Source component (required)
- `mode`: 'municipal' or 'agricultural' (required)
- **Municipal mode:**
  - `population`: Population served (required)
  - `per_capita_demand_lpd`: Per capita demand [L/person/day] (required)
- **Agricultural mode:**
  - `irrigated_area_ha`: Irrigated area [hectares] (required)
  - `crop_coefficient`: Crop coefficient (required)

**Inputs:**
- `available_supply`: Available water [m³/day]
- PET (from global climate, for agricultural mode) [mm/day]

**Outputs:**
- `demand`: Calculated demand [m³/day]
- `supplied`: Actually supplied [m³/day]
- `deficit`: Unmet demand [m³/day]

**Example (municipal):**
```yaml
city_demand:
  type: Demand
  source: main_reservoir
  mode: municipal
  population: 50000
  per_capita_demand_lpd: 200
```

**Example (agricultural):**
```yaml
farm_demand:
  type: Demand
  source: irrigation_diversion
  mode: agricultural
  irrigated_area_ha: 500
  crop_coefficient: 0.8
```

### 5. RiverDiversion

Diverts flow from a river or stream.

**Parameters:**
- `max_diversion_m3d`: Maximum diversion rate [m³/day] (required)
- `priority`: Diversion priority (required)
- `source`: Source component (required)

**Inputs:**
- `river_flow`: Available river flow [m³/day]

**Outputs:**
- `diverted_flow_m3d`: Extracted flow [m³/day]
- `remaining_flow_m3d`: Flow continuing downstream [m³/day]

**Example:**
```yaml
irrigation_diversion:
  type: RiverDiversion
  max_diversion_m3d: 50000
  priority: 1
  source: river_junction
```

### 6. Junction

Aggregates multiple flows.

**Parameters:**
- `inflows`: List of inflow connections defining graph topology (required)

**How it works:** The `inflows` parameter in YAML specifies which component outputs to aggregate (e.g., `['catchment1.runoff_m3d', 'catchment2.runoff_m3d']`). The framework resolves these connections and provides the individual flow values to the Junction's `step()` method, which sums them to produce the output.

**Outputs:**
- `outflow_m3d`: Combined flow [m³/day]

**Example:**
```yaml
confluence:
  type: Junction
  inflows:
    - upper_catchment.runoff_m3d
    - lower_catchment.runoff_m3d
```

## Global Climate Utilities

waterlib provides built-in climate utilities that are available to all components without requiring explicit YAML component definitions. This eliminates boilerplate and makes models cleaner.

### Three Climate Modes

waterlib supports three modes for each climate variable, and you can mix modes (e.g., WGEN precipitation with timeseries temperature):

1. **WGEN**: Stochastic weather generator (Markov chain-gamma model)
2. **Timeseries**: Load actual data from CSV files
3. **Stochastic**: Simple stochastic generators (legacy)

### Configuration

Climate utilities are configured in the `settings.climate` block of your YAML file:

```yaml
settings:
  climate:
    precipitation:
      mode: 'stochastic'  # or 'timeseries'
      params:
        mean_annual: 800  # mm/year
        wet_day_prob: 0.3
        wet_wet_prob: 0.6
        alpha: 1.0  # Shape parameter (optional, default=1.0)
      seed: 42  # Random seed (optional)
    temperature:
      mode: 'stochastic'  # or 'timeseries'
      params:
        mean_tmin: 5   # °C
        mean_tmax: 20  # °C
        amplitude_tmin: 10  # °C
        amplitude_tmax: 10  # °C
        std_tmin: 3  # °C (optional, default=3)
        std_tmax: 3  # °C (optional, default=3)
      seed: 42  # Random seed (optional)
    et_method: 'hargreaves'
    latitude: 40.5
```

**Note on Configuration Format:**

For stochastic mode, parameters are nested under `params:` as shown above. This keeps the configuration organized and makes it clear which parameters belong to the climate driver.

### PrecipGen (Stochastic Precipitation)

Generates synthetic daily precipitation using a two-state Markov chain model.

**Configuration:**
```yaml
precipitation:
  mode: 'stochastic'
  params:
    mean_annual: 800  # Mean annual precipitation [mm/year]
    wet_day_prob: 0.3  # Probability of wet day after dry day [0-1]
    wet_wet_prob: 0.6  # Probability of wet day after wet day [0-1]
    alpha: 1.0  # Shape parameter for exponential distribution (optional, default=1.0)
  seed: 42  # Random seed for reproducibility (optional)
```

**Parameters (nested under `params:`):**
- `mean_annual`: Mean annual precipitation [mm/year]
- `wet_day_prob`: Probability of wet day after dry day [0-1]
- `wet_wet_prob`: Probability of wet day after wet day [0-1]
- `alpha`: Shape parameter for exponential distribution (default=1.0)

**Top-level parameters:**
- `seed`: Random seed for reproducibility (optional)

### TempGen (Stochastic Temperature)

Generates synthetic daily minimum and maximum temperature using sinusoidal annual cycle.

**Configuration:**
```yaml
temperature:
  mode: 'stochastic'
  params:
    mean_tmin: 5   # Mean annual minimum temperature [°C]
    mean_tmax: 20  # Mean annual maximum temperature [°C]
    amplitude_tmin: 10  # Seasonal amplitude for Tmin [°C] (optional, default=10)
    amplitude_tmax: 10  # Seasonal amplitude for Tmax [°C] (optional, default=10)
    std_tmin: 3  # Standard deviation for daily Tmin variation [°C] (optional, default=3)
    std_tmax: 3  # Standard deviation for daily Tmax variation [°C] (optional, default=3)
  seed: 42  # Random seed for reproducibility (optional)
```

**Parameters (nested under `params:`):**
- `mean_tmin`: Mean annual minimum temperature [°C]
- `mean_tmax`: Mean annual maximum temperature [°C]
- `amplitude_tmin`: Seasonal amplitude for Tmin [°C] (default=10)
- `amplitude_tmax`: Seasonal amplitude for Tmax [°C] (default=10)
- `std_tmin`: Standard deviation for daily Tmin variation [°C] (default=3)
- `std_tmax`: Standard deviation for daily Tmax variation [°C] (default=3)

**Top-level parameters:**
- `seed`: Random seed for reproducibility (optional)

### Hargreaves-Samani ET

Calculates reference evapotranspiration (ET0) from temperature and latitude.

**Parameters:**
- `latitude`: Site latitude [degrees]
- `hargreaves_coefficient`: Hargreaves coefficient (default=0.0023)

**Formula:**
```
ET0 = C_H * R_a * (T_mean + 17.8) * sqrt(T_max - T_min)
```

Where:
- C_H is the Hargreaves coefficient
- R_a is extraterrestrial radiation [MJ/m²/day]
- T_mean is mean daily temperature [°C]
- T_max and T_min are daily max/min temperatures [°C]

### Timeseries Mode

Load actual climate data from CSV files:

```yaml
settings:
  climate:
    precipitation:
      mode: 'timeseries'
      file: 'data/climate_timeseries.csv'
      column: 'precip_mm'
    temperature:
      mode: 'timeseries'
      file: 'data/climate_timeseries.csv'
      tmin_column: 'tmin_c'
      tmax_column: 'tmax_c'
    solar_radiation:
      mode: 'timeseries'
      file: 'data/climate_timeseries.csv'
      column: 'solar_mjm2'
    et_method: 'hargreaves'
    latitude: 40.5
```

**CSV file format:**
```csv
date,precip_mm,tmin_c,tmax_c,solar_mjm2
2020-01-01,5.2,2.1,12.3,8.5
2020-01-02,0.0,3.4,14.2,10.2
2020-01-03,12.5,1.8,10.5,6.3
```

### Switching Between Modes

One of waterlib's strengths is the ability to easily switch between modes without changing component definitions:

**Switch from WGEN to Timeseries:**
Just change the `mode` parameter in your YAML - no component changes needed!

**Mixed Mode (WGEN + Timeseries):**
```yaml
settings:
  climate:
    precipitation:
      mode: 'wgen'  # Synthetic precipitation
    temperature:
      mode: 'timeseries'  # Observed temperatures
      file: 'data/observed_temps.csv'
      tmin_column: 'tmin'
      tmax_column: 'tmax'
    solar_radiation:
      mode: 'wgen'  # Synthetic solar radiation
    wgen_config:
      param_file: 'data/wgen_params.csv'
      # ... WGEN parameters ...
```

Components automatically receive climate data through the DriverRegistry - they don't know or care about the source!

### How Components Access Climate Data

Components that need climate data (like Catchment) automatically receive it through the **DriverRegistry** system. At runtime, the simulation framework provides a `drivers` object to each component's `step(date, drivers)` method, which allows access to climate data without explicit YAML connections.

**Example:**
```yaml
# Climate configured in settings
settings:
  climate:
    precipitation:
      mode: 'wgen'  # or 'timeseries' or 'stochastic'
    temperature:
      mode: 'wgen'
    wgen_config:
      param_file: 'data/wgen_params.csv'
      # ... parameters ...

# Catchment automatically receives climate data through drivers
components:
  catchment:
    type: Catchment
    area_km2: 100.0
    # No need to specify precipitation source!
    # Works the same regardless of climate mode!
```

**Type-safe API with IDE autocompletion:**
```python
# Inside component step() method:
def step(self, date, drivers):
    # New API: attribute-based access with autocompletion
    precip = drivers.climate.precipitation.get_value(date)
    temp = drivers.climate.temperature.get_value(date)  # Returns {'tmin': x, 'tmax': y}
    et = drivers.climate.et.get_value(date)

    # For components needing average temperature:
    if isinstance(temp, dict):
        tavg = (temp['tmin'] + temp['tmax']) / 2.0
    else:
        tavg = temp  # Backward compatibility

    # Benefits:
    # - IDE autocomplete: type "drivers.climate." and see options
    # - Typos caught at design time, not runtime
    # - No magic strings: AttributeError if you type "precip" instead of "precipitation"
    # - Source-agnostic: Works with WGEN, timeseries, or stochastic modes
```

**How it works internally:**
- The framework creates a `DriverRegistry` containing all climate utilities (precipitation, temperature, ET, solar radiation)
- Each component's `step(date, drivers)` method receives this registry
- Components use `drivers.climate.precipitation` for type-safe access with IDE autocompletion
- The ClimateManager handles data generation/loading and updates the DriverRegistry each timestep

### Visualization Exclusion

Global utilities are excluded from network diagrams by default, keeping visualizations clean and focused on physical components. If you need to show climate inputs, you can use explicit Timeseries components instead.

## Visualization and Meta Dictionaries

waterlib provides powerful visualization capabilities with explicit control over node positioning and styling.

### Meta Dictionary

Each component can include a `meta` dictionary that controls its appearance in network diagrams:

```yaml
components:
  catchment:
    type: Catchment
    area_km2: 100.0
    # ... parameters ...
    meta:
      x: 0.5          # X position (0-1, left to right)
      y: 0.8          # Y position (0-1, bottom to top)
      color: '#90EE90'  # Node color (hex or name)
      label: 'Mountain Catchment'  # Display label
```

**Meta fields:**
- `x`: Horizontal position (0=left, 1=right)
- `y`: Vertical position (0=bottom, 1=top)
- `color`: Node color (hex code or matplotlib color name)
- `label`: Display label (defaults to component name)

### Creating Network Diagrams

```python
import waterlib

# Load model
model = waterlib.load_model('my_model.yaml')

# Create network diagram
model.visualize(output_path='model_network.png')
```

**Visualization features:**
- Explicit node positioning from meta dictionaries
- Color-coded nodes by type or custom colors
- Directed edges showing flow dependencies
- Clean layout optimized for top-to-bottom flow
- High-resolution output (300 DPI) for reports

**Figure size control:**
```yaml
settings:
  visualization:
    figure_size: [12, 8]  # width, height in inches
```

### Creating Time Series Plots

The `Results` object provides plotting capabilities:

```python
# Single-axis plot
results.plot(
    outputs=['main_reservoir.storage'],
    title='Reservoir Volume Over Time',
    filename='reservoir_volume.png'
)

# Dual-axis plot (different scales)
results.plot(
    outputs=['main_reservoir.storage'],
    secondary_outputs=['catchment.runoff_m3d'],
    title='Reservoir Volume and Catchment Runoff',
    filename='volume_vs_runoff.png'
)

# Multi-variable plot
results.plot(
    outputs=['main_reservoir.storage', 'main_reservoir.elevation'],
    secondary_outputs=['catchment.runoff_m3d', 'city_demand.supplied'],
    title='Reservoir State and Flow Metrics',
    filename='multi_variable.png'
)
```

**Plot features:**
- Automatic axis labels from dot-notation identifiers
- Grid for improved readability
- Legend with all variable names
- Distinct colors for primary vs. secondary variables
- High resolution (300 DPI) for publications
- Tight layout to prevent label clipping

## YAML Structure Reference

### Complete YAML Template

```yaml
# Model metadata
name: "Model Name"
description: "Model description"

# Physical site properties
site:
  latitude: 40.5        # Decimal degrees (-90 to 90)
  elevation_m: 500      # Meters above sea level
  time_zone: -7.0       # Optional: UTC offset in hours

# Simulation settings
settings:
  # Date range
  start_date: "YYYY-MM-DD"
  end_date: "YYYY-MM-DD"

  # Climate configuration
  climate:
    precipitation:
      mode: 'stochastic'  # or 'timeseries' or 'wgen'
      params:  # for stochastic mode - nested parameters
        mean_annual: 800
        wet_day_prob: 0.3
        wet_wet_prob: 0.6
        alpha: 1.0  # optional
      seed: 42  # optional, for reproducibility
      # OR for timeseries mode:
      # file: 'data/precip.csv'
      # column: 'precip_mm'

    temperature:
      mode: 'stochastic'  # or 'timeseries' or 'wgen'
      params:  # for stochastic mode - nested parameters
        mean_tmin: 5
        mean_tmax: 20
        amplitude_tmin: 10  # optional
        amplitude_tmax: 10  # optional
        std_tmin: 3  # optional
        std_tmax: 3  # optional
      seed: 42  # optional, for reproducibility
      # OR for timeseries mode:
      # file: 'data/temp.csv'
      # tmin_column: 'tmin_c'
      # tmax_column: 'tmax_c'

    et_method: 'hargreaves'

    # WGEN weather generator configuration (optional)
    # Note: latitude and elevation are now in the site: block
    wgen_config:
      param_file: data/wgen_params.csv
      txmd: 18.5      # Mean Tmax dry (°C)
      txmw: 15.3      # Mean Tmax wet (°C)
      tn: 4.7         # Mean Tmin (°C)
      atx: 15.1       # Amplitude Tmax (°C)
      atn: 11.7       # Amplitude Tmin (°C)
      cvtx: 0.01675   # CV Tmax mean
      acvtx: -0.00383 # CV Tmax amplitude
      cvtn: 0.01605   # CV Tmin mean
      acvtn: -0.00345 # CV Tmin amplitude
      dt_day: 200     # Peak temperature day
      seed: 42        # Optional: random seed

  # Visualization settings
  visualization:
    figure_size: [12, 8]

# Component definitions
components:
  component_name:
    type: ComponentType
    # Component-specific parameters
    param1: value1
    param2: value2
    # Visualization metadata
    meta:
      x: 0.5
      y: 0.5
      color: '#RRGGBB'
      label: 'Display Name'

# Connections (optional - can be inferred from component parameters)
connections:
  - from: component1.output
    to: component2.input
```

### Data Types

- **Scalars**: `population: 50000` (int/float)
- **Strings**: `mode: 'municipal'`
- **Lists**: `inflows: [comp1, comp2]`
- **Dictionaries**: `snow17_params: {scf: 1.0, mfmax: 1.5}`
- **File paths**: Relative to YAML file location

### Comments

YAML supports inline comments for documentation:

```yaml
components:
  # This is a comment
  catchment:  # This is also a comment
    type: Catchment
    area_km2: 100.0  # Catchment area in square kilometers
```

## Examples

The [`examples/`](examples/) directory contains complete working examples:

### Recommended Starting Point

- **`live_view.ipynb`**: 🌟 **Start here!** Live Model Watcher with split-screen workflow for iterative design

### Basic Examples

- **`simple_catchment_reservoir.yaml`**: Basic catchment-reservoir-demand system
- **`full_system.yaml`**: Comprehensive example with all component types
- **`library_first_workflow.ipynb`**: Jupyter notebook demonstrating the library-first workflow

### Specialized Examples

- **`awbm_example.yaml`**: AWBM catchment modeling
- **`snow17_example.yaml`**: Snow accumulation and melt
- **`awbm_hargreaves_example.py`**: Catchment with Hargreaves ET
- **`reservoir_with_evaporation.yaml`**: Reservoir with evaporation losses

### Feedback Loop Examples

- **`feedback_pump_control.yaml`**: Pump control with downstream feedback
- **`feedback_treatment_recycle.yaml`**: Treatment plant with recycle stream

### Visualization Examples

- **`visualization_demo.yaml`**: Demonstrates meta dictionary usage
- **`generate_readme_images.py`**: Script to generate documentation images

### Python Scripts

- **`quickstart.py`**: Complete working example with detailed comments
- **`awbm_quickstart.py`**: AWBM catchment example
- **`snow17_quickstart.py`**: Snow17 example
- **`snow17_awbm_quickstart.py`**: Combined Snow17+AWBM example
- **`results_logging.py`**: Results analysis and plotting
- **`visualize_model.py`**: Model visualization examples
- **`visualize_feedback.py`**: Feedback loop visualization

To run the examples:

```bash
cd examples
python quickstart.py
python awbm_quickstart.py
python visualize_model.py
```

## Error Handling

waterlib provides clear, actionable error messages:

### Configuration Errors

```python
ConfigurationError: Component 'city_demand' of type 'Demand' is missing required
parameter 'population'. Required parameters for municipal mode: population, per_capita_demand_lpd
```

### Circular Dependencies

```python
CircularDependencyError: Model contains circular dependencies that cannot be broken
by LaggedValue components: reservoir_a -> pump_b -> reservoir_c -> reservoir_a

Add a LaggedValue component to break the cycle.
```

### Missing Climate Data

```python
KeyError: Date 2020-01-15 not found in climate data.
Available date range: 2020-01-01 to 2020-01-10
```

### Invalid Connections

```python
UndefinedComponentError: Connection references undefined component 'bad_reservoir'.
Available components: catchment, main_reservoir, city_demand
```

All errors include component names, parameter names, and helpful suggestions for resolution.

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=waterlib --cov-report=html
```

The test suite includes:
- Unit tests for each component
- Property-based tests using Hypothesis
- Integration tests for complete models
- YAML parsing and validation tests
- Error handling tests

## Project Status

**Version 0.2.0** - Current Release

Current features:
- ✅ Six core components (Catchment, Reservoir, Pump, Demand, RiverDiversion, Junction)
- ✅ Global climate utilities (PrecipGen, TempGen, Hargreaves-Samani)
- ✅ Single YAML configuration with settings block
- ✅ One-function simulation execution
- ✅ Integrated components (Catchment with Snow17+AWBM, Reservoir with spillway)
- ✅ Network visualization with meta dictionary control
- ✅ Results plotting with dual-axis support
- ✅ Comprehensive error handling
- ✅ Property-based testing with Hypothesis

## Roadmap

- Additional ET methods (Penman-Monteith, Priestley-Taylor)
- Optimization and calibration framework
- Additional component types (pipes, treatment plants)
- Interactive plotting

## Contributing

Contributions welcome! Areas of interest:
- Additional component types
- Alternative ET calculation methods
- Visualization improvements
- Documentation improvements

**For Developers:**
- [Developer Guide](DEVELOPER_GUIDE.md) - Architecture and patterns
- [Kernel Purity Enforcement](docs/KERNEL_PURITY_ENFORCEMENT.md) - Architectural constraints

Please open an issue to discuss proposed changes before submitting a pull request.

## License

MIT License - see LICENSE file for details.

## Documentation

### Core Documentation

- [Getting Started Guide](GETTING_STARTED.md) - Tutorial for new users
- [Component Reference](COMPONENTS.md) - Complete component documentation
- [API Reference](docs/API_REFERENCE.md) - Python API documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Architecture and development patterns

### Architecture

- [Architecture Diagrams](docs/ARCHITECTURE_DIAGRAM.md) - Visual overview
- [Kernel Usage Examples](docs/KERNEL_USAGE_EXAMPLES.md) - Using kernels directly
- [Kernel Purity Enforcement](docs/KERNEL_PURITY_ENFORCEMENT.md) - Architectural constraints

## Support

- **Documentation**: See links above
- **Examples**: Check the `examples/` directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
