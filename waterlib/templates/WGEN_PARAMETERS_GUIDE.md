# WGEN Parameter Guide

## Overview

This guide explains how to configure and use the WGEN (Weather Generator) stochastic weather simulation in waterlib. WGEN generates synthetic daily weather data (precipitation, temperature, and solar radiation) based on monthly precipitation parameters and constant temperature/radiation parameters with Fourier-based seasonal variation.

## Quick Start

1. Copy `wgen_params_template.csv` to your project's data directory
2. Modify the monthly precipitation parameters to match your location's climate
3. Configure your YAML file with constant temperature/radiation parameters and latitude
4. Run your simulation

## Parameter Structure Overview

WGEN uses two distinct types of parameters:

1. **Monthly Precipitation Parameters**: 12 values (one per month) for PWW, PWD, ALPHA, and BETA
2. **Constant Temperature/Radiation Parameters**: Single scalar values that remain constant throughout the year

The system uses **Fourier functions** with latitude to simulate realistic seasonal variations in temperature and solar radiation, eliminating the need for monthly temperature/radiation parameters.

## Parameter Files

### 1. Monthly Precipitation Parameters (CSV File)

The CSV file contains precipitation parameters that vary by month. It must have exactly 12 rows (one per month) with the following columns:

| Column | Description | Units | Valid Range | Notes |
|--------|-------------|-------|-------------|-------|
| `Month` | Month name or number | - | Jan-Dec or 1-12 | For reference only |
| `PWW` | Probability of wet day following wet day | dimensionless | 0-1 | Higher = longer wet spells |
| `PWD` | Probability of wet day following dry day | dimensionless | 0-1 | Higher = more frequent rain events |
| `ALPHA` | Gamma distribution shape parameter | dimensionless | > 0 | Controls precipitation distribution shape |
| `BETA` | Gamma distribution scale parameter | mm | > 0 | Controls precipitation amount scale |

**Key Relationship:** Mean precipitation per wet day ≈ `ALPHA × BETA` mm

**Example CSV Format:**
```csv
Month,PWW,PWD,ALPHA,BETA
Jan,0.493,0.248,0.860,3.865
Feb,0.454,0.252,0.897,3.956
Mar,0.461,0.248,0.945,4.828
Apr,0.541,0.228,0.834,6.446
May,0.535,0.180,0.830,6.170
Jun,0.470,0.112,0.760,5.743
Jul,0.363,0.105,0.691,5.648
Aug,0.351,0.135,0.720,5.035
Sep,0.432,0.130,0.677,7.387
Oct,0.505,0.128,0.836,6.190
Nov,0.474,0.191,0.817,5.116
Dec,0.480,0.237,0.849,4.253
```

### 2. Constant Temperature and Radiation Parameters (YAML Configuration)

These parameters remain constant throughout the year and are specified in your YAML configuration file. The system uses Fourier functions with these constants to generate realistic seasonal patterns.

#### Required Location Parameter

| Parameter | Description | Units | Valid Range | Example |
|-----------|-------------|-------|-------------|---------|
| `latitude` | Station latitude | degrees | -90 to 90 | 40.76 |

**Note:** Latitude is critical for Fourier-based seasonal calculations. Positive values are Northern Hemisphere, negative values are Southern Hemisphere.

#### Required Temperature Parameters

All temperature parameters are specified in **Celsius** at the interface level. The system internally converts to Kelvin for calculations.

| Parameter | Description | Units | Example | Notes |
|-----------|-------------|-------|---------|-------|
| `txmd` | Mean maximum temperature on dry days | °C | 18.5 | Base temperature for dry days |
| `atx` | Amplitude of maximum temperature seasonal variation | °C | 15.1 | Controls seasonal swing in Tmax |
| `txmw` | Mean maximum temperature on wet days | °C | 15.3 | Typically 1-3°C lower than txmd |
| `tn` | Mean minimum temperature | °C | 4.8 | Base minimum temperature |
| `atn` | Amplitude of minimum temperature seasonal variation | °C | 11.7 | Controls seasonal swing in Tmin |
| `cvtx` | Coefficient of variation for Tmax mean | dimensionless | 0.01675 | Stochastic variability |
| `acvtx` | Coefficient of variation for Tmax amplitude | dimensionless | -0.00383 | Seasonal CV variation |
| `cvtn` | Coefficient of variation for Tmin mean | dimensionless | 0.01605 | Stochastic variability |
| `acvtn` | Coefficient of variation for Tmin amplitude | dimensionless | -0.00345 | Seasonal CV variation |

#### Required Solar Radiation Parameters

Solar radiation parameters are specified in **MJ/m²/day**.

| Parameter | Description | Units | Example | Notes |
|-----------|-------------|-------|---------|-------|
| `rmd` | Mean solar radiation on dry days | MJ/m²/day | 12.9 | Base radiation for dry days |
| `ar` | Amplitude of solar radiation seasonal variation | MJ/m²/day | 10.2 | Controls seasonal swing |
| `rmw` | Mean solar radiation on wet days | MJ/m²/day | 12.9 | Typically 70-80% of rmd |

#### Optional Parameters

| Parameter | Description | Units | Default |
|-----------|-------------|-------|---------|
| `random_seed` | Random seed for reproducibility | integer | None (random) |

## Fourier-Based Seasonal Variation

The WGEN kernel uses **Fourier functions** to simulate realistic seasonal patterns in temperature and solar radiation. This approach eliminates the need for monthly temperature/radiation parameters while maintaining physical realism.

### How It Works

For temperature:
```
T(day) = mean + amplitude × cos(2π × (day_of_year - peak_day) / 365)
```

For solar radiation:
```
R(day) = mean + amplitude × cos(2π × (day_of_year - peak_day) / 365)
```

### Peak Day Calculation

The peak day (warmest/highest radiation day) is automatically calculated based on latitude:

- **Northern Hemisphere** (latitude ≥ 0):
  - Temperature peak: ~day 200 (mid-July)
  - Radiation peak: ~day 172 (summer solstice)

- **Southern Hemisphere** (latitude < 0):
  - Temperature peak: ~day 20 (mid-January)
  - Radiation peak: ~day 355 (summer solstice)

### Benefits of This Approach

1. **Fewer parameters**: Only 13 constants instead of 12 monthly values for each variable
2. **Smooth transitions**: No abrupt changes between months
3. **Physical realism**: Follows natural sinusoidal patterns
4. **Latitude-aware**: Automatically adjusts for hemisphere and latitude effects

## Example YAML Configuration

### Full WGEN Configuration

```yaml
wgen_config:
  # Monthly precipitation parameters (CSV file)
  param_file: "data/wgen_params.csv"

  # Location (required for Fourier calculations)
  latitude: 40.76  # degrees, -90 to 90

  # Temperature parameters (Celsius at interface)
  txmd: 18.5    # Mean max temp on dry days (°C)
  atx: 15.1     # Amplitude of max temp seasonal variation (°C)
  txmw: 15.3    # Mean max temp on wet days (°C)
  tn: 4.8       # Mean min temp (°C)
  atn: 11.7     # Amplitude of min temp seasonal variation (°C)
  cvtx: 0.01675   # Coefficient of variation for Tmax mean
  acvtx: -0.00383 # Coefficient of variation for Tmax amplitude
  cvtn: 0.01605   # Coefficient of variation for Tmin mean
  acvtn: -0.00345 # Coefficient of variation for Tmin amplitude

  # Solar radiation parameters (MJ/m²/day)
  rmd: 12.9     # Mean solar radiation on dry days
  ar: 10.2      # Amplitude of solar radiation seasonal variation
  rmw: 12.9     # Mean solar radiation on wet days

  # Optional: Random seed for reproducibility
  random_seed: 42
```

### Minimal Configuration (Using Defaults)

If you only have precipitation data and basic temperature information:

```yaml
wgen_config:
  # Required
  param_file: "data/wgen_params.csv"
  latitude: 40.76

  # Minimum temperature parameters
  txmd: 18.5
  atx: 15.1
  txmw: 15.3
  tn: 4.8
  atn: 11.7
  cvtx: 0.01675
  acvtx: -0.00383
  cvtn: 0.01605
  acvtn: -0.00345

  # Minimum radiation parameters
  rmd: 12.9
  ar: 10.2
  rmw: 12.9
```

### Southern Hemisphere Example

For a location in the Southern Hemisphere (e.g., Sydney, Australia):

```yaml
wgen_config:
  param_file: "data/sydney_wgen_params.csv"

  # Negative latitude for Southern Hemisphere
  latitude: -33.87

  # Temperature parameters (note: seasons are reversed)
  txmd: 22.3    # Warmer dry days
  atx: 8.5      # Smaller seasonal variation (coastal)
  txmw: 19.8    # Cooler wet days
  tn: 13.5      # Mild minimum temperatures
  atn: 6.2      # Smaller seasonal variation
  cvtx: 0.015
  acvtx: -0.003
  cvtn: 0.014
  acvtn: -0.003

  # Solar radiation
  rmd: 18.5     # Higher radiation (lower latitude)
  ar: 8.0       # Seasonal variation
  rmw: 14.8     # Reduced on wet days
```

## Parameter Estimation from Historical Data

To estimate WGEN parameters from your own historical weather data, use the provided parameter estimation utility or follow these steps:

### Using the Parameter Estimator Tool

The easiest way to estimate parameters is using the built-in tool:

```bash
python waterlib/templates/wgen_parameter_estimator.py \
  --input historical_weather.csv \
  --output wgen_params.csv \
  --latitude 40.76
```

This will generate both:
1. A CSV file with monthly precipitation parameters
2. A YAML snippet with constant temperature/radiation parameters

### Manual Estimation

If you prefer to estimate parameters manually:

#### 1. Monthly Precipitation Parameters

For each month (12 values each):

1. **Calculate transition probabilities:**
   - `PWW` = (# of wet days following wet days) / (# of wet days)
   - `PWD` = (# of wet days following dry days) / (# of dry days)
   - A day is "wet" if precipitation > 0.254 mm (or your local threshold)

2. **Fit gamma distribution to wet day amounts:**
   - Use method of moments or maximum likelihood estimation
   - `ALPHA` (shape) and `BETA` (scale) parameters
   - Most statistical software (R, Python scipy) can fit gamma distributions

**Example Python code:**
```python
from scipy import stats
import pandas as pd

# For each month
monthly_precip = df[df['month'] == month_num]['precip']
wet_days = monthly_precip[monthly_precip > 0.254]

# Fit gamma distribution
shape, loc, scale = stats.gamma.fit(wet_days, floc=0)
alpha = shape
beta = scale
```

#### 2. Constant Temperature Parameters

These are **single values** (not monthly), estimated from the entire dataset:

1. **Separate data by wet/dry days:**
   - Dry days: precipitation ≤ 0.254 mm
   - Wet days: precipitation > 0.254 mm

2. **Calculate mean temperatures:**
   - `txmd` = mean of Tmax on dry days (all months combined)
   - `txmw` = mean of Tmax on wet days (all months combined)
   - `tn` = mean of Tmin (all days, all months)

3. **Fit Fourier series to seasonal pattern:**
   - Fit a cosine function to daily Tmax: `Tmax(day) = mean + amplitude × cos(2π(day - peak)/365)`
   - `atx` = amplitude of Tmax seasonal variation
   - `atn` = amplitude of Tmin seasonal variation
   - Peak day is automatically determined by latitude (no need to estimate)

4. **Calculate coefficients of variation:**
   - `cvtx` = std(Tmax) / mean(Tmax) across all days
   - `cvtn` = std(Tmin) / mean(Tmin) across all days
   - `acvtx`, `acvtn` = amplitude of CV seasonal variation (fit Fourier to daily CV values)

**Example Python code:**
```python
import numpy as np
from scipy.optimize import curve_fit

# Mean temperatures
txmd = df[df['precip'] <= 0.254]['tmax'].mean()
txmw = df[df['precip'] > 0.254]['tmax'].mean()
tn = df['tmin'].mean()

# Fit Fourier for amplitude
def fourier(day, mean, amplitude, peak):
    return mean + amplitude * np.cos(2 * np.pi * (day - peak) / 365)

days = df['day_of_year'].values
tmax_values = df['tmax'].values

# Fit to get amplitude (fix peak based on latitude)
peak_day = 200 if latitude >= 0 else 20
popt, _ = curve_fit(lambda d, m, a: fourier(d, m, a, peak_day),
                    days, tmax_values, p0=[txmd, 15])
atx = popt[1]
```

#### 3. Constant Solar Radiation Parameters

These are **single values** (not monthly):

1. **Separate by wet/dry days:**
   - `rmd` = mean solar radiation on dry days (all months)
   - `rmw` = mean solar radiation on wet days (all months)

2. **Fit Fourier series for seasonal pattern:**
   - Fit cosine function to daily radiation values
   - `ar` = amplitude of solar radiation seasonal variation

**Example Python code:**
```python
# Mean radiation by wet/dry
rmd = df[df['precip'] <= 0.254]['solar'].mean()
rmw = df[df['precip'] > 0.254]['solar'].mean()

# Fit Fourier for amplitude
peak_day = 172 if latitude >= 0 else 355  # Summer solstice
popt, _ = curve_fit(lambda d, m, a: fourier(d, m, a, peak_day),
                    days, df['solar'].values, p0=[rmd, 10])
ar = popt[1]
```

## Units Summary

The WGEN interface uses the following units:

| Parameter Type | Unit | Notes |
|----------------|------|-------|
| **Temperature** | Celsius (°C) | Converted to Kelvin internally for calculations |
| **Precipitation (BETA)** | Millimeters (mm) | Scale parameter for gamma distribution |
| **Solar Radiation** | MJ/m²/day | Megajoules per square meter per day |
| **Probabilities (PWW, PWD)** | Dimensionless | Range: 0 to 1 |
| **Shape (ALPHA)** | Dimensionless | Must be > 0 |
| **Latitude** | Degrees | Range: -90 to 90 |

### Temperature Unit Handling

**Important:** Temperature parameters are specified in **Celsius** at the interface level. The WGEN kernel automatically converts these to Kelvin for internal calculations, then converts outputs back to Celsius. You never need to work with Kelvin directly.

```python
# You provide parameters in Celsius
params = WGENParams(
    txmd=18.5,  # Celsius
    tn=4.8,     # Celsius
    # ... other params
)

# Outputs are also in Celsius
outputs = wgen_step(params, state)
print(outputs.tmax_c)  # Celsius
print(outputs.tmin_c)  # Celsius
```

## Unit Conversions

### CRITICAL: Legacy Data Migration

If you are converting parameters from legacy WGEN datasets (which may use imperial units), you **MUST** perform these conversions:

#### Temperature Conversion (Fahrenheit to Celsius)
```
Celsius = (Fahrenheit - 32) × 5/9
```

Example:
- 65°F → (65 - 32) × 5/9 = 18.3°C

**Apply to:** txmd, atx, txmw, tn, atn

#### Precipitation Beta Conversion (Inches to Millimeters)
```
BETA_mm = BETA_inches × 25.4
```

Example:
- BETA = 0.3098 inches → 0.3098 × 25.4 = 7.869 mm

**This is the most critical conversion!** Forgetting this will make your simulation generate desert-level rainfall.

#### Solar Radiation Conversion (Langleys to MJ/m²/day)
```
MJ/m²/day = Langleys × 0.04184
```

Example:
- 400 Langleys → 400 × 0.04184 = 16.7 MJ/m²/day

**Apply to:** rmd, ar, rmw

### Validation Checklist

After setting up or converting parameters, verify:

**Monthly Precipitation Parameters (CSV file):**
- [ ] CSV file has exactly 12 rows (one per month)
- [ ] All required columns present: Month, PWW, PWD, ALPHA, BETA
- [ ] PWW values are between 0 and 1
- [ ] PWD values are between 0 and 1
- [ ] ALPHA values are > 0
- [ ] BETA values are > 0
- [ ] BETA values are in the range 3-15 mm for typical climates (not 0.1-0.5)
- [ ] Mean precipitation per wet day (ALPHA × BETA) is 3-20 mm for your location

**Constant Temperature Parameters (YAML):**
- [ ] Temperature parameters are in Celsius (check if values are reasonable: -20 to 40°C)
- [ ] txmd is 1-3°C higher than txmw (wet days are cooler)
- [ ] atx and atn are 5-20°C for typical mid-latitude locations
- [ ] CV values (cvtx, cvtn) are small positive numbers (typically 0.01-0.05)
- [ ] ACV values (acvtx, acvtn) are small numbers (typically -0.01 to 0.01)

**Constant Radiation Parameters (YAML):**
- [ ] Radiation values are in MJ/m²/day (typically 10-25 for mid-latitudes)
- [ ] rmd and rmw are positive
- [ ] ar is positive and less than rmd
- [ ] rmw is typically 70-90% of rmd (wet days have less radiation)

**Location Parameter:**
- [ ] Latitude is between -90 and 90 degrees
- [ ] Latitude sign is correct (positive = Northern Hemisphere, negative = Southern Hemisphere)

## Sanity Checks

### Precipitation (Monthly Parameters)
- Mean annual precipitation ≈ 365 × mean(PWD) × mean(ALPHA × BETA)
- Should be within 20% of known annual precipitation for your location
- Typical values: 400-1200 mm/year for temperate climates
- PWW should generally be higher than PWD (wet days tend to cluster)
- ALPHA × BETA should give reasonable daily precipitation amounts (3-20 mm for temperate climates)

### Temperature (Constant Parameters)
- `txmd` should be 1-3°C higher than `txmw` (wet days are cooler due to cloud cover)
- `atx` and `atn` should be 5-20°C for mid-latitudes (larger at continental interiors, smaller at coasts)
- `tn` should be lower than both `txmd` and `txmw` (minimum < maximum)
- Coefficient of variation values (cvtx, cvtn) should be small (0.01-0.05)
- Temperature ranges should make sense for your location:
  - Tropical: txmd ~30-35°C, tn ~20-25°C, small amplitudes (5-10°C)
  - Temperate: txmd ~15-25°C, tn ~5-15°C, medium amplitudes (10-20°C)
  - Continental: txmd ~10-30°C, tn ~-10-10°C, large amplitudes (15-30°C)

### Solar Radiation (Constant Parameters)
- `rmd` should be 10-25 MJ/m²/day for mid-latitudes (higher at lower latitudes)
- `ar` should be positive and less than `rmd` (typically 30-50% of rmd)
- `rmw` should be 70-90% of `rmd` (wet days have less radiation due to clouds)
- All radiation values must be positive

### Latitude
- Must be between -90 and 90 degrees
- Sign matters: positive = Northern Hemisphere, negative = Southern Hemisphere
- Affects Fourier peak days automatically (no manual adjustment needed)

## Troubleshooting

### Problem: Simulation generates very little precipitation

**Likely Cause:** BETA values are in inches instead of millimeters

**Solution:** Multiply all BETA values in your CSV file by 25.4

**Check:** Calculate ALPHA × BETA for each month. Should be 3-20 mm for typical climates, not 0.1-1.0.

**Example:**
```
Wrong: BETA = 0.3 (inches) → ALPHA × BETA = 0.26 mm/day (too low!)
Right: BETA = 7.6 (mm) → ALPHA × BETA = 6.6 mm/day (reasonable)
```

### Problem: Temperatures are unrealistic (too high or too low)

**Likely Cause:** Temperature parameters are in Fahrenheit instead of Celsius

**Solution:** Convert all temperature parameters in your YAML: `C = (F - 32) × 5/9`

**Check:** Verify txmd, txmw, tn are in reasonable range for your location in Celsius:
- Tropical: 20-35°C
- Temperate: 10-25°C
- Cold: -10-15°C

**Example:**
```
Wrong: txmd = 65 (Fahrenheit) → unrealistically hot in Celsius context
Right: txmd = 18.3 (Celsius) → reasonable for temperate climate
```

### Problem: Seasonal patterns are reversed (hot in winter, cold in summer)

**Likely Cause:** Latitude sign is incorrect

**Solution:** Check your latitude value:
- Northern Hemisphere: positive latitude (e.g., 40.76 for New York)
- Southern Hemisphere: negative latitude (e.g., -33.87 for Sydney)

**Check:** Run a full year simulation and verify temperature peaks occur in the correct season.

### Problem: No seasonal variation in temperature/radiation

**Likely Cause:** Amplitude parameters (atx, atn, ar) are too small or zero

**Solution:** Check that amplitude values are reasonable:
- atx, atn: typically 5-20°C for mid-latitudes
- ar: typically 30-50% of rmd

**Check:** Plot generated temperature/radiation over a full year to verify seasonal patterns.

### Problem: Solar radiation is always zero or negative

**Likely Cause:** Radiation parameters are in wrong units or negative

**Solution:**
1. Check that rmd, ar, rmw are all positive
2. Verify units are MJ/m²/day (not Langleys or W/m²)
3. If converting from Langleys: multiply by 0.04184

**Check:** Typical values are 10-25 MJ/m²/day for mid-latitudes.

### Problem: Results are not reproducible

**Likely Cause:** Random seed is not set

**Solution:** Add `random_seed: 42` (or any integer) to your YAML configuration

**Check:** Run the simulation twice with the same seed - results should be identical.

### Problem: Validation error about list lengths

**Likely Cause:** CSV file doesn't have exactly 12 rows

**Solution:** Ensure your CSV file has one row for each month (January through December)

**Check:** Open the CSV file and count rows (excluding header).

### Problem: Validation error about latitude range

**Likely Cause:** Latitude is outside valid range [-90, 90]

**Solution:** Check your latitude value:
- Must be between -90 (South Pole) and 90 (North Pole)
- Use decimal degrees (not degrees/minutes/seconds)

**Example:**
```
Wrong: latitude = 40°45'36"N → not in decimal format
Right: latitude = 40.76 → decimal degrees
```

### Problem: Wet days are too clustered or too random

**Likely Cause:** PWW and PWD values are incorrect

**Solution:** Check the relationship between PWW and PWD:
- PWW > PWD: wet days cluster (typical for most climates)
- PWW ≈ PWD: random wet/dry pattern (unusual)
- PWW < PWD: dry days cluster (very unusual)

**Check:** For most climates, PWW should be 0.3-0.7 and PWD should be 0.1-0.4.

## Advanced Topics

### Understanding the Fourier Approach

The WGEN kernel uses Fourier functions to model seasonal variations. This is more physically realistic than using discrete monthly values because:

1. **Smooth transitions**: Temperature doesn't jump abruptly on the first day of each month
2. **Continuous representation**: Any day of the year has a well-defined expected temperature
3. **Fewer parameters**: 2 values (mean + amplitude) instead of 12 monthly values
4. **Latitude-aware**: Peak timing automatically adjusts for hemisphere

The mathematical form is:
```
T(d) = T_mean + T_amplitude × cos(2π × (d - d_peak) / 365)
```

Where:
- `d` = day of year (1-365)
- `d_peak` = day with maximum temperature (automatically set based on latitude)
- `T_mean` = annual mean temperature (txmd, tn, etc.)
- `T_amplitude` = seasonal swing (atx, atn, etc.)

### Precipitation vs Temperature/Radiation Parameters

**Why are precipitation parameters monthly while temperature/radiation are constant?**

1. **Precipitation patterns**: Highly variable month-to-month (monsoons, dry seasons, etc.)
2. **Temperature patterns**: Follow smooth sinusoidal patterns driven by solar geometry
3. **Radiation patterns**: Directly related to Earth's orbit and axial tilt (smooth variation)

This hybrid approach captures the irregular nature of precipitation while maintaining physical realism for temperature and radiation.

### Coefficient of Variation Parameters

The CV parameters (cvtx, acvtx, cvtn, acvtn) control stochastic variability:

- **cvtx, cvtn**: Base level of day-to-day temperature variability
- **acvtx, acvtn**: How variability changes seasonally

Typical patterns:
- Higher variability in winter (cold air masses, frontal systems)
- Lower variability in summer (stable high pressure)
- Continental climates have higher CV than maritime climates

### Wet vs Dry Day Parameters

Several parameters distinguish between wet and dry days:

- **txmd vs txmw**: Maximum temperature is typically 1-3°C lower on wet days due to cloud cover
- **rmd vs rmw**: Solar radiation is typically 20-30% lower on wet days due to clouds

This captures the physical relationship between precipitation and other weather variables.

## Parameter Estimation Tool

The waterlib package includes a parameter estimation utility that can automatically estimate all WGEN parameters from historical weather data:

```bash
python waterlib/templates/wgen_parameter_estimator.py \
  --input historical_data.csv \
  --output wgen_params.csv \
  --latitude 40.76 \
  --precip-column "precip_mm" \
  --tmax-column "tmax_c" \
  --tmin-column "tmin_c" \
  --solar-column "solar_mjm2"
```

The tool will:
1. Calculate monthly PWW, PWD, ALPHA, BETA values
2. Estimate constant temperature parameters using Fourier fitting
3. Estimate constant radiation parameters
4. Generate a CSV file with monthly parameters
5. Generate a YAML snippet with constant parameters

See `waterlib/templates/wgen_parameter_estimator.py` for detailed usage.

## References

1. Richardson, C.W., and Wright, D.A. (1984). "WGEN: A Model for Generating Daily Weather Variables." U.S. Department of Agriculture, Agricultural Research Service, ARS-8.

2. Richardson, C.W. (1982). "Dependence Structure of Daily Temperature and Solar Radiation." Transactions of the ASAE, 25(3), 735-739.

3. Nicks, A.D., and Gander, G.A. (1994). "CLIGEN: A Weather Generator for Climate Inputs to Water Resource and Other Models." Proceedings of the 5th International Conference on Computers in Agriculture, 903-909.

## Support

For questions or issues with WGEN parameter configuration, please refer to:
- The waterlib documentation at `docs/API_REFERENCE.md`
- The kernel migration guide at `docs/KERNEL_MIGRATION_GUIDE.md`
- Example configurations in the `examples/` directory
- The WGEN interface restructure design document at `.kiro/specs/wgen-interface-restructure/design.md`

## License

This template and guide are part of the waterlib project.
