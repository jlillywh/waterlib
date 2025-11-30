# YAML Schema Reference

Complete reference for waterlib model.yaml configuration files.

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Site Block](#site-block)
4. [Settings Block](#settings-block)
5. [Components Block](#components-block)
6. [Connections Block](#connections-block)
7. [Complete Examples](#complete-examples)
8. [Validation Rules](#validation-rules)

---

## Overview

A waterlib model is defined in a single YAML file that contains:

1. **Metadata** (optional): Model name and description
2. **Settings** (required): Simulation dates, timestep, and climate configuration
3. **Components** (required): Water system components and their parameters
4. **Connections** (optional): Explicit flow connections (can be inferred from component parameters)

### Minimal Example

```yaml
site:
  latitude: 40.5
  elevation_m: 500

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: stochastic
      params:
        mean_annual: 800
    temperature:
      mode: stochastic
      params:
        mean_tmin: 5
        mean_tmax: 20
    et_method: hargreaves

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
```

---

## File Structure

### Top-Level Structure

```yaml
# Optional metadata
name: "Model Name"
description: "Model description"

# Required site configuration (for models using WGEN or Snow17)
site:
  latitude: 40.5        # decimal degrees
  elevation_m: 500      # meters above sea level
  time_zone: -7         # optional: UTC offset

# Required settings
settings:
  # ... settings configuration ...

# Required components
components:
  # ... component definitions ...

# Optional connections
connections:
  # ... explicit connections ...
```

### Data Types

| Type | YAML Syntax | Example |
|------|-------------|---------|
| String | `key: "value"` or `key: value` | `name: "My Model"` |
| Integer | `key: 123` | `population: 50000` |
| Float | `key: 123.45` | `area_km2: 100.5` |
| Boolean | `key: true` or `key: false` | `progress: true` |
| List | `key: [item1, item2]` or multi-line | `inflows: [comp1, comp2]` |
| Dictionary | `key: {k1: v1, k2: v2}` or multi-line | `params: {mean: 10, std: 5}` |
| Date | `key: "YYYY-MM-DD"` | `start_date: "2020-01-01"` |
| Path | `key: "path/to/file"` | `file: "../data/precip.csv"` |

### Comments

```yaml
# This is a comment
components:
  catchment:  # Inline comment
    type: Catchment
    area_km2: 100.0  # Catchment area in square kilometers
```

---

## Site Block

The `site` block defines physical site properties used by components and climate models. This block is **required** when using WGEN weather generation or Snow17 snow modeling.

### Structure

```yaml
site:
  latitude: float        # Required: decimal degrees (-90 to 90)
  elevation_m: float     # Required: meters above sea level
  time_zone: int         # Optional: UTC offset (-12 to 14)
```

### Parameters

| Parameter | Type | Required | Units | Valid Range | Description |
|-----------|------|----------|-------|-------------|-------------|
| `latitude` | float | Yes | degrees | -90 to 90 | Site latitude (positive = N, negative = S) |
| `elevation_m` | float | Yes | meters | any | Elevation above mean sea level |
| `time_zone` | int | No | hours | -12 to 14 | UTC offset for local time |

### When is Site Required?

The `site` block is **required** when your model uses:
- **WGEN** stochastic weather generation (uses latitude for Fourier seasonal calculations)
- **Snow17** snow modeling (uses latitude and elevation for snowmelt processes)

If you're only using timeseries climate data and components without Snow17, the site block may be omitted.

### Usage by Components

**WGEN Climate Driver:**
- Uses `latitude` for Fourier-based seasonal temperature and radiation patterns
- Automatically adjusts peak day based on hemisphere (N: day 200, S: day 20)

**Snow17 (within Catchment):**
- Uses `latitude` for melt calculations
- Uses `elevation_m` for temperature adjustments and snow processes

### Examples

**Northern Hemisphere (USA):**
```yaml
site:
  latitude: 40.5        # Central USA
  elevation_m: 1500     # Mountain catchment
  time_zone: -7         # Mountain Time
```

**Southern Hemisphere (Australia):**
```yaml
site:
  latitude: -33.87      # Sydney area
  elevation_m: 50       # Coastal catchment
  time_zone: 10         # AEST
```

**Arctic Region:**
```yaml
site:
  latitude: 68.5        # Northern Norway
  elevation_m: 200
  time_zone: 1          # CET
```

### Notes

- **Latitude validation**: -90° (South Pole) to +90° (North Pole)
- **Positive latitude** = Northern Hemisphere
- **Negative latitude** = Southern Hemisphere
- **Elevation** can be negative (below sea level) but must be reasonable for your location
- **Time zone** is optional and used for timestamp localization

---

## Settings Block

The `settings` block contains simulation configuration and climate settings.

### Structure

```yaml
settings:
  # Simulation period (required)
  start_date: "YYYY-MM-DD"
  end_date: "YYYY-MM-DD"
  timestep: "frequency"  # Optional, default: "1D"

  # Climate configuration (required)
  climate:
    # ... climate settings ...

  # Visualization settings (optional)
  visualization:
    # ... visualization settings ...
```

### Simulation Period

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `start_date` | string | Yes | - | Simulation start date (YYYY-MM-DD) |
| `end_date` | string | Yes | - | Simulation end date (YYYY-MM-DD) |
| `timestep` | string | No | "1D" | Pandas frequency string |

**Timestep values:**
- `"1D"`: Daily (default)
- `"1H"`: Hourly
- `"6H"`: 6-hourly
- `"1W"`: Weekly
- `"1M"`: Monthly

**Example:**

```yaml
settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"
  timestep: "1D"
```

### Climate Configuration

The `climate` block configures global climate drivers.

#### Structure

```yaml
settings:
  climate:
    # Precipitation driver (required)
    precipitation:
      mode: stochastic | timeseries
      # ... mode-specific parameters ...

    # Temperature driver (required)
    temperature:
      mode: stochastic | timeseries
      # ... mode-specific parameters ...

    # ET configuration (required)
    et_method: hargreaves | penman_monteith
    latitude: float  # Required for hargreaves

    # OR explicit ET driver
    # et:
    #   mode: stochastic | timeseries
    #   # ... mode-specific parameters ...
```

#### Stochastic Mode

Generate synthetic climate data using statistical parameters.

**Precipitation (Stochastic):**

```yaml
precipitation:
  mode: stochastic
  seed: 42  # Optional, for reproducibility
  params:
    mean_annual: 800  # mm/year
    wet_day_prob: 0.3  # P(wet|dry)
    wet_wet_prob: 0.6  # P(wet|wet)
    alpha: 1.0  # Optional, shape parameter
```

**OR load parameters from CSV:**

```yaml
precipitation:
  mode: stochastic
  seed: 42
  file: ../data/precip_params.csv
```

CSV format:
```csv
mean_annual,wet_day_prob,wet_wet_prob
800,0.3,0.6
```

**Temperature (Stochastic):**

```yaml
temperature:
  mode: stochastic
  seed: 42  # Optional
  params:
    mean_tmin: 5  # °C
    mean_tmax: 20  # °C
    amplitude_tmin: 10  # °C, seasonal variation
    amplitude_tmax: 10  # °C, seasonal variation
    std_tmin: 3  # °C, daily variation
    std_tmax: 3  # °C, daily variation
```

**OR load from CSV:**

```yaml
temperature:
  mode: stochastic
  seed: 42
  file: ../data/temp_params.csv
    alpha: 1.0
```

Both formats produce identical results. The nested `params:` format is recommended as it provides clearer separation between driver configuration (`mode`, `seed`) and statistical parameters.

#### Timeseries Mode

Load historical climate data from CSV files.

**Precipitation (Timeseries):**

```yaml
precipitation:
  mode: timeseries
  file: ../data/precip.csv
  column: precip_mm
  date_column: date  # Optional, default: first column or index
```

**Temperature (Timeseries):**

```yaml
temperature:
  mode: timeseries
  file: ../data/temp.csv
  tmin_column: tmin_c
  tmax_column: tmax_c
  date_column: date  # Optional
```

**CSV format:**

```csv
date,precip_mm,tmin_c,tmax_c
2020-01-01,5.2,3.1,12.4
2020-01-02,0.0,4.2,14.1
2020-01-03,12.8,2.8,10.9
```

**Notes:**
- File paths are relative to the YAML file location
- Date column must be parseable by pandas (YYYY-MM-DD recommended)
- CSV must cover the full simulation period

#### ET Configuration

**Hargreaves-Samani Method:**

```yaml
climate:
  # ... precipitation and temperature ...
  et_method: hargreaves
  latitude: 40.5  # degrees
  hargreaves_coefficient: 0.0023  # Optional, default: 0.0023
```

**Explicit ET Driver (Stochastic):**

```yaml
climate:
  # ... precipitation and temperature ...
  et:
    mode: stochastic
    seed: 42
    params:
      mean: 3.5  # mm/day
      std: 1.5  # mm/day
    std: 1.5
```

**Explicit ET Driver (Timeseries):**

```yaml
climate:
  # ... precipitation and temperature ...
  et:
    mode: timeseries
    file: ../data/et.csv
    column: et_mm
```

#### Migration Guide: Flat to Nested Format

If you have existing models using the flat parameter format, you can migrate them to the recommended nested `params:` format. Both formats are supported indefinitely, so migration is optional.

**Migration Steps:**

1. **Identify stochastic climate drivers** in your YAML file
2. **Group statistical parameters** under a `params:` key
3. **Keep driver configuration** (`mode`, `seed`, `file`) at the top level

**Example Migration:**

**Before (flat format):**
```yaml
climate:
  precipitation:
    mode: stochastic
    seed: 42
    mean_annual: 800
    wet_day_prob: 0.3
    wet_wet_prob: 0.6
    alpha: 1.0

  temperature:
    mode: stochastic
    seed: 42
    mean_tmin: 5
    mean_tmax: 20
    amplitude_tmin: 10
    amplitude_tmax: 10
    std_tmin: 3
    std_tmax: 3
```

**After (nested format):**
```yaml
climate:
  precipitation:
    mode: stochastic
    seed: 42
    params:
      mean_annual: 800
      wet_day_prob: 0.3
      wet_wet_prob: 0.6
      alpha: 1.0

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
```

**What to Move Under `params:`:**

| Driver | Parameters to Nest |
|--------|-------------------|
| Precipitation (stochastic) | `mean_annual`, `wet_day_prob`, `wet_wet_prob`, `alpha` |
| Temperature (stochastic) | `mean_tmin`, `mean_tmax`, `amplitude_tmin`, `amplitude_tmax`, `std_tmin`, `std_tmax` |
| ET (stochastic) | `mean`, `std` |

**What to Keep at Top Level:**

- `mode` (always)
- `seed` (optional)
- `file` (for timeseries mode or CSV parameter loading)
- `column`, `tmin_column`, `tmax_column`, `date_column` (for timeseries mode)

**Timeseries Mode:**

Timeseries mode does not use `params:` - all parameters remain at the top level:

```yaml
# Timeseries mode - no params: needed
precipitation:
  mode: timeseries
  file: ../data/precip.csv
  column: precip_mm
  date_column: date
```

### Visualization Settings

Optional settings for network diagrams.

```yaml
settings:
  visualization:
    figure_size: [12, 8]  # [width, height] in inches
    dpi: 300  # Optional, default: 300
    node_size: 3000  # Optional, default: 3000
    font_size: 10  # Optional, default: 10
```

---

## Components Block

The `components` block defines water system components.

### Structure

```yaml
components:
  component_name:
    type: ComponentType
    # Component-specific parameters
    param1: value1
    param2: value2
    # Optional visualization metadata
    meta:
      x: 0.5
      y: 0.5
      color: '#90EE90'
      label: 'Display Name'
```

### Component Types

| Type | Description |
|------|-------------|
| `Catchment` | Rainfall-runoff with Snow17 + AWBM |
| `Reservoir` | Water storage with spillway |
| `Pump` | Active flow control |
| `Demand` | Water extraction (municipal or agricultural) |
| `RiverDiversion` | River flow diversion |
| `Junction` | Flow aggregation |
| `MetStation` | Climate data recorder for validation and analysis |

### Data Connections

Components can receive explicit data inputs using the `data_connections` field. This enables feedback control and complex data routing beyond automatic inflow connections.

**Format:**

```yaml
components:
  component_name:
    type: ComponentType
    # ... parameters ...
    data_connections:
      - source: source_component.output_name
        output: output_name
        input: input_name
```

**Example (Pump monitoring reservoir storage):**

```yaml
components:
  reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    inflows:
      - catchment.runoff

  pump:
    type: Pump
    capacity: 50000
    process_variable: reservoir.storage
    target: 3000000
    data_connections:
      - source: reservoir.storage  # Monitor reservoir storage
        output: storage
        input: reservoir.storage
      - source: demand.demand  # Receive demand request
        output: demand
        input: demand
```

**Notes:**
- `source`: Component and output in dot notation (e.g., `reservoir.storage`)
- `output`: Name of the output field from source component
- `input`: Name of the input field in receiving component
- Data connections are processed before each timestep via `_transfer_data()`
- Enables feedback control: pump monitors reservoir, adjusts based on storage level
- Different from `inflows` which define graph edges for execution ordering

### Meta Block

Optional visualization metadata for each component.

```yaml
meta:
  x: float  # X position (0-1, left to right)
  y: float  # Y position (0-1, bottom to top)
  color: string  # Color (hex code or name)
  label: string  # Display label
```

**Example:**

```yaml
components:
  catchment:
    type: Catchment
    area_km2: 100.0
    # ... parameters ...
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Mountain Catchment'
```

**Color options:**
- Hex codes: `'#90EE90'`, `'#4169E1'`, `'#FF6347'`
- Named colors: `'lightgreen'`, `'royalblue'`, `'tomato'`
- See [matplotlib colors](https://matplotlib.org/stable/gallery/color/named_colors.html)

### Catchment

```yaml
catchment_name:
  type: Catchment
  area_km2: float  # Required
  snow17_params:  # Required
    scf: float
    mfmax: float
    mfmin: float
    uadj: float
    si: float
    pxtemp: float
    nmf: float
    tipm: float
    mbase: float
    plwhc: float
    daygm: float
  awbm_params:  # Required
    c1: float
    c2: float
    c3: float
    a1: float
    a2: float
    a3: float
    kbase: float
    ksurf: float
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**See [Component Reference](../COMPONENTS.md#catchment) for parameter details.**

### Reservoir

```yaml
reservoir_name:
  type: Reservoir
  initial_storage_m3: float  # Required
  max_storage_m3: float  # Required
  surface_area_m2: float  # Required
  spillway_elevation_m: float  # Required
  inflows:  # Required
    - component1.output1
    - component2.output2
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**See [Component Reference](../COMPONENTS.md#reservoir) for parameter details.**

### Pump

**Deadband Control Mode:**

```yaml
pump_name:
  type: Pump
  control_mode: deadband  # Required
  capacity: float  # Required (m³/day)
  process_variable: component.output  # Required (e.g., reservoir.storage)
  target: float  # Required (constant target)
  deadband: float  # Required for deadband mode
  inflows:  # Optional (for execution ordering)
    - component1.output1
  data_connections:  # Required for receiving monitored values
    - source: reservoir.storage
      output: storage
      input: reservoir.storage
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**Proportional Control Mode:**

```yaml
pump_name:
  type: Pump
  control_mode: proportional  # Required
  capacity: float  # Required (m³/day)
  process_variable: component.output  # Required
  target: float  # Required (constant) OR dict for seasonal
  kp: float  # Required for proportional mode
  inflows:  # Optional
    - component1.output1
  data_connections:  # Required for receiving monitored values
    - source: reservoir.storage
      output: storage
      input: reservoir.storage
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**Seasonal Target Example:**

```yaml
pump_with_seasonal_target:
  type: Pump
  control_mode: deadband
  capacity: 50000
  process_variable: reservoir.storage
  target:
    1: 2000000    # Jan 1: 2M m³
    182: 3000000  # Jul 1: 3M m³ (summer target)
    365: 2000000  # Dec 31: 2M m³
  deadband: 500000
  data_connections:
    - source: reservoir.storage
      output: storage
      input: reservoir.storage
```

**See [Component Reference](../COMPONENTS.md#pump) for parameter details.**

### Demand

**Municipal Mode:**

```yaml
demand_name:
  type: Demand
  source: component_name  # Required
  mode: municipal  # Required
  population: int  # Required
  per_capita_demand_lpd: float  # Required
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**Agricultural Mode:**

```yaml
demand_name:
  type: Demand
  source: component_name  # Required
  mode: agricultural  # Required
  irrigated_area_ha: float  # Required
  crop_coefficient: float  # Required
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**See [Component Reference](../COMPONENTS.md#demand) for parameter details.**

### RiverDiversion

```yaml
diversion_name:
  type: RiverDiversion
  max_diversion_m3d: float  # Required
  priority: int  # Required
  source: component_name  # Required
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**See [Component Reference](../COMPONENTS.md#riverdiversion) for parameter details.**

### Junction

```yaml
junction_name:
  type: Junction
  inflows:  # Required
    - component1.output1
    - component2.output2
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**See [Component Reference](../COMPONENTS.md#junction) for parameter details.**

### MetStation

Records and persists climate driver data (precipitation, temperature, solar radiation, ET0) for validation and analysis.

```yaml
met_station_name:
  type: MetStation
  log_precip: bool  # Optional, default: true
  log_temp: bool    # Optional, default: true (logs both tmin and tmax)
  log_solar: bool   # Optional, default: true
  log_et0: bool     # Optional, default: true (reference ET)
  meta:  # Optional
    x: float
    y: float
    color: string
    label: string
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `log_precip` | bool | No | true | Log precipitation data |
| `log_temp` | bool | No | true | Log temperature data (tmin and tmax) |
| `log_solar` | bool | No | true | Log solar radiation data |
| `log_et0` | bool | No | true | Log reference ET data |

**Outputs:**

MetStation records data internally and provides export methods:
- `to_dataframe()`: Returns pandas DataFrame with recorded data
- `export_csv(path)`: Exports data to CSV file

**Example (Log all climate variables):**

```yaml
components:
  met_station:
    type: MetStation
    # Uses default config (all variables logged)
    meta:
      x: 0.1
      y: 0.9
      color: '#FFD700'
      label: 'Climate Station'
```

**Example (Log only precipitation and temperature):**

```yaml
components:
  met_station:
    type: MetStation
    config:
      log_precip: true
      log_temp: true
      log_solar: false
      log_et0: false
    meta:
      x: 0.1
      y: 0.9
      color: '#FFD700'
      label: 'Precip/Temp Station'
```

**Usage in Python:**

```python
import waterlib

# Load and run model
model = waterlib.load_model('model.yaml')
results = waterlib.run_simulation(model, output_dir='./results')

# Export climate data
met = model.components['met_station']
met.export_csv('./results/climate_data.csv')

# Or get as DataFrame
df = met.to_dataframe()
print(df.head())
```

**Notes:**
- MetStation automatically receives climate data from the DriverRegistry
- No explicit connections needed - climate data is globally available
- Useful for validating climate inputs and analyzing weather patterns
- Works with any climate mode (WGEN, timeseries, or stochastic)
- Output columns depend on configuration and available drivers:
  - `precip_mm`: Precipitation [mm/day]
  - `tmin_c`: Minimum temperature [°C]
  - `tmax_c`: Maximum temperature [°C]
  - `solar_mjm2`: Solar radiation [MJ/m²/day]
  - `et0_mm`: Reference evapotranspiration [mm/day]

**See [Component Reference](../COMPONENTS.md#metstation) for more details.**

---

## Connections Block

Optional explicit connections between components. Most connections can be inferred from component parameters (e.g., `source`, `inflows`).

### Structure

```yaml
connections:
  - from: component1.output_name
    to: component2.input_name
  - from: component2.output_name
    to: component3.input_name
```

### Example

```yaml
connections:
  - from: catchment.runoff_m3d
    to: reservoir.inflow
  - from: reservoir.outflow
    to: demand.available_supply
```

**Note:** Connections are typically inferred from component parameters and don't need to be explicitly specified.

---

## Complete Examples

### Simple Catchment-Reservoir System

```yaml
name: "Simple Water Supply System"
description: "Catchment feeding reservoir serving municipal demand"

site:
  latitude: 40.5
  elevation_m: 500

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: stochastic
      seed: 42
      params:
        mean_annual: 800
        wet_day_prob: 0.3
        wet_wet_prob: 0.6
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

  visualization:
    figure_size: [12, 8]

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
      label: 'Mountain Catchment'

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
      label: 'Main Reservoir'

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
      label: 'City Water Supply'
```

### Multi-Catchment with River Diversion

```yaml
name: "Multi-Catchment System"
description: "Multiple catchments with river diversion for irrigation"

site:
  latitude: 40.5
  elevation_m: 1200

settings:
  start_date: "2020-01-01"
  end_date: "2020-12-31"

  climate:
    precipitation:
      mode: timeseries
      file: ../data/precip.csv
      column: precip_mm
    temperature:
      mode: timeseries
      file: ../data/temp.csv
      tmin_column: tmin_c
      tmax_column: tmax_c
    et_method: hargreaves

components:
  upper_catchment:
    type: Catchment
    area_km2: 150.0
    snow17_params:
      scf: 1.0
      mfmax: 1.5
    awbm_params:
      c1: 0.134
      c2: 0.433
      c3: 0.433
    meta:
      x: 0.3
      y: 0.9
      color: '#90EE90'

  lower_catchment:
    type: Catchment
    area_km2: 80.0
    snow17_params:
      scf: 1.0
      mfmax: 1.5
    awbm_params:
      c1: 0.134
      c2: 0.433
      c3: 0.433
    meta:
      x: 0.7
      y: 0.9
      color: '#98FB98'

  river_junction:
    type: Junction
    inflows:
      - upper_catchment.runoff_m3d
      - lower_catchment.runoff_m3d
    meta:
      x: 0.5
      y: 0.7
      color: '#4682B4'

  irrigation_diversion:
    type: RiverDiversion
    max_diversion_m3d: 50000
    priority: 1
    source: river_junction
    meta:
      x: 0.7
      y: 0.5
      color: '#32CD32'

  farm_demand:
    type: Demand
    source: irrigation_diversion
    mode: agricultural
    irrigated_area_ha: 500
    crop_coefficient: 0.8
    meta:
      x: 0.7
      y: 0.3
      color: '#228B22'

  main_reservoir:
    type: Reservoir
    initial_storage_m3: 2500000
    max_storage_m3: 5000000
    surface_area_m2: 600000
    spillway_elevation_m: 245.0
    inflows:
      - irrigation_diversion.remaining_flow_m3d
    meta:
      x: 0.3
      y: 0.5
      color: '#4169E1'

  city_demand:
    type: Demand
    source: main_reservoir
    mode: municipal
    population: 75000
    per_capita_demand_lpd: 220
    meta:
      x: 0.3
      y: 0.3
      color: '#FF6347'
```

---

## Validation Rules

### Required Fields

**Top-level:**
- `settings` block (required)
- `components` block (required)

**Settings:**
- `start_date` (required)
- `end_date` (required)
- `climate` block (required)

**Climate:**
- `precipitation` configuration (required)
- `temperature` configuration (required)
- Either `et_method` + `latitude` OR `et` driver (required)

**Components:**
- Each component must have `type` field
- Each component must have all required parameters for its type

### Validation Checks

1. **Date validation:**
   - `start_date` must be before `end_date`
   - Dates must be valid and parseable

2. **Climate validation:**
   - Driver mode must be 'stochastic' or 'timeseries'
   - Stochastic mode requires `params` or `file`
   - Timeseries mode requires `file` and `column`
   - CSV files must exist and be readable

3. **Component validation:**
   - Component type must be valid
   - All required parameters must be present
   - Parameter types must be correct
   - Parameter values must be in valid ranges

4. **Climate parameter format:**
   - Both nested `params:` and flat formats are valid
   - Stochastic mode can use `params:` dictionary or flat parameters
   - Timeseries mode uses flat parameters only
   - Mixed format (same parameter in both `params:` and top level) is invalid

5. **Connection validation:**
   - All referenced components must exist
   - Output names must be valid for source component
   - Input names must be valid for target component

6. **Circular dependency detection:**
   - Model must not contain circular dependencies
   - Use `LaggedValue` components to break cycles

7. **Disconnected component detection:**
   - All components should either provide or receive data
   - Warning issued for disconnected components

### Common Errors

**Missing required field:**
```
ConfigurationError: Missing required 'settings' block in model.yaml
```

**Invalid date:**
```
ConfigurationError: Invalid date format for start_date: '2020-13-01'.
Expected YYYY-MM-DD format.
```

**Missing climate configuration:**
```
ConfigurationError: Missing required 'climate' block in settings
```

**Invalid driver mode:**
```
ConfigurationError: Invalid driver mode 'invalid' for precipitation.
Must be 'stochastic' or 'timeseries'.
```

**Invalid params type:**
```
ConfigurationError: 'params' must be a dictionary, got str
```

**Mixed parameter format:**
```
ConfigurationError: Parameter 'mean_annual' specified both in 'params' and at top level.
Use either nested 'params:' format or flat format, not both.
```

**Missing component parameter:**
```
ConfigurationError: Component 'demand' of type 'Demand' is missing required
parameter 'population'. Required parameters for municipal mode: population, per_capita_demand_lpd
```

**Circular dependency:**
```
ValidationError: Circular dependency detected in component connections:
reservoir_a -> pump_b -> reservoir_c -> reservoir_a
```

**Invalid connection:**
```
ValidationError: Connection references undefined component 'bad_reservoir'.
Available components: catchment, main_reservoir, city_demand
```

---

## Best Practices

### File Organization

```
project/
├── models/
│   ├── baseline.yaml
│   ├── scenario_1.yaml
│   └── scenario_2.yaml
├── data/
│   ├── precip.csv
│   ├── temp.csv
│   └── precip_params.csv
└── results/
    ├── baseline/
    ├── scenario_1/
    └── scenario_2/
```

### Naming Conventions

- Use descriptive component names: `upper_mountain_catchment` not `c1`
- Use snake_case for component names: `main_reservoir` not `MainReservoir`
- Use consistent naming across models

### Comments

Add comments to document:
- Parameter sources (calibrated, literature, assumed)
- Model assumptions
- Component groupings

```yaml
components:
  # ========== CATCHMENTS ==========

  # Upper catchment with snow processes
  # Parameters calibrated to USGS gauge 12345678 (2015-2020)
  upper_catchment:
    type: Catchment
    area_km2: 150.0  # Drainage area from GIS analysis
    # ... parameters ...
```

### Version Control

- Track YAML files in git
- Use meaningful commit messages
- Don't track results or generated files

```bash
git add models/*.yaml
git commit -m "Add baseline model with calibrated catchment parameters"
```

---

## See Also

- [API Reference](API_REFERENCE.md) - Python API documentation
- [Component Reference](../COMPONENTS.md) - Component parameter details
- [Driver System](DRIVER_SYSTEM.md) - Climate driver documentation
- [Getting Started](../GETTING_STARTED.md) - Step-by-step tutorial
