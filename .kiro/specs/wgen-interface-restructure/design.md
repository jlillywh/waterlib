# Design Document: WGEN Interface Restructure

## Overview

This design restructures the WGEN (Weather Generator) kernel interface to accept a simplified, standardized parameter structure that aligns with the standard WGEN input format. The new interface separates monthly precipitation parameters from constant temperature/radiation parameters, using Fourier functions with latitude to simulate seasonal temperature and radiation variations.

The key changes are:
- Monthly precipitation parameters: 12 values each for PWW, PWD, ALPHA, BETA (48 total values)
- Constant temperature/radiation parameters: 13 scalar values (TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN, RMD, AR, RMW)
- Latitude: 1 scalar value for Fourier-based seasonal calculations
- Temperature interface in Celsius, converted to Kelvin internally

## Architecture

### Component Structure

The WGEN kernel remains a pure function with no side effects. The architecture consists of:

1. **WGENParams dataclass**: Holds all input parameters (monthly precipitation, constant temp/radiation, latitude)
2. **WGENState dataclass**: Maintains simulation state (previous day wetness, RNG state, current date)
3. **WGENOutputs dataclass**: Returns generated weather variables
4. **wgen_step function**: Pure kernel function that generates one day of weather
5. **Helper functions**: Internal functions for Fourier calculations and unit conversions

### Data Flow

```
WGENParams (monthly precip + constants + latitude)
    ↓
wgen_step(params, state) → (new_state, outputs)
    ↓
WGENOutputs (precip, tmax, tmin, solar)
```

The `wgen_step` function:
1. Extracts the current month from state
2. Selects appropriate monthly precipitation parameters
3. Applies Fourier functions with latitude for temperature/radiation
4. Generates stochastic weather variables
5. Returns updated state and outputs

## Components and Interfaces

### WGENParams Dataclass

```python
@dataclass
class WGENParams:
    """
    Parameters for WGEN stochastic weather generation.

    Attributes:
        # Monthly precipitation parameters (12 values each)
        pww: List[float]  # Probability wet|wet for each month [0-1]
        pwd: List[float]  # Probability wet|dry for each month [0-1]
        alpha: List[float]  # Gamma shape parameter for each month [>0]
        beta: List[float]  # Gamma scale parameter for each month (mm) [>0]

        # Constant temperature parameters (Celsius at interface)
        txmd: float  # Mean max temp on dry days (°C)
        atx: float   # Amplitude of max temp seasonal variation (°C)
        txmw: float  # Mean max temp on wet days (°C)
        tn: float    # Mean min temp (°C)
        atn: float   # Amplitude of min temp seasonal variation (°C)
        cvtx: float  # Coefficient of variation for Tmax mean
        acvtx: float # Coefficient of variation for Tmax amplitude
        cvtn: float  # Coefficient of variation for Tmin mean
        acvtn: float # Coefficient of variation for Tmin amplitude

        # Constant radiation parameters
        rmd: float   # Mean solar radiation on dry days (MJ/m²/day)
        ar: float    # Amplitude of solar radiation seasonal variation (MJ/m²/day)
        rmw: float   # Mean solar radiation on wet days (MJ/m²/day)

        # Location
        latitude: float  # Station latitude (degrees, -90 to 90)

        # Optional
        random_seed: Optional[int] = None
    """
```

### WGENState Dataclass

```python
@dataclass
class WGENState:
    """
    State variables for WGEN simulation.

    Attributes:
        is_wet: Whether the previous day was wet
        random_state: Internal RNG state for reproducibility
        current_date: Current simulation date (for month selection)
    """
    is_wet: bool
    random_state: Optional[tuple]
    current_date: datetime.date  # NEW: needed to select monthly params
```

### WGENOutputs Dataclass

```python
@dataclass
class WGENOutputs:
    """
    Outputs from one WGEN timestep.

    Attributes:
        precip_mm: Generated precipitation (mm/day)
        tmax_c: Generated maximum temperature (°C)
        tmin_c: Generated minimum temperature (°C)
        solar_mjm2: Generated solar radiation (MJ/m²/day)
        is_wet: Whether this day is classified as wet
    """
    precip_mm: float
    tmax_c: float
    tmin_c: float
    solar_mjm2: float
    is_wet: bool
```

### Core Kernel Function

```python
def wgen_step(
    params: WGENParams,
    state: WGENState
) -> Tuple[WGENState, WGENOutputs]:
    """
    Generate one day of synthetic weather data using WGEN algorithm.

    Pure function with no side effects (except internal RNG state).

    Args:
        params: Fixed parameters defining weather statistics
        state: Current state (previous day's wetness, RNG state, date)

    Returns:
        Tuple of (new_state, outputs)
    """
```

### Helper Functions

```python
def _celsius_to_kelvin(temp_c: float) -> float:
    """Convert Celsius to Kelvin."""
    return temp_c + 273.15

def _kelvin_to_celsius(temp_k: float) -> float:
    """Convert Kelvin to Celsius."""
    return temp_k - 273.15

def _get_monthly_params(
    params: WGENParams,
    month: int
) -> Tuple[float, float, float, float]:
    """
    Extract monthly precipitation parameters for given month.

    Args:
        params: WGEN parameters
        month: Month number (1-12)

    Returns:
        Tuple of (pww, pwd, alpha, beta) for the month
    """
    idx = month - 1  # Convert to 0-indexed
    return (
        params.pww[idx],
        params.pwd[idx],
        params.alpha[idx],
        params.beta[idx]
    )

def _calculate_seasonal_temp(
    mean: float,
    amplitude: float,
    day_of_year: int,
    latitude: float
) -> float:
    """
    Calculate temperature using Fourier function.

    Args:
        mean: Mean temperature (K)
        amplitude: Seasonal amplitude (K)
        day_of_year: Day of year (1-365/366)
        latitude: Station latitude (degrees)

    Returns:
        Temperature for the day (K)
    """
    # Fourier function: T = mean + amplitude * cos(2π(doy - peak)/365)
    # Peak day varies with latitude (Northern Hemisphere ~200, Southern ~20)
    peak_day = 200 if latitude >= 0 else 20
    angle = 2 * np.pi * (day_of_year - peak_day) / 365
    return mean + amplitude * np.cos(angle)

def _calculate_seasonal_radiation(
    mean: float,
    amplitude: float,
    day_of_year: int,
    latitude: float
) -> float:
    """
    Calculate solar radiation using Fourier function.

    Args:
        mean: Mean radiation (MJ/m²/day)
        amplitude: Seasonal amplitude (MJ/m²/day)
        day_of_year: Day of year (1-365/366)
        latitude: Station latitude (degrees)

    Returns:
        Solar radiation for the day (MJ/m²/day)
    """
    # Similar Fourier function for radiation
    peak_day = 172 if latitude >= 0 else 355  # Summer solstice
    angle = 2 * np.pi * (day_of_year - peak_day) / 365
    return max(0, mean + amplitude * np.cos(angle))
```

## Data Models

### Parameter Validation

The WGENParams dataclass should include validation:

```python
def __post_init__(self):
    """Validate parameters after initialization."""
    # Check list lengths
    if len(self.pww) != 12:
        raise ValueError(f"pww must have 12 values, got {len(self.pww)}")
    if len(self.pwd) != 12:
        raise ValueError(f"pwd must have 12 values, got {len(self.pwd)}")
    if len(self.alpha) != 12:
        raise ValueError(f"alpha must have 12 values, got {len(self.alpha)}")
    if len(self.beta) != 12:
        raise ValueError(f"beta must have 12 values, got {len(self.beta)}")

    # Check probability ranges
    for i, (pww, pwd) in enumerate(zip(self.pww, self.pwd)):
        if not 0 <= pww <= 1:
            raise ValueError(f"pww[{i}] must be in [0,1], got {pww}")
        if not 0 <= pwd <= 1:
            raise ValueError(f"pwd[{i}] must be in [0,1], got {pwd}")

    # Check positive values
    for i, (alpha, beta) in enumerate(zip(self.alpha, self.beta)):
        if alpha <= 0:
            raise ValueError(f"alpha[{i}] must be > 0, got {alpha}")
        if beta <= 0:
            raise ValueError(f"beta[{i}] must be > 0, got {beta}")

    # Check latitude range
    if not -90 <= self.latitude <= 90:
        raise ValueError(f"latitude must be in [-90,90], got {self.latitude}")
```

### CSV File Format

The monthly parameter CSV file format:

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

### YAML Configuration Format

Temperature and radiation parameters in YAML:

```yaml
wgen_config:
  # Monthly precipitation parameters
  param_file: "data/wgen_params.csv"

  # Location
  latitude: 40.76

  # Temperature parameters (Celsius)
  txmd: 291.7
  atx: 15.1
  txmw: 288.5
  tn: 277.9
  atn: 11.7
  cvtx: 0.01675
  acvtx: -0.00383
  cvtn: 0.01605
  acvtn: -0.00345

  # Radiation parameters (MJ/m²/day)
  rmd: 12.9
  ar: 10.2
  rmw: 12.9
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

1.1 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for PWW
  Thoughts: This is testing that the dataclass accepts a list of 12 values. We can test this by creating random lists of various lengths and ensuring that only lists of length 12 are accepted.
  Testable: yes - property

1.2 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for PWD
  Thoughts: Same as 1.1, testing list length validation
  Testable: yes - property

1.3 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for ALPHA
  Thoughts: Same as 1.1, testing list length validation
  Testable: yes - property

1.4 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for BETA
  Thoughts: Same as 1.1, testing list length validation
  Testable: yes - property

1.5 WHEN monthly precipitation parameters are provided THEN the system SHALL validate that each list contains exactly 12 values
  Thoughts: This is redundant with 1.1-1.4, as they all test the same validation logic
  Testable: redundant - covered by 1.1-1.4

2.1 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept scalar values for TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN, RMD, AR, and RMW
  Thoughts: This is testing that the dataclass accepts scalar float values for these parameters. We can test by creating instances with random float values.
  Testable: yes - example

2.2 WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept a latitude value in degrees
  Thoughts: Testing that latitude is accepted as a scalar
  Testable: yes - example

2.3 WHEN latitude is provided THEN the system SHALL validate that the value is between -90 and 90 degrees
  Thoughts: This is testing boundary validation. We can generate random latitudes both inside and outside the valid range and ensure proper validation.
  Testable: yes - property

2.4 WHEN temperature parameters are provided at the interface THEN the system SHALL accept values in Celsius
  Thoughts: This is about the interface accepting Celsius values, which is just the dataclass accepting float values
  Testable: yes - example

2.5 WHEN temperature calculations are performed internally THEN the system SHALL convert Celsius to Kelvin
  Thoughts: This is a round-trip property. If we provide temperature in Celsius, convert to Kelvin, then convert back, we should get the original value (within floating point precision).
  Testable: yes - property

2.6 WHEN radiation parameters are provided THEN the system SHALL accept values in MJ/m²/day
  Thoughts: This is just testing that the dataclass accepts float values for radiation parameters
  Testable: yes - example

2.7 WHEN precipitation BETA parameters are provided THEN the system SHALL accept values in millimeters
  Thoughts: This is testing that beta values are accepted as floats
  Testable: yes - example

3.1 WHEN the wgen_step function is called THEN the system SHALL compute outputs without side effects
  Thoughts: This is about purity of the function. We can test that calling the function multiple times with the same inputs produces the same outputs (given the same RNG state).
  Testable: yes - property

3.2 WHEN the wgen_step function is called THEN the system SHALL not depend on graph structure or external state
  Thoughts: This is an architectural constraint that's hard to test directly. It's more of a code review item.
  Testable: no

3.3 WHEN the wgen_step function is called THEN the system SHALL return a tuple of (new_state, outputs)
  Thoughts: This is testing the return type structure. We can verify that the function returns a 2-tuple with the correct types.
  Testable: yes - property

3.4 WHEN the wgen_step function uses monthly parameters THEN the system SHALL select the appropriate month's values based on the current simulation date
  Thoughts: This is testing that the function correctly extracts monthly parameters. We can test by providing different dates and verifying the correct month's parameters are used.
  Testable: yes - property

4.1 WHEN the wgen_params_template.csv file is updated THEN the system SHALL maintain the 12-month structure with PWW, PWD, ALPHA, BETA columns
  Thoughts: This is about file format, which is a manual verification task, not an automated test
  Testable: no

4.2 WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document the new temperature/radiation parameter structure
  Thoughts: This is documentation, not testable code
  Testable: no

4.3 WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document that temperature/radiation parameters are constants with Fourier-based seasonal variation
  Thoughts: This is documentation, not testable code
  Testable: no

4.4 WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document the latitude parameter and its valid range
  Thoughts: This is documentation, not testable code
  Testable: no

5.1 WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate monthly PWW, PWD, ALPHA, BETA values
  Thoughts: This is testing the parameter estimation function. We can test that given historical data, it produces 12 values for each parameter.
  Testable: yes - property

5.2 WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate constant temperature parameters
  Thoughts: Testing that the estimator produces scalar temperature parameters
  Testable: yes - property

5.3 WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate constant radiation parameters
  Thoughts: Testing that the estimator produces scalar radiation parameters
  Testable: yes - property

5.4 WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL output parameters in a format compatible with the new WGENParams structure
  Thoughts: This is a round-trip property: estimate parameters from data, create WGENParams, verify it's valid
  Testable: yes - property

6.1 WHEN unit tests are updated THEN the system SHALL test WGENParams instantiation with monthly precipitation parameters
  Thoughts: This is about writing tests, not a property to test
  Testable: no

6.2 WHEN unit tests are updated THEN the system SHALL test WGENParams instantiation with constant temperature/radiation parameters
  Thoughts: This is about writing tests, not a property to test
  Testable: no

6.3 WHEN unit tests are updated THEN the system SHALL test parameter validation
  Thoughts: This is about writing tests, not a property to test
  Testable: no

6.4 WHEN unit tests are updated THEN the system SHALL test that wgen_step correctly selects monthly parameters based on simulation date
  Thoughts: This is about writing tests, not a property to test
  Testable: no

7.1-7.4: All documentation updates
  Thoughts: Documentation is not testable code
  Testable: no

### Property Reflection

After reviewing the prework, I identify the following redundancies:

1. Properties 1.1-1.4 all test the same validation logic (12-month list length). These can be combined into a single comprehensive property.
2. Properties 2.4, 2.6, 2.7 are all just testing that the dataclass accepts float values, which is trivial. These can be combined into a single example test.
3. Property 5.4 subsumes the validation aspects of 5.1-5.3, as it tests the complete round-trip.

### Correctness Properties

Property 1: Monthly parameter lists have exactly 12 values
*For any* WGENParams instance, the pww, pwd, alpha, and beta lists must each contain exactly 12 values
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

Property 2: Latitude validation
*For any* latitude value, WGENParams instantiation should succeed if and only if the latitude is in the range [-90, 90]
**Validates: Requirements 2.3**

Property 3: Temperature unit conversion round-trip
*For any* temperature value in Celsius, converting to Kelvin and back to Celsius should yield the original value (within floating point precision)
**Validates: Requirements 2.5**

Property 4: Function purity
*For any* WGENParams and WGENState with fixed RNG state, calling wgen_step multiple times should produce identical outputs
**Validates: Requirements 3.1**

Property 5: Return type structure
*For any* valid inputs, wgen_step should return a 2-tuple where the first element is a WGENState and the second is a WGENOutputs
**Validates: Requirements 3.3**

Property 6: Monthly parameter selection
*For any* date, wgen_step should use the precipitation parameters corresponding to that date's month
**Validates: Requirements 3.4**

Property 7: Parameter estimation output compatibility
*For any* historical climate data, the parameter estimator should produce outputs that can successfully instantiate a valid WGENParams object
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

## Error Handling

### Validation Errors

The system should raise clear validation errors for:

1. **Invalid list lengths**: "pww must have 12 values, got {n}"
2. **Invalid probability ranges**: "pww[{i}] must be in [0,1], got {value}"
3. **Invalid positive values**: "alpha[{i}] must be > 0, got {value}"
4. **Invalid latitude**: "latitude must be in [-90,90], got {value}"

### File Loading Errors

When loading CSV files:

1. **Missing file**: "WGEN parameter file not found: {path}"
2. **Invalid format**: "WGEN parameter file must have columns: Month, PWW, PWD, ALPHA, BETA"
3. **Wrong number of rows**: "WGEN parameter file must have exactly 12 rows, got {n}"
4. **Invalid values**: "Invalid value in row {i}, column {col}: {value}"

### Runtime Errors

During simulation:

1. **Invalid date**: "WGENState.current_date must be set for monthly parameter selection"
2. **RNG state issues**: Handle gracefully with informative messages

## Testing Strategy

### Unit Tests

Unit tests will cover:

1. **WGENParams instantiation**: Test with valid and invalid parameters
2. **Validation logic**: Test boundary conditions for probabilities, positive values, latitude
3. **Helper functions**: Test unit conversion, monthly parameter extraction, Fourier calculations
4. **CSV loading**: Test loading valid and invalid CSV files
5. **YAML configuration**: Test parsing YAML with temperature/radiation parameters

### Property-Based Tests

Property-based tests will use the **Hypothesis** library for Python. Each test will run a minimum of 100 iterations.

1. **Property 1: Monthly parameter lists** - Generate random lists of various lengths, verify only length-12 lists are accepted
2. **Property 2: Latitude validation** - Generate random latitudes, verify validation
3. **Property 3: Temperature conversion round-trip** - Generate random temperatures, verify conversion accuracy
4. **Property 4: Function purity** - Generate random params/state, verify deterministic behavior
5. **Property 5: Return type structure** - Generate random inputs, verify return types
6. **Property 6: Monthly parameter selection** - Generate random dates, verify correct month selection
7. **Property 7: Parameter estimation compatibility** - Generate synthetic climate data, verify estimator output

### Integration Tests

Integration tests will verify:

1. **End-to-end workflow**: Load CSV → Create WGENParams → Run wgen_step → Verify outputs
2. **YAML configuration**: Load YAML → Parse parameters → Create WGENParams → Run simulation
3. **Parameter estimation**: Historical data → Estimate parameters → Create WGENParams → Run simulation

## Implementation Notes

### File Updates Required

1. **waterlib/kernels/climate/wgen.py**: Update WGENParams, WGENState, wgen_step, add helper functions
2. **waterlib/templates/wgen_params_template.csv**: Update to new format (already close to correct)
3. **waterlib/templates/WGEN_PARAMETERS_GUIDE.md**: Update documentation for new interface
4. **waterlib/templates/wgen_parameter_estimator.py**: Update to estimate new parameter structure
5. **tests/unit/kernels/test_wgen.py**: Create comprehensive unit and property tests
6. **docs/API_REFERENCE.md**: Update WGEN documentation
7. **docs/KERNEL_MIGRATION_GUIDE.md**: Update WGEN examples

### Dependencies

- **numpy**: For Fourier calculations and array operations
- **hypothesis**: For property-based testing
- **datetime**: For date handling in WGENState

### Performance Considerations

- Monthly parameter lookup is O(1) using list indexing
- Fourier calculations are simple trigonometric operations
- No performance concerns for typical simulation lengths

### Future Enhancements

This design focuses on the interface restructure. Future work may include:

1. Full WGEN stochastic algorithm implementation (currently placeholder)
2. Cross-correlation between temperature, precipitation, and radiation
3. Advanced parameter estimation techniques
4. Support for sub-daily timesteps
