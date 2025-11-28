# Design Document

## Overview

This design addresses the critical configuration parameter naming inconsistency between waterlib's documentation and code implementation. The documentation consistently shows climate drivers configured with a nested `params:` dictionary structure, but the `DriverConfig` dataclass does not support this syntax, causing immediate errors for users following the getting started guide.

The solution involves modifying the `DriverConfig` class and `ClimateSettings.from_dict()` method to accept and properly parse the documented nested `params:` structure while maintaining backward compatibility with existing flat configurations.

## Architecture

### Current Architecture

```
YAML File:
  climate:
    precipitation:
      mode: 'stochastic'
      params:              # ← Not supported!
        mean_annual: 800

↓ Parsed by

ClimateSettings.from_dict()
  ↓ Creates
DriverConfig(**precip_dict)  # ← Fails with "unexpected keyword argument 'params'"
```

### Proposed Architecture

```
YAML File:
  climate:
    precipitation:
      mode: 'stochastic'
      params:              # ← Now supported!
        mean_annual: 800

↓ Parsed by

ClimateSettings.from_dict()
  ↓ Detects nested params
  ↓ Flattens structure
  ↓ Creates
DriverConfig(mode='stochastic', mean_annual=800, ...)  # ← Success!
```

### Key Design Decisions

1. **Backward Compatibility**: Support both nested `params:` and flat structures to avoid breaking existing models
2. **Parsing Location**: Handle flattening in `ClimateSettings.from_dict()` before passing to `DriverConfig`
3. **Mode-Specific Parameters**: Stochastic mode uses `params:`, timeseries mode uses flat parameters (file, column)
4. **Validation**: Validate mode-specific parameters after flattening

## Components and Interfaces

### Modified Components

#### 1. DriverConfig Dataclass

**Current Structure:**
```python
@dataclass
class DriverConfig:
    mode: Literal['stochastic', 'timeseries', 'wgen']
    seed: Optional[int] = None
    file: Optional[Path] = None
    column: Optional[str] = None
```

**Proposed Structure:**
```python
@dataclass
class DriverConfig:
    mode: Literal['stochastic', 'timeseries', 'wgen']
    seed: Optional[int] = None
    file: Optional[Path] = None
    column: Optional[str] = None
    # Stochastic mode parameters (from params: dict)
    mean_annual: Optional[float] = None
    wet_day_prob: Optional[float] = None
    wet_wet_prob: Optional[float] = None
    alpha: Optional[float] = None
    mean_tmin: Optional[float] = None
    mean_tmax: Optional[float] = None
    amplitude_tmin: Optional[float] = None
    amplitude_tmax: Optional[float] = None
    std_tmin: Optional[float] = None
    std_tmax: Optional[float] = None
    mean: Optional[float] = None  # For ET
    std: Optional[float] = None   # For ET
```

**Rationale**: Adding optional fields for all documented stochastic parameters allows the dataclass to accept them directly after flattening.

#### 2. ClimateSettings.from_dict() Method

**Current Implementation:**
```python
if 'precipitation' in climate_dict:
    precip_dict = climate_dict['precipitation']
    precipitation = DriverConfig(**precip_dict)  # Fails if params: present
```

**Proposed Implementation:**
```python
if 'precipitation' in climate_dict:
    precip_dict = climate_dict['precipitation'].copy()
    # Flatten nested params if present
    if 'params' in precip_dict:
        params = precip_dict.pop('params')
        precip_dict.update(params)  # Merge params into top level
    precipitation = DriverConfig(**precip_dict)  # Now works!
```

**Rationale**: Flattening at parse time keeps DriverConfig simple and maintains backward compatibility.

### New Utility Functions

#### flatten_driver_config()

```python
def flatten_driver_config(driver_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten nested params dictionary in driver configuration.

    Args:
        driver_dict: Driver configuration dictionary (may contain 'params')

    Returns:
        Flattened dictionary with params merged to top level

    Example:
        Input:  {'mode': 'stochastic', 'params': {'mean_annual': 800}}
        Output: {'mode': 'stochastic', 'mean_annual': 800}
    """
    flattened = driver_dict.copy()
    if 'params' in flattened:
        params = flattened.pop('params')
        if not isinstance(params, dict):
            raise ConfigurationError(
                f"'params' must be a dictionary, got {type(params).__name__}"
            )
        flattened.update(params)
    return flattened
```

## Data Models

### Configuration Dictionary Formats

#### Nested Format (Documented, Now Supported)

```yaml
precipitation:
  mode: 'stochastic'
  seed: 42
  params:
    mean_annual: 800
    wet_day_prob: 0.3
    wet_wet_prob: 0.6
```

#### Flat Format (Backward Compatible)

```yaml
precipitation:
  mode: 'stochastic'
  seed: 42
  mean_annual: 800
  wet_day_prob: 0.3
  wet_wet_prob: 0.6
```

#### Timeseries Format (No params:)

```yaml
precipitation:
  mode: 'timeseries'
  file: 'data/precip.csv'
  column: 'precip_mm'
```

### Parameter Mapping

| Mode | Parameters | Location |
|------|-----------|----------|
| stochastic (precip) | mean_annual, wet_day_prob, wet_wet_prob, alpha | params: dict |
| stochastic (temp) | mean_tmin, mean_tmax, amplitude_tmin, amplitude_tmax, std_tmin, std_tmax | params: dict |
| stochastic (et) | mean, std | params: dict |
| timeseries | file, column | top level |
| wgen | (uses WgenConfig) | top level |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Nested params parsing succeeds

*For any* valid climate driver configuration with nested `params:` dictionary, parsing should succeed without errors and produce a valid DriverConfig instance.
**Validates: Requirements 1.1**

### Property 2: Parameter extraction correctness

*For any* valid `params:` dictionary, the DriverConfig instance should contain all parameters from the nested dictionary at the top level.
**Validates: Requirements 1.2**

### Property 3: Flattening preserves semantics

*For any* valid nested configuration, flattening then parsing should produce the same DriverConfig as if the parameters were flat originally.
**Validates: Requirements 1.4**

### Property 4: Backward compatibility

*For any* valid flat configuration (old format), parsing should succeed and produce the same DriverConfig as before the changes.
**Validates: Requirements 1.5**

### Property 5: Dual format support

*For any* valid configuration, both nested `params:` format and flat format should parse to equivalent DriverConfig instances.
**Validates: Requirements 2.2**

### Property 6: Invalid configuration errors

*For any* invalid climate configuration, the system should raise a ConfigurationError with a descriptive message.
**Validates: Requirements 4.1**

### Property 7: Missing parameter errors

*For any* configuration missing a required parameter, the error message should specify which parameter is missing.
**Validates: Requirements 4.3**

### Property 8: Unexpected parameter errors

*For any* configuration with an unexpected parameter, the error message should list valid parameters for that mode.
**Validates: Requirements 4.4**

### Property 9: Error message completeness

*For any* configuration parsing failure, the error message should include the driver name and the configuration block that failed.
**Validates: Requirements 4.5**

### Property 10: Mode-specific validation

*For any* configuration, mode-specific parameters should be validated appropriately (stochastic params for stochastic mode, file/column for timeseries mode).
**Validates: Requirements 8.5**

## Error Handling

### Error Types and Messages

#### 1. Invalid params Type

```python
# Input: params: "not a dict"
ConfigurationError: 'params' must be a dictionary, got str
```

#### 2. Missing Required Parameter

```python
# Input: mode: 'stochastic', params: {}
ConfigurationError: Stochastic precipitation driver missing required parameter 'mean_annual'.
Required parameters: mean_annual, wet_day_prob, wet_wet_prob
```

#### 3. Unexpected Parameter

```python
# Input: mode: 'stochastic', params: {invalid_param: 123}
ConfigurationError: Unexpected parameter 'invalid_param' for stochastic mode.
Valid parameters: mean_annual, wet_day_prob, wet_wet_prob, alpha, seed
```

#### 4. Mixed Format Error

```python
# Input: mode: 'stochastic', params: {mean_annual: 800}, mean_annual: 900
ConfigurationError: Parameter 'mean_annual' specified both in 'params' and at top level.
Use either nested 'params:' format or flat format, not both.
```

#### 5. Mode-Specific Parameter Error

```python
# Input: mode: 'timeseries', params: {mean_annual: 800}
ConfigurationError: 'params' dictionary not valid for timeseries mode.
Timeseries mode uses flat parameters: file, column
```

### Validation Strategy

1. **Parse-time validation**: Check for structural issues (params type, mixed formats)
2. **Post-flatten validation**: Check for mode-specific required parameters
3. **DriverConfig validation**: Check parameter types and ranges in `__post_init__`

## Testing Strategy

### Unit Tests

1. **Test nested params parsing**
   - Valid nested configurations parse successfully
   - All parameters extracted correctly
   - Seed parameter preserved

2. **Test flat format parsing**
   - Backward compatibility maintained
   - Old configurations still work
   - No regression in existing functionality

3. **Test mixed format detection**
   - Error raised when params and flat parameters both present
   - Clear error message provided

4. **Test mode-specific validation**
   - Stochastic mode requires stochastic parameters
   - Timeseries mode requires file/column
   - WGEN mode handled correctly

5. **Test error messages**
   - Missing parameters identified
   - Unexpected parameters listed
   - Driver name included in errors

### Property-Based Tests

Property-based tests will use Hypothesis to generate random configurations and verify properties hold across all inputs.

#### Test Generators

```python
from hypothesis import given, strategies as st

# Generate valid stochastic params
stochastic_params = st.fixed_dictionaries({
    'mean_annual': st.floats(min_value=0, max_value=5000),
    'wet_day_prob': st.floats(min_value=0, max_value=1),
    'wet_wet_prob': st.floats(min_value=0, max_value=1),
})

# Generate valid driver configs
driver_config_nested = st.fixed_dictionaries({
    'mode': st.just('stochastic'),
    'params': stochastic_params,
    'seed': st.one_of(st.none(), st.integers(min_value=0))
})

driver_config_flat = st.fixed_dictionaries({
    'mode': st.just('stochastic'),
    'mean_annual': st.floats(min_value=0, max_value=5000),
    'wet_day_prob': st.floats(min_value=0, max_value=1),
    'wet_wet_prob': st.floats(min_value=0, max_value=1),
    'seed': st.one_of(st.none(), st.integers(min_value=0))
})
```

### Integration Tests

1. **Test documented examples**
   - Load all examples from GETTING_STARTED.md
   - Parse and verify they work
   - Run simulations to completion

2. **Test scaffolding**
   - Generate project with create_project()
   - Load generated baseline.yaml
   - Run generated run_model.py
   - Verify no errors

3. **Test example files**
   - Load all YAML files in examples/
   - Parse configurations
   - Verify no errors

### Documentation Tests

1. **Extract and test code blocks**
   - Parse YAML blocks from markdown files
   - Attempt to load each configuration
   - Verify they parse successfully

2. **Test README examples**
   - Extract all YAML examples from README.md
   - Parse and validate each one

3. **Test YAML_SCHEMA examples**
   - Extract all examples from docs/YAML_SCHEMA.md
   - Verify they match implementation

## Implementation Notes

### Migration Path

1. **Phase 1**: Add support for nested `params:` (this design)
   - Modify DriverConfig to accept stochastic parameters
   - Update ClimateSettings.from_dict() to flatten params
   - Maintain backward compatibility

2. **Phase 2**: Update documentation
   - Update GETTING_STARTED.md examples
   - Update YAML_SCHEMA.md
   - Update README.md
   - Update API reference

3. **Phase 3**: Update templates and examples
   - Update scaffolding templates
   - Update all example YAML files
   - Update example Python scripts

4. **Phase 4**: Add tests
   - Unit tests for new functionality
   - Property-based tests
   - Integration tests for examples

### Backward Compatibility Guarantee

The implementation will support both formats indefinitely:

```python
# Old format (still works)
precipitation:
  mode: 'stochastic'
  mean_annual: 800
  wet_day_prob: 0.3

# New format (now works)
precipitation:
  mode: 'stochastic'
  params:
    mean_annual: 800
    wet_day_prob: 0.3
```

Users can migrate at their own pace or continue using the old format.

### Performance Considerations

- Flattening adds minimal overhead (single dictionary copy and update)
- No impact on simulation performance
- Parsing time increase negligible (< 1ms per driver)

### Future Extensibility

The design supports adding new driver modes:

```python
# Future: Add new mode
precipitation:
  mode: 'neural_network'
  params:
    model_path: 'models/precip_nn.pkl'
    # ... other params
```

The flattening logic will work for any new mode that uses `params:`.
