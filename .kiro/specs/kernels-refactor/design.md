# Design Document

## Overview

This design establishes a clear architectural separation between computational kernels (pure algorithms) and graph components (system nodes) in waterlib. Currently, algorithmic implementations are mixed with graph-level components, creating confusion about what can be connected in YAML versus what is an internal calculation.

The refactor creates a `waterlib/kernels/` directory structure organized by domain (hydrology, hydraulics, climate), moves pure computational code into kernels, and updates components to import and orchestrate these kernels. This separation improves code organization, testability, and makes the architecture immediately obvious to developers.

## Architecture

### Current Structure (Before Refactor)

```
waterlib/
├── components/
│   ├── snow17.py          # Mixed: algorithm + component wrapper
│   ├── awbm.py            # Mixed: algorithm + component wrapper
│   ├── hargreaves.py      # Mixed: algorithm + component wrapper
│   ├── weir.py            # Mixed: algorithm + component wrapper
│   ├── catchment.py       # Component that uses Snow17 + AWBM
│   ├── reservoir.py       # Pure component
│   ├── pump.py            # Pure component
│   └── ...
└── climate.py             # Contains stochastic generators
```

### Target Structure (After Refactor)

```
waterlib/
├── kernels/               # NEW: Pure computational algorithms
│   ├── __init__.py
│   ├── hydrology/
│   │   ├── __init__.py
│   │   ├── snow17.py      # MOVED: Pure Snow17 algorithm
│   │   ├── awbm.py        # MOVED: Pure AWBM algorithm
│   │   └── runoff.py      # Runoff generation utilities
│   ├── hydraulics/
│   │   ├── __init__.py
│   │   ├── weir.py        # MOVED: Pure weir equations
│   │   └── spillway.py    # Spillway calculations
│   └── climate/
│       ├── __init__.py
│       ├── et.py          # MOVED: Hargreaves + future ET methods
│       └── wgen.py        # MOVED: WGEN stochastic generator
│
├── components/            # Graph-connectable components only
│   ├── catchment.py       # UPDATED: Imports from kernels.hydrology
│   ├── reservoir.py       # UPDATED: Imports from kernels.hydraulics
│   ├── pump.py            # No change (pure component)
│   └── ...
│
└── climate.py             # UPDATED: Imports from kernels.climate
```

### Dependency Flow

```
┌─────────────────────────────────────────┐
│         YAML Model Definition           │
│    (User-facing configuration)          │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      waterlib.components                │
│  (Graph nodes, I/O, state management)   │
│                                         │
│  • Catchment                            │
│  • Reservoir                            │
│  • Pump                                 │
└─────────────────────────────────────────┘
                  │
                  │ imports from
                  ▼
┌─────────────────────────────────────────┐
│       waterlib.kernels                  │
│   (Pure algorithms, no graph deps)      │
│                                         │
│  • hydrology/snow17                     │
│  • hydrology/awbm                       │
│  • hydraulics/weir                      │
│  • climate/et                           │
└─────────────────────────────────────────┘
```

**Key Principle**: Kernels never import from components. Components orchestrate kernels.

## Components and Interfaces

### Kernel Interface Pattern

All kernels follow a pure function pattern:

```python
def kernel_function(inputs: KernelInputs, params: KernelParams, state: KernelState) -> KernelOutputs:
    """
    Pure computational function with no side effects.

    Args:
        inputs: Current timestep inputs (e.g., precipitation, temperature)
        params: Fixed parameters (e.g., mfmax, mfmin for Snow17)
        state: Current state variables (e.g., w_i, w_q for Snow17)

    Returns:
        Tuple of (new_state, outputs)
    """
    # Pure calculation logic
    new_state = calculate_new_state(inputs, params, state)
    outputs = calculate_outputs(new_state)
    return new_state, outputs
```

### Component Interface Pattern

Components wrap kernels and handle graph integration:

```python
class ComponentName(Component):
    """Graph node that orchestrates one or more kernels."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        # Extract parameters for kernel
        self.kernel_params = extract_kernel_params(kwargs)
        # Initialize kernel state
        self.kernel_state = initialize_kernel_state(kwargs)
        # Store source references (resolved by loader)
        self.source_refs = extract_sources(kwargs)

    def step(self, date, global_data: dict) -> dict:
        """Execute one timestep."""
        # Get inputs from sources
        inputs = self.get_inputs_from_sources()

        # Call kernel
        new_state, outputs = kernel_function(
            inputs, self.kernel_params, self.kernel_state
        )

        # Update state
        self.kernel_state = new_state

        # Store outputs
        self.outputs = outputs
        return self.outputs
```

## Data Models

### Kernel Module Structure

Each kernel module contains:

1. **Parameter Classes**: Dataclasses or TypedDicts defining kernel parameters
2. **State Classes**: Dataclasses defining state variables
3. **Input/Output Classes**: Dataclasses defining I/O structures
4. **Core Function**: Pure function implementing the algorithm
5. **Helper Functions**: Supporting calculations

Example for Snow17 kernel:

```python
# waterlib/kernels/hydrology/snow17.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class Snow17Params:
    """Fixed parameters for Snow17 algorithm."""
    mfmax: float = 1.6
    mfmin: float = 0.6
    mbase: float = 0.0
    pxtemp1: float = 0.0
    pxtemp2: float = 1.0
    scf: float = 1.0
    nmf: float = 0.15
    plwhc: float = 0.04
    uadj: float = 0.05
    tipm: float = 0.15
    lapse_rate: float = 0.006

@dataclass
class Snow17State:
    """State variables for Snow17 algorithm."""
    w_i: float = 0.0      # Ice content (mm)
    w_q: float = 0.0      # Liquid water (mm)
    ait: float = 0.0      # Antecedent temperature index (°C)
    deficit: float = 0.0  # Heat deficit (mm)

@dataclass
class Snow17Inputs:
    """Inputs for one Snow17 timestep."""
    temp_c: float
    precip_mm: float
    elevation_m: float
    ref_elevation_m: float
    day_of_year: int
    days_in_year: int
    dt_hours: float

@dataclass
class Snow17Outputs:
    """Outputs from one Snow17 timestep."""
    runoff_mm: float
    swe_mm: float
    rain_mm: float
    snow_mm: float

def snow17_step(
    inputs: Snow17Inputs,
    params: Snow17Params,
    state: Snow17State
) -> Tuple[Snow17State, Snow17Outputs]:
    """
    Execute one timestep of Snow17 algorithm.

    Pure function with no side effects.
    """
    # Algorithm implementation
    # ...
    return new_state, outputs
```

### Component Wrapper Structure

Components maintain backward compatibility while using kernels:

```python
# waterlib/components/catchment.py

from waterlib.core.base import Component
from waterlib.kernels.hydrology.snow17 import snow17_step, Snow17Params, Snow17State
from waterlib.kernels.hydrology.awbm import awbm_step, AWBMParams, AWBMState

class Catchment(Component):
    """
    Catchment component that internally uses Snow17 and AWBM kernels.

    Users define this as a single component in YAML and don't need to
    wire Snow17 and AWBM separately.
    """

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

        # Extract and store kernel parameters
        self.snow17_params = Snow17Params(**kwargs.get('snow17_params', {}))
        self.awbm_params = AWBMParams(**kwargs.get('awbm_params', {}))

        # Initialize kernel states
        self.snow17_state = Snow17State(w_i=kwargs.get('initial_swe', 0.0))
        self.awbm_state = AWBMState(**kwargs.get('initial_stores', {}))

        # Store source references (resolved by loader)
        self.temp_source = None
        self.precip_source = None
        self.pet_source = None

    def step(self, date, global_data: dict) -> dict:
        """Execute one timestep using both kernels."""
        # Get inputs from global data or sources
        temp = global_data.get('temperature', 0.0)
        precip = global_data.get('precipitation', 0.0)
        pet = global_data.get('pet', 0.0)

        # Run Snow17 kernel
        snow17_inputs = Snow17Inputs(
            temp_c=temp,
            precip_mm=precip,
            elevation_m=self.elevation,
            ref_elevation_m=self.ref_elevation,
            day_of_year=date.timetuple().tm_yday,
            days_in_year=366 if date.year % 4 == 0 else 365,
            dt_hours=24.0
        )
        self.snow17_state, snow17_outputs = snow17_step(
            snow17_inputs, self.snow17_params, self.snow17_state
        )

        # Run AWBM kernel with Snow17 outputs
        awbm_inputs = AWBMInputs(
            precip_mm=snow17_outputs.runoff_mm,
            pet_mm=pet
        )
        self.awbm_state, awbm_outputs = awbm_step(
            awbm_inputs, self.awbm_params, self.awbm_state
        )

        # Package outputs
        self.outputs = {
            'runoff_m3d': awbm_outputs.runoff_mm * self.area_km2 * 1000.0,
            'swe_mm': snow17_outputs.swe_mm
        }
        return self.outputs
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Kernel Import Isolation

*For any* kernel module in `waterlib/kernels/`, parsing its imports should reveal no imports from `waterlib.components`.

**Validates: Requirements 1.3, 5.2**

### Property 2: Component Kernel Imports

*For any* component that uses kernels, all kernel imports should use absolute paths starting with `waterlib.kernels`.

**Validates: Requirements 5.1**

### Property 3: No Circular Dependencies

*For any* module in the codebase, building a dependency graph should show that kernels never depend on components (directly or transitively).

**Validates: Requirements 5.3**

### Property 4: Import Path Migration Completeness

*For any* Python file in the codebase, there should be no import statements using old paths like `from waterlib.components.snow17` for kernel code.

**Validates: Requirements 5.5**

### Property 5: Test Import Consistency

*For any* test file, kernel imports should use `waterlib.kernels` paths and component imports should use `waterlib.components` paths.

**Validates: Requirements 6.1, 6.2, 6.4**

### Property 6: Kernel __init__ Exports

*For any* kernel subdirectory __init__.py file, it should expose the main classes and functions from that subdirectory through __all__ or direct imports.

**Validates: Requirements 10.2**

### Property 7: WGEN Kernel Purity

*For any* import in `waterlib/kernels/climate/wgen.py`, there should be no imports from `waterlib.components` or graph-related modules.

**Validates: Requirements 8.2**

### Property 8: File Move Consistency

*For any* file that was moved from components to kernels, after the move all imports referencing that file should use the new path.

**Validates: Requirements 9.2**

## Error Handling

### Migration Errors

1. **Import Errors**: If old import paths are used after refactoring
   - Provide clear error messages indicating the old path and new path
   - Example: "ImportError: cannot import 'Snow17' from 'waterlib.components.snow17'. Snow17 has moved to 'waterlib.kernels.hydrology.snow17'"

2. **Missing Kernel Files**: If a component tries to import a kernel that doesn't exist
   - Provide clear error message with expected location
   - Example: "ImportError: cannot import 'snow17_step' from 'waterlib.kernels.hydrology.snow17'. Check that the file exists."

3. **Circular Dependency Detection**: If a kernel accidentally imports from components
   - Fail fast during import with clear error
   - Example: "ImportError: Kernel modules cannot import from waterlib.components. Found import in waterlib/kernels/hydrology/snow17.py"

### Runtime Errors

1. **Kernel Function Errors**: If a kernel function raises an exception
   - Wrap with context about which component called it
   - Include input values and parameters for debugging
   - Example: "Error in Catchment 'upper_basin' calling snow17_step: ValueError: temperature must be numeric, got 'None'"

2. **State Validation**: If kernel state becomes invalid
   - Validate state after each kernel call
   - Provide clear error about which state variable is invalid
   - Example: "Invalid state in Snow17: w_i cannot be negative, got -5.2"

### Backward Compatibility

1. **Deprecation Warnings**: For any code still using old import paths
   - Issue DeprecationWarning with migration instructions
   - Example: "DeprecationWarning: Importing Snow17 from waterlib.components is deprecated. Use 'from waterlib.kernels.hydrology.snow17 import snow17_step' instead."

2. **Compatibility Shims**: Temporarily maintain old import paths
   - Create stub files in old locations that import from new locations
   - Remove after one release cycle

## Testing Strategy

### Unit Testing

The system will use **pytest** as the testing framework.

**Unit Test Coverage:**

1. **Kernel Tests**: Test each kernel function in isolation
   - Test with known input/output pairs
   - Test edge cases (zero values, extreme values)
   - Test state transitions
   - Test parameter validation
   - Example: Test snow17_step with various temperature/precipitation combinations

2. **Component Tests**: Test components that use kernels
   - Test that components correctly call kernels
   - Test that components correctly package kernel outputs
   - Test that components handle kernel errors gracefully
   - Example: Test Catchment component orchestration of Snow17 and AWBM

3. **Import Tests**: Test that imports work correctly
   - Test that kernels can be imported from new paths
   - Test that components can import kernels
   - Test that old import paths are removed
   - Example: `from waterlib.kernels.hydrology import snow17_step`

4. **Integration Tests**: Test complete workflows
   - Test that models using refactored components still work
   - Test that YAML loading works with new structure
   - Test that simulation execution works end-to-end

**Example Unit Test:**
```python
def test_snow17_kernel_basic():
    """Test Snow17 kernel with simple inputs."""
    from waterlib.kernels.hydrology.snow17 import snow17_step, Snow17Params, Snow17State, Snow17Inputs

    params = Snow17Params(mfmax=1.6, mfmin=0.6)
    state = Snow17State(w_i=50.0, w_q=0.0)
    inputs = Snow17Inputs(
        temp_c=-5.0,
        precip_mm=10.0,
        elevation_m=1500.0,
        ref_elevation_m=1000.0,
        day_of_year=15,
        days_in_year=365,
        dt_hours=24.0
    )

    new_state, outputs = snow17_step(inputs, params, state)

    # Snow should accumulate at -5°C
    assert new_state.w_i > state.w_i
    assert outputs.snow_mm > 0
    assert outputs.rain_mm == 0
```

### Property-Based Testing

The system will use **Hypothesis** as the property-based testing framework.

**Property-Based Test Configuration:**
- Minimum 100 iterations per property test
- Each test must reference its corresponding design property using the format: `**Feature: kernels-refactor, Property {number}: {property_text}**`

**Property Test Coverage:**

1. **Import Isolation**: Generate random kernel files and verify no component imports
2. **Import Path Consistency**: Generate random component files and verify kernel imports use correct paths
3. **Dependency Graph**: Build dependency graph and verify no cycles between kernels and components
4. **State Validity**: Generate random kernel inputs and verify state remains valid

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import ast
import os

@given(kernel_file=st.sampled_from(get_all_kernel_files()))
def test_kernel_import_isolation(kernel_file):
    """
    **Feature: kernels-refactor, Property 1: Kernel Import Isolation**

    For any kernel module, parsing its imports should reveal no imports
    from waterlib.components.
    """
    with open(kernel_file, 'r') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ''
            assert not module.startswith('waterlib.components'), \
                f"Kernel {kernel_file} imports from components: {module}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith('waterlib.components'), \
                    f"Kernel {kernel_file} imports from components: {alias.name}"
```

### Testing Approach

1. **Test-First for Kernels**: Write kernel tests before extracting kernel code
2. **Regression Testing**: Ensure all existing tests pass after refactor
3. **Import Validation**: Automated checks for import path correctness
4. **Continuous Integration**: Run full test suite on every commit

### Test Organization

```
tests/
├── unit/
│   ├── kernels/
│   │   ├── test_snow17_kernel.py
│   │   ├── test_awbm_kernel.py
│   │   ├── test_weir_kernel.py
│   │   └── test_et_kernel.py
│   ├── components/
│   │   ├── test_catchment.py
│   │   ├── test_reservoir.py
│   │   └── ...
│   └── test_imports.py
├── property/
│   ├── test_import_isolation.py
│   ├── test_import_consistency.py
│   └── test_dependency_graph.py
└── integration/
    ├── test_full_simulation.py
    └── test_yaml_loading.py
```

## Implementation Phases

### Phase 1: Create Kernel Directory Structure

**Goal**: Establish the new directory structure

1. Create `waterlib/kernels/` directory
2. Create `waterlib/kernels/hydrology/` subdirectory with `__init__.py`
3. Create `waterlib/kernels/hydraulics/` subdirectory with `__init__.py`
4. Create `waterlib/kernels/climate/` subdirectory with `__init__.py`
5. Create root `waterlib/kernels/__init__.py`

**Deliverable**: Empty kernel directory structure ready for code

### Phase 2: Extract and Move Hydrology Kernels

**Goal**: Move Snow17 and AWBM to kernels

1. Extract pure Snow17 algorithm from `waterlib/components/snow17.py`
2. Create `waterlib/kernels/hydrology/snow17.py` with pure functions
3. Extract pure AWBM algorithm from `waterlib/components/awbm.py`
4. Create `waterlib/kernels/hydrology/awbm.py` with pure functions
5. Update `waterlib/kernels/hydrology/__init__.py` to export functions
6. Write unit tests for extracted kernels

**Deliverable**: Snow17 and AWBM kernels with tests

### Phase 3: Extract and Move Hydraulics Kernels

**Goal**: Move weir equations to kernels

1. Extract weir equation logic from `waterlib/components/weir.py`
2. Create `waterlib/kernels/hydraulics/weir.py` with pure functions
3. Extract spillway logic if separate
4. Update `waterlib/kernels/hydraulics/__init__.py` to export functions
5. Write unit tests for extracted kernels

**Deliverable**: Weir and spillway kernels with tests

### Phase 4: Extract and Move Climate Kernels

**Goal**: Move ET and WGEN to kernels

1. Extract Hargreaves-Samani from `waterlib/components/hargreaves.py`
2. Create `waterlib/kernels/climate/et.py` with ET calculation functions
3. Move WGEN from `waterlib/climate.py` (or create if doesn't exist)
4. Create `waterlib/kernels/climate/wgen.py` with stochastic generation
5. Update `waterlib/kernels/climate/__init__.py` to export functions
6. Write unit tests for extracted kernels

**Deliverable**: ET and WGEN kernels with tests

### Phase 5: Update Components to Use Kernels

**Goal**: Refactor components to import and use kernels

1. Update `waterlib/components/catchment.py` to import from `waterlib.kernels.hydrology`
2. Update `waterlib/components/reservoir.py` to import from `waterlib.kernels.hydraulics`
3. Update `waterlib/climate.py` to import from `waterlib.kernels.climate`
4. Remove old algorithm code from component files (keep only orchestration)
5. Update all component imports to use absolute kernel paths

**Deliverable**: Components using kernels with clean separation

### Phase 6: Update Tests

**Goal**: Fix all test imports and ensure tests pass

1. Update test imports to use new kernel paths
2. Add new kernel-specific tests
3. Update component tests to reflect new structure
4. Run full test suite and fix any failures
5. Add property tests for import isolation

**Deliverable**: All tests passing with new structure

### Phase 7: Cleanup and Documentation

**Goal**: Remove old code and document changes

1. Remove old component files that were moved to kernels (if any)
2. Add deprecation warnings for any backward compatibility shims
3. Update documentation to explain kernel vs component distinction
4. Update developer guide with kernel development patterns
5. Create migration guide for external users

**Deliverable**: Clean codebase with updated documentation

## Migration Strategy

### For Internal Development

1. **Branch Strategy**: Create feature branch for refactor
2. **Incremental Commits**: Commit after each phase
3. **Test Continuously**: Run tests after each change
4. **Review Before Merge**: Full code review of refactor

### For External Users

1. **Backward Compatibility**: Maintain old import paths temporarily with deprecation warnings
2. **Migration Guide**: Provide clear guide for updating imports
3. **Version Bump**: Mark as minor version bump (new structure, backward compatible)
4. **Deprecation Timeline**: Remove old paths in next major version

### Breaking Changes

- Import paths change for kernel code
- Component internal structure changes (but external API remains same)
- Test import paths change

These will be documented in CHANGELOG and migration guide.

## Dependencies

### Core Dependencies

- **Python**: >=3.8 (for dataclasses)
- **typing**: For type hints in kernel interfaces
- **dataclasses**: For kernel parameter/state classes

### Testing Dependencies

- **pytest**: Unit testing framework
- **hypothesis**: Property-based testing
- **ast**: For parsing imports in tests

### No New External Dependencies

The refactor is purely organizational and requires no new external packages.

## Future Extensions

### Additional Kernels

- **Penman-Monteith ET**: Add to `waterlib/kernels/climate/et.py`
- **Priestley-Taylor ET**: Add to `waterlib/kernels/climate/et.py`
- **SCS Curve Number**: Add to `waterlib/kernels/hydrology/runoff.py`
- **Muskingum Routing**: Add to `waterlib/kernels/hydraulics/routing.py`

### Kernel Optimization

- **Numba JIT**: Add @jit decorators to performance-critical kernels
- **Vectorization**: Vectorize kernels for batch processing
- **Cython**: Compile performance-critical kernels to C

### Kernel Testing

- **Benchmark Suite**: Performance benchmarks for each kernel
- **Validation Data**: Compare kernel outputs against reference implementations
- **Sensitivity Analysis**: Automated parameter sensitivity testing
