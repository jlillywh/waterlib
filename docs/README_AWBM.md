# AWBM Component

The AWBM (Australian Water Balance Model) component implements the Boughton (2004) conceptual catchment hydrology model for waterlib.

## Overview

AWBM is a conceptual rainfall-runoff model that:
- Simulates partial area runoff using three surface moisture stores
- Splits overflow into baseflow and surface runoff components
- Routes flows through linear recession stores
- Operates on a daily timestep

This implementation follows the AWBM2002 self-calibrating version with hardcoded partial areas (A1=0.134, A2=0.433, A3=0.433).

## Configuration

### Required Parameters

- `area_km2`: Catchment area in square kilometers
- `precip_source`: Name of precipitation source component (mm/day)
- `pet_source`: Name of potential evapotranspiration source component (mm/day)
- `c_vec`: List of three capacity values [C1, C2, C3] in mm
- `bfi`: Baseflow Index (0-1), fraction of overflow to baseflow
- `ks`: Surface runoff recession constant (0-1)
- `kb`: Baseflow recession constant (0-1)

### Optional Parameters

- `initial_stores`: Initial state [SS1, SS2, SS3, S_surf, B_base] in mm (default: all zeros)

## Example YAML

```yaml
components:
  rainfall:
    type: Timeseries
    file: data/climate.csv
    column: precip_mm

  pet:
    type: Timeseries
    file: data/climate.csv
    column: pet_mm

  catchment:
    type: AWBM
    area_km2: 150.0
    precip_source: rainfall
    pet_source: pet
    c_vec: [7.5, 76.0, 152.0]  # Default AWBM2002 values
    bfi: 0.35
    ks: 0.35
    kb: 0.95

  reservoir:
    type: Reservoir
    initial_volume_m3: 5000000
    eav_table: data/reservoir_eav.csv
    inflows: [catchment.runoff_m3d]
```

## Outputs

- `runoff_m3d`: Total runoff in cubic meters per day
- `runoff_depth_mm`: Total runoff depth in mm
- `excess_mm`: Overflow from surface stores in mm
- `store_0` through `store_4`: Individual store states in mm
  - `store_0`: Surface store 1 (SS1)
  - `store_1`: Surface store 2 (SS2)
  - `store_2`: Surface store 3 (SS3)
  - `store_3`: Surface runoff routing store (S_surf)
  - `store_4`: Baseflow routing store (B_base)

## Parameter Guidance

### Surface Store Capacities (c_vec)

The three capacity values represent different soil moisture storage capacities across the catchment:
- **C1**: Shallow storage (default: 7.5 mm)
- **C2**: Medium storage (default: 76.0 mm)
- **C3**: Deep storage (default: 152.0 mm)

The default values [7.5, 76.0, 152.0] give an average capacity of 100 mm and are suitable for many Australian catchments.

### Baseflow Index (bfi)

Controls the split between surface runoff and baseflow:
- **0.0**: All overflow becomes surface runoff (flashy response)
- **0.5**: Equal split between surface and baseflow
- **1.0**: All overflow becomes baseflow (slow response)

Typical range: 0.2 - 0.5

### Recession Constants (ks, kb)

Control how quickly water is released from routing stores:
- **ks** (surface): Typically 0.2 - 0.5 (faster recession)
- **kb** (baseflow): Typically 0.8 - 0.95 (slower recession)

Higher values = slower recession (water stays in store longer)

## State Management

AWBM uses waterlib's two-pass execution model:

1. **Update pass**: Calculates runoff based on current state and inputs, stages new state
2. **Finalize pass**: Commits the staged state changes

This ensures consistent state across all components in each timestep.

## Unit Conversions

The AWBM algorithm operates in depth units (mm), but waterlib reservoirs expect volume (m³/day). The component automatically converts:

```
runoff_m3d = runoff_depth_mm × area_km2 × 1000
```

## References

- Boughton, W. (2004). The Australian water balance model. Environmental Modelling & Software, 19(10), 943-956.
- AWBM2002 self-calibrating version with standardized partial areas

## Integration with HargreavesET

AWBM can use the HargreavesET component to calculate PET from temperature data:

```yaml
components:
  tmin:
    type: Timeseries
    file: data/climate.csv
    column: tmin_c

  tmax:
    type: Timeseries
    file: data/climate.csv
    column: tmax_c

  rainfall:
    type: Timeseries
    file: data/climate.csv
    column: precip_mm

  pet_hargreaves:
    type: HargreavesET
    latitude_deg: -35.0
    tmin_source: tmin
    tmax_source: tmax

  catchment:
    type: AWBM
    area_km2: 150.0
    precip_source: rainfall
    pet_source: pet_hargreaves  # Uses HargreavesET output
    c_vec: [7.5, 76.0, 152.0]
    bfi: 0.35
    ks: 0.35
    kb: 0.95
```

The AWBM component automatically detects whether the PET source provides `value` (Timeseries) or `et0_mm` (HargreavesET) output.

## Example Usage

See the following examples for complete working demonstrations:
- `examples/awbm_example.yaml` - AWBM with Timeseries PET input
- `examples/awbm_with_hargreaves.yaml` - AWBM with HargreavesET PET calculation
- `examples/awbm_quickstart.py` - Basic AWBM simulation script
- `examples/awbm_hargreaves_example.py` - AWBM with Hargreaves ET simulation script
