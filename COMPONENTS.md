# Component Reference

Complete reference for all waterlib components with parameters, inputs, outputs, and examples.

## Table of Contents

1. [Catchment](#catchment)
2. [Reservoir](#reservoir)
3. [Pump](#pump)
4. [Demand](#demand)
5. [RiverDiversion](#riverdiversion)
6. [Junction](#junction)
7. [Weir](#weir)

---

## Catchment

Simulates rainfall-runoff processes with integrated snow accumulation/melt (Snow17) and water balance modeling (AWBM).

### Description

The Catchment component combines two well-established hydrological models:
- **Snow17**: Snow accumulation and ablation model (Anderson, 1973)
- **AWBM**: Australian Water Balance Model for rainfall-runoff (Boughton, 2004)

Snow17 processes precipitation into rain and snowmelt, which then feeds into AWBM for runoff generation. This integrated approach is ideal for catchments with seasonal snow cover.

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `area_km2` | float | Yes | km² | Catchment drainage area |
| `snow17_params` | dict | Yes | - | Snow17 model parameters (see below) |
| `awbm_params` | dict | Yes | - | AWBM model parameters (see below) |

#### Snow17 Parameters

| Parameter | Type | Default | Units | Description |
|-----------|------|---------|-------|-------------|
| `scf` | float | 1.0 | - | Snow correction factor (gauge undercatch) |
| `mfmax` | float | 1.5 | mm/°C/6hr | Maximum melt factor (June 21) |
| `mfmin` | float | 0.5 | mm/°C/6hr | Minimum melt factor (Dec 21) |
| `uadj` | float | 0.04 | mm/mb/6hr | Average wind function during rain-on-snow |
| `si` | float | 1000.0 | mm | Areal water equivalent above which 100% cover |
| `pxtemp` | float | 1.0 | °C | Temperature dividing rain from snow |
| `nmf` | float | 0.15 | mm/mb/6hr | Maximum negative melt factor |
| `tipm` | float | 0.1 | - | Antecedent temperature index parameter |
| `mbase` | float | 1.0 | °C | Base temperature for melt |
| `plwhc` | float | 0.04 | - | Percent liquid water holding capacity |
| `daygm` | float | 0.05 | mm/day | Daily ground melt |

#### AWBM Parameters

| Parameter | Type | Default | Units | Description |
|-----------|------|---------|-------|-------------|
| `c_vec` | list | [7.5, 76.0, 152.0] | mm | List of three capacity values [C1, C2, C3] |
| `bfi` | float | 0.35 | - | Baseflow Index (fraction of overflow to baseflow, 0-1) |
| `ks` | float | 0.35 | - | Surface runoff recession constant (0-1) |
| `kb` | float | 0.95 | - | Baseflow recession constant (0-1) |
| `initial_stores` | list | [0, 0, 0, 0, 0] | mm | Optional initial state [SS1, SS2, SS3, S_surf, B_base] |

**Note**: Partial area fractions (A1, A2, A3) are hard-coded to match AWBM2002 auto-calibration pattern: A1=0.134, A2=0.433, A3=0.433

### Inputs

Climate data from drivers:
- Precipitation [mm/day]
- Temperature [°C]
- ET (Evapotranspiration) [mm/day]

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `runoff_m3d` | m³/day | Total runoff volume |
| `snow_water_equivalent` | mm | Snow water equivalent |
| `runoff_depth_mm` | mm | Runoff depth |

### Example

```yaml
components:
  mountain_catchment:
    type: Catchment
    area_km2: 150.0
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
      c_vec: [7.5, 76.0, 152.0]
      bfi: 0.35
      ks: 0.35
      kb: 0.95
    meta:
      x: 0.5
      y: 0.8
      color: '#90EE90'
      label: 'Mountain Catchment'
```

### Notes

- Default AWBM parameters represent typical calibrated values
- Partial area fractions: A1=0.134, A2=0.433, A3=0.433
- For catchments without snow, omit `snow17_params` or set to `null`

---

## Reservoir

Models water storage with integrated spillway for passive overflow.

### Description

The Reservoir component simulates water storage using mass balance principles. It includes an integrated spillway that automatically activates when storage exceeds the spillway elevation. Evaporation losses are calculated based on surface area and evaporation data from climate drivers.

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `initial_storage` | float | Yes | m³ | Starting storage volume |
| `max_storage` | float | Yes | m³ | Maximum storage capacity |
| `surface_area` | float | No | m² | Water surface area (for simple mode evaporation) |
| `eav_table` | string | No | - | Path to EAV table CSV file (for EAV mode) |
| `spillway_elevation` | float | No | m | Spillway crest elevation |

### Inputs

| Input | Units | Description |
|-------|-------|-------------|
| `inflow` | m³/day | Incoming flow (from connected components) |
| `release` | m³/day | Controlled release (optional) |
| `evaporation` | mm/day | From climate drivers (optional) |

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `storage` | m³ | Current storage volume |
| `outflow` | m³/day | Total outflow (release + spill) |
| `spill` | m³/day | Spillway overflow |
| `evaporation_loss` | m³/day | Evaporation loss (if surface_area or eav_table) |
| `elevation` | m | Water surface elevation (EAV mode only) |
| `area` | m² | Water surface area (EAV mode only) |

### Example (Simple Mode)

```yaml
components:
  main_reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    surface_area: 500000
    spillway_elevation: 245.0
    meta:
      x: 0.5
      y: 0.5
      color: '#4169E1'
      label: 'Main Reservoir'

connections:
  - from: catchment.runoff_m3d
    to: main_reservoir.inflow
  - from: upstream_river.flow_m3d
    to: main_reservoir.inflow
```

### Example (EAV Mode)

```yaml
components:
  main_reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    eav_table: data/reservoir_eav.csv
    spillway_elevation: 245.0
    meta:
      x: 0.5
      y: 0.5
      color: '#4169E1'
      label: 'Main Reservoir'
```

### Notes

- Two modes: Simple (constant surface_area) or EAV (elevation-area-volume table)
- EAV mode provides realistic elevation and area tracking
- Spillway activates automatically when storage exceeds spillway elevation
- Evaporation calculated from climate drivers when surface_area or eav_table provided

---
- Spillway activates automatically when storage exceeds max_storage
- Evaporation is calculated as: `evap_volume = surface_area * evaporation_rate / 1000`
- Storage cannot exceed `max_storage` (excess goes to spill)
- Storage cannot go below zero (release is reduced if insufficient water)

---

## Pump

Feedback-controlled flow component with deadband or proportional control.

### Description

The Pump component monitors a process variable (typically reservoir depth/elevation) and adjusts flow to maintain a target value. The target can vary seasonally via a lookup table with linear interpolation.

Control Modes:
- **Deadband (ON/OFF)**: Pump operates at full capacity when error exceeds deadband
- **Proportional**: Flow is proportional to error (Flow = Kp × error)

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `control_mode` | string | Yes | - | 'deadband' or 'proportional' |
| `capacity` | float | Yes | m³/day | Maximum flow rate |
| `process_variable` | string | Yes | - | Component output to monitor (format: "component.output") |
| `target` | float or dict | Yes | varies | Fixed target value or seasonal lookup table |
| `deadband` | float | No* | varies | Deadband threshold (deadband mode) |
| `kp` | float | No* | - | Proportional gain coefficient (proportional mode) |

*Required for respective control mode

### Inputs

| Input | Units | Description |
|-------|-------|-------------|
| `process_variable` | varies | Monitored value (e.g., reservoir.storage or reservoir.elevation) |

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `pumped_flow` | m³/day | Controlled flow |
| `error` | varies | Control error (target - current) for diagnostics |
| `target_value` | varies | Current target value for diagnostics |

### Example (Deadband Mode with Constant Target)

```yaml
components:
  pump_1:
    type: Pump
    control_mode: 'deadband'
    capacity: 50000
    process_variable: 'main_reservoir.elevation'
    target: 100.0
    deadband: 2.0
    meta:
      x: 0.6
      y: 0.3
      color: '#FF8C00'
      label: 'Pump Station'
```

### Example (Proportional Mode with Seasonal Target)

```yaml
components:
  pump_2:
    type: Pump
    control_mode: 'proportional'
    capacity: 50000
    process_variable: 'main_reservoir.storage'
    target:
      1: 1000000    # Jan 1: 1,000,000 m³
      182: 1500000  # Jul 1: 1,500,000 m³
      365: 1000000  # Dec 31: 1,000,000 m³
    kp: 0.1
    meta:
      x: 0.6
      y: 0.3
      color: '#FF8C00'
      label: 'Variable Pump'
```

### Notes

- Deadband mode: Pump turns ON at full capacity when error > deadband, OFF otherwise
- Proportional mode: Flow = kp × (target - current), clamped to [0, capacity]
- Seasonal targets use linear interpolation between day-of-year points
- Process variable can be any component output (storage, elevation, flow, etc.)
- Use LaggedValue component for feedback control to avoid circular dependencies

---

## Demand

Water extraction component with municipal or agricultural modes.

### Description

The Demand component simulates water extraction with two modes:
- **Municipal mode**: Calculates demand based on population and per capita consumption
- **Agricultural mode**: Calculates demand based on irrigated area, crop coefficient, and PET

The component tracks supplied water and deficit (unmet demand).

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `source` | string | Yes | - | Source component name |
| `mode` | string | Yes | - | 'municipal' or 'agricultural' |

**Municipal Mode Parameters:**

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `population` | int | Yes | people | Population served |
| `per_capita_demand_lpd` | float | Yes | L/person/day | Per capita water demand |

**Agricultural Mode Parameters:**

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `irrigated_area_ha` | float | Yes | hectares | Irrigated area |
| `crop_coefficient` | float | Yes | - | Crop coefficient (Kc) |

### Inputs

| Input | Units | Description |
|-------|-------|-------------|
| `available_supply` | m³/day | Available water from source |
| ET | mm/day | From climate drivers (agricultural mode only) |

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `demand` | m³/day | Calculated water demand |
| `supplied` | m³/day | Actually supplied water |
| `deficit` | m³/day | Unmet demand |

### Example (Municipal)

```yaml
components:
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

### Example (Agricultural)

```yaml
components:
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
      label: 'Farm Irrigation'
```

### Notes

- Municipal demand calculation: `demand = population * per_capita_demand_lpd / 1000`
- Agricultural demand calculation: `demand = irrigated_area_ha * 10000 * pet_mmd * crop_coefficient / 1000`
- Supplied water cannot exceed available supply
- Deficit is calculated as: `deficit = demand - supplied`

---

## RiverDiversion

Priority-based flow diversion from a river or stream.

### Description

The RiverDiversion component models a diversion structure that allocates water to multiple destinations based on priority order. It supports instream flow requirements (environmental flows) and multiple outflows with individual priorities and demands.

Water is allocated in priority order (lower number = higher priority):
1. Instream flow requirement is satisfied first
2. Remaining flow is allocated to outflows by priority
3. Each outflow receives up to its demand, if available
4. Unallocated flow continues downstream

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `max_diversion` | float | Yes | m³/day | Maximum total diversion rate |
| `instream_flow` | float | No | m³/day | Minimum flow that must remain in river (default: 0) |
| `outflows` | list | No | - | List of outflow destinations with priority and demand |

**Outflows Format** (if specified):
```yaml
outflows:
  - name: "canal_a"
    priority: 1
    demand: 5000
  - name: "canal_b"
    priority: 2
    demand: 3000
```

### Inputs

| Input | Units | Description |
|-------|-------|-------------|
| `river_flow` | m³/day | Available river flow |

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `diverted_flow` | m³/day | Total flow extracted from river |
| `remaining_flow` | m³/day | Flow continuing downstream |
| `instream_flow` | m³/day | Flow allocated to instream requirement |
| `{outflow_name}` | m³/day | Individual outflow (if outflows specified) |
| `{outflow_name}_deficit` | m³/day | Unmet demand for each outflow |

### Example (Simple with Instream Flow)

```yaml
components:
  river_diversion:
    type: RiverDiversion
    max_diversion: 10000
    instream_flow: 2000
    meta:
      x: 0.7
      y: 0.6
      color: '#32CD32'
      label: 'River Diversion'

connections:
  - from: river_junction.outflow
    to: river_diversion.river_flow
```

### Example (Priority-Based Allocation)

```yaml
components:
  priority_diversion:
    type: RiverDiversion
    max_diversion: 15000
    instream_flow: 3000
    outflows:
      - name: municipal
        priority: 1
        demand: 5000
      - name: irrigation
        priority: 2
        demand: 8000
      - name: industrial
        priority: 3
        demand: 2000
    meta:
      x: 0.7
      y: 0.6
      color: '#32CD32'
      label: 'Priority Diversion'

connections:
  - from: river_junction.outflow
    to: priority_diversion.river_flow
  - from: priority_diversion.municipal
    to: city_demand.available_supply
  - from: priority_diversion.irrigation
    to: farm_demand.available_supply
```

### Notes

- Instream flow requirement has highest priority (satisfied first)
- Outflows are allocated in priority order (lower number = higher priority)
- Each outflow receives up to its demand, limited by available flow
- Deficits are tracked for each outflow when demand exceeds available water
- If no outflows specified, creates single `diverted_flow` output up to max_diversion

---

## Junction

Aggregates multiple flows into a single outflow.

### Description

The Junction component is a simple aggregator that sums multiple inflows into a single outflow. It's useful for combining flows from multiple sources (e.g., multiple catchments, tributary confluence).

This is a stateless component that simply aggregates flows at each timestep.

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| None | - | - | - | Pure aggregation component (no parameters) |

### Inputs

Multiple inflow inputs dynamically named through connections (e.g., inflow_1, inflow_2, ...)

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `outflow` | m³/day | Sum of all inflows |

### Example

```yaml
components:
  # Aggregate catchment flows
  confluence:
    type: Junction
    meta:
      x: 0.5
      y: 0.7
      color: '#4682B4'
      label: 'River Confluence'

connections:
  - from: tributary_a.runoff
    to: confluence.inflow_1
  - from: tributary_b.runoff
    to: confluence.inflow_2
  - from: tributary_c.runoff
    to: confluence.inflow_3
```

### Notes

- Junction performs simple summation: `outflow = sum(all inputs)`
- No limit on number of inflows
- Inputs are dynamically named through the connection system
- Useful for creating measurement points in the model
- Can be used to aggregate flows before diversion or storage

---

## Weir

Passive overflow structure using weir equation.

### Description

The Weir component models passive overflow structures using the weir equation to calculate discharge based on upstream water elevation. It monitors a control source (typically a Reservoir) and calculates discharge using the standard weir equation for rectangular sharp-crested weirs.

The weir equation:
```
Q = C × L × H^(3/2)
```
Where:
- Q = discharge (m³/s)
- C = discharge coefficient
- L = weir width (m)
- H = head over crest (m)

### Parameters

| Parameter | Type | Required | Units | Description |
|-----------|------|----------|-------|-------------|
| `control_source` | string | Yes | - | Name of reservoir component to monitor |
| `crest_elevation_m` | float | Yes | m | Weir crest elevation |
| `coefficient` | float | Yes | - | Discharge coefficient (typically 1.5-2.0) |
| `width_m` | float | Yes | m | Weir width |
| `source` | string | No | - | Water source component (defaults to control_source) |

### Inputs

| Input | Units | Description |
|-------|-------|-------------|
| `elevation` | m | Water surface elevation from control_source |

### Outputs

| Output | Units | Description |
|--------|-------|-------------|
| `discharge_m3d` | m³/day | Weir discharge |

### Example

```yaml
components:
  main_reservoir:
    type: Reservoir
    initial_storage: 2000000
    max_storage: 5000000
    eav_table: data/reservoir_eav.csv

  spillway:
    type: Weir
    control_source: main_reservoir
    crest_elevation_m: 245.0
    coefficient: 1.8
    width_m: 20.0
    meta:
      x: 0.6
      y: 0.4
      color: '#FF4500'
      label: 'Spillway'
```

### Notes

- Discharge is calculated only when head over crest (H) is positive
- Discharge coefficient typically ranges from 1.5 to 2.0 for sharp-crested weirs
- The component automatically withdraws calculated discharge from the source
- If source is not specified, control_source is used as the water source
- Weir provides passive overflow control (no active regulation)

---

## Component Selection Guide

### When to Use Each Component

| Component | Use When... |
|-----------|-------------|
| **Catchment** | You need to simulate rainfall-runoff with snow processes |
| **Reservoir** | You need water storage with mass balance tracking |
| **Pump** | You need feedback-controlled flow based on process variable |
| **Demand** | You need to model water extraction (municipal or agricultural) |
| **RiverDiversion** | You need priority-based allocation from a river |
| **Junction** | You need to combine multiple flows |
| **Weir** | You need passive overflow based on elevation |

### Common Component Combinations

**Catchment → Reservoir → Demand**
```
Basic water supply system with storage
```

**Multiple Catchments → Junction → Reservoir**
```
Multiple tributaries feeding a reservoir
```

**Reservoir → Pump → Demand**
```
Pumped water supply system
```

**River → Diversion → Demand (agricultural)**
```
Irrigation from river diversion
```

**Reservoir → Weir (spillway) + Demand → Junction**
```
Reservoir with both controlled release and passive overflow
```

**Reservoir → Pump (feedback control)**
```
Pumped water supply with level control
```

### Parameter Tuning Tips

**Catchment:**
- Start with default AWBM parameters (`c_vec: [7.5, 76.0, 152.0]`)
- Adjust `scf` (snow correction factor) if snow accumulation seems too low/high
- Adjust `mfmax` (melt factor) if snowmelt timing is off
- Calibrate to observed streamflow if available

**Reservoir:**
- Set `initial_storage` to typical operating level
- Use EAV mode for realistic elevation tracking with variable surface area
- Set `spillway_elevation` below max_storage to allow for flood storage
- Ensure `surface_area` is representative for evaporation calculations (simple mode)

**Pump:**
- For deadband mode, set deadband to acceptable error tolerance
- For proportional mode, tune `kp` to avoid oscillations
- Start with small kp values (e.g., 0.0001) and increase if response is too slow
- Use seasonal targets for varying operational requirements

**Demand:**
- Municipal: Use local per capita consumption rates (typically 150-300 L/person/day)
- Agricultural: Use crop-specific Kc values (0.3-1.2 depending on crop and growth stage)

**RiverDiversion:**
- Set `max_diversion` to water right or physical capacity
- Set `instream_flow` to meet environmental flow requirements
- Use priority-based outflows for complex allocation scenarios

**Junction:**
- No parameters to tune - just ensure all inflows are correctly connected

**Weir:**
- Use discharge coefficient of 1.8-2.0 for sharp-crested weirs
- Set `crest_elevation_m` to desired spillway elevation
- Width should match physical weir dimensions

---

## Advanced Topics

### Component Interactions

Components interact through their inputs and outputs. Understanding these interactions is key to building correct models.

**Example: Catchment → Reservoir → Demand**

```yaml
components:
  catchment:
    type: Catchment
    # ... parameters ...
    # Output: runoff_m3d

  reservoir:
    type: Reservoir
    inflows:
      - catchment.runoff_m3d  # Receives catchment output
    # Output: storage, outflow

  demand:
    type: Demand
    source: reservoir  # Receives from reservoir
    # Output: supplied, deficit
```

### State Management

Some components maintain internal state across timesteps:

- **Catchment**: Snow water equivalent, soil moisture stores
- **Reservoir**: Storage volume
- **Pump (variable)**: Control state

State is automatically managed by the simulation engine.

### Error Handling

All components validate their parameters during initialization and provide clear error messages:

```python
ConfigurationError: Component 'demand' of type 'Demand' is missing required
parameter 'population'. Required parameters for municipal mode: population, per_capita_demand_lpd
```

Common validation checks:
- Required parameters present
- Parameter types correct
- Parameter values in valid ranges
- Referenced components exist

### Performance Considerations

- **Catchment**: Most computationally intensive (Snow17 + AWBM calculations)
- **Reservoir**: Moderate (mass balance + spillway calculations)
- **Other components**: Lightweight (simple calculations)

For large models or long simulations:
- Consider simplifying catchment representation if snow processes aren't critical
- Use constant pump mode instead of variable if control isn't necessary
- Aggregate small catchments into larger units

---

## See Also

- [Getting Started Guide](GETTING_STARTED.md) - Step-by-step tutorial
- [README](README.md) - Main documentation
- [Examples](examples/) - Working example models
