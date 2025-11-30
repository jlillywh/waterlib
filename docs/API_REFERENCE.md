# API Reference

Python API reference for waterlib.

## Core Functions

### create_project()

Create a new waterlib project with directory structure and starter files.

```python
def create_project(
    name: str,
    parent_dir: str = ".",
    include_examples: bool = True,
    overwrite: bool = False
) -> Path
```

**Parameters:**
- `name` (str): Project name
- `parent_dir` (str): Parent directory (default: current directory)
- `include_examples` (bool): Include example files (default: True)
- `overwrite` (bool): Overwrite existing directory (default: False)

**Returns:** Path to created project directory

**Example:**

```python
import waterlib

# Create new project
project_path = waterlib.create_project("my_water_model")

# Create in specific location without examples
project_path = waterlib.create_project(
    "test_model",
    parent_dir="/projects",
    include_examples=False
)
```

---

### load_model()

Load a water system model from YAML configuration.

```python
def load_model(yaml_path: str | Path) -> Model
```

**Parameters:**
- `yaml_path` (str or Path): Path to YAML file

**Returns:** Model object ready for simulation

**Example:**

```python
import waterlib

model = waterlib.load_model('models/my_model.yaml')
print(f"Loaded: {model.name}")
print(f"Components: {list(model.components.keys())}")
```

---

### run_simulation()

Execute simulation and save results.

```python
def run_simulation(
    model: Model,
    output_dir: str | Path,
    progress: bool = True,
    generate_plots: bool = False
) -> SimulationResult
```

**Parameters:**
- `model` (Model): Model from load_model()
- `output_dir` (str or Path): Directory for results
- `progress` (bool): Show progress bar (default: True)
- `generate_plots` (bool): Generate diagrams (default: False)

**Returns:** SimulationResult with paths and dataframe

**Example:**

```python
import waterlib

model = waterlib.load_model('models/my_model.yaml')
results = waterlib.run_simulation(
    model,
    output_dir='./results',
    generate_plots=True
)

# Analyze results
print(f"Results: {results.csv_path}")
mean_storage = results.dataframe['reservoir.storage'].mean()
print(f"Mean storage: {mean_storage:,.0f} m³")
```

---

## Model Class

Represents a complete water system model. Typically created by `load_model()`.

### Properties

**components** - Dictionary of components by name

```python
model.components['reservoir'].max_storage
```

**settings** - Model configuration (dates, timestep)

```python
model.settings.start_date
model.settings.end_date
```

**site** - Physical site properties (latitude, elevation)

```python
model.site.latitude       # Decimal degrees
model.site.elevation_m    # Meters above sea level
model.site.time_zone      # Optional: UTC offset
```

**drivers** - Climate data providers (DriverRegistry)

```python
# Type-safe API (recommended)
precip = model.drivers.climate.precipitation.get_value(date)
temp = model.drivers.climate.temperature.get_value(date)  # Returns {'tmin': x, 'tmax': y}
et = model.drivers.climate.et.get_value(date)
solar = model.drivers.climate.solar_radiation.get_value(date)

# Legacy API (still supported)
precip = model.drivers.get('precipitation').get_value(date)
```

---

## Results Class

Simulation results with time series data.

### Properties

- `csv_path` (Path): Path to results CSV
- `dataframe` (pd.DataFrame): Results as DataFrame
- `start_date` (datetime): Simulation start
- `end_date` (datetime): Simulation end
- `num_timesteps` (int): Number of timesteps
- `components_logged` (List[str]): Component names in results

### Methods

**plot()** - Generate time series plots

```python
results.plot(
    components=['reservoir', 'catchment'],
    outputs=['storage', 'runoff_m3d'],
    save_path='plots.png'
)
```

---

## Exception Classes

### ConfigurationError

Raised for invalid YAML configuration.

```python
try:
    model = waterlib.load_model('bad_model.yaml')
except waterlib.ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### ValidationError

Raised for invalid component parameters or connections.

### SimulationError

Raised when simulation fails during execution.

---

## Component Classes

### MetStation

Records and persists climate driver data for validation and analysis.

```python
from waterlib.components.met_station import MetStation
from waterlib.core.drivers import DriverRegistry

# Create met station with all logging enabled (default)
met = MetStation(drivers)

# Or with selective logging
met = MetStation(
    drivers,
    log_precip=True,
    log_temp=True,
    log_solar=False,
    log_et0=False
)

# Record data each timestep
for date in date_range:
    met.step(date)

# Export results
met.export_csv('climate_data.csv')
df = met.to_dataframe()
```

#### MetStation Parameters

**Parameters:**
- `drivers` (DriverRegistry): Driver registry for accessing climate data (required)
- `log_precip` (bool): Log precipitation data (default: True)
- `log_temp` (bool): Log temperature data (tmin and tmax) (default: True)
- `log_solar` (bool): Log solar radiation data (default: True)
- `log_et0` (bool): Log reference ET data (default: True)

**Example:**

```python
# Log only precipitation and temperature
met = MetStation(
    drivers,
    log_precip=True,
    log_temp=True,
    log_solar=False,
    log_et0=False
)
```

#### MetStation Methods

**step(sim_date: date)** - Record climate data for a single timestep

```python
from datetime import date
met.step(date(2020, 1, 1))
```

**to_dataframe() -> pd.DataFrame** - Convert recorded data to DataFrame

```python
df = met.to_dataframe()
print(df.head())
#    precip_mm  tmin_c  tmax_c  solar_mjm2  et0_mm
# 0       10.0     5.0    15.0        20.0     2.0
# 1       11.0     6.0    16.0        21.0     3.0
```

**export_csv(path: str)** - Export recorded data to CSV file

```python
met.export_csv('outputs/climate_data.csv')
```

#### YAML Configuration

```yaml
components:
  met_station:
    type: MetStation
    log_precip: true
    log_temp: true
    log_solar: true
    log_et0: true
```

**Note:** MetStation automatically receives climate data from the DriverRegistry. No explicit connections needed.

---

## Complete Example

```python
import waterlib

# Create project
project_path = waterlib.create_project("river_system")

# Load model
model = waterlib.load_model(project_path / "models/baseline.yaml")

# Run simulation
results = waterlib.run_simulation(
    model,
    output_dir=project_path / "outputs",
    progress=True,
    generate_plots=True
)

# Analyze
df = results.dataframe
print(f"Simulation complete: {results.num_timesteps} days")
print(f"Total runoff: {df['catchment.runoff_m3d'].sum():,.0f} m³")
print(f"Results: {results.csv_path}")

# If model includes MetStation, export climate data
if 'met_station' in model.components:
    met = model.components['met_station']
    met.export_csv(project_path / "outputs/climate_data.csv")
    print("Climate data exported")
```

---

## See Also

- [Getting Started Guide](../GETTING_STARTED.md) - Tutorial
- [Component Reference](../COMPONENTS.md) - Component parameters
- [Developer Guide](../DEVELOPER_GUIDE.md) - Ar
