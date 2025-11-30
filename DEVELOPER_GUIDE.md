# Waterlib Developer Guide

**Last Updated:** 2025-11-27
**Audience:** Contributors and developers extending waterlib

---

## 1. Introduction

This guide provides the technical foundation for developing waterlib. Whether you're adding a new component, fixing a bug, or extending the framework, this document will help you understand the architecture, patterns, and conventions used throughout the codebase.

### 1.1 What This Guide Covers

- Core architecture and design patterns
- Component development workflow
- Testing strategy and requirements
- Code style and conventions
- Common development tasks
- Debugging and troubleshooting

### 1.2 Prerequisites

Before contributing, you should be familiar with:
- Python 3.8+ (type hints, dataclasses, ABC)
- Object-oriented programming
- Graph theory basics (topological sort, DAGs)
- YAML configuration
- Git workflow (branches, PRs, commits)

---

## 2. Architecture Overview

### 2.1 Core Design Principles

**Library-First Approach**
- Users interact primarily through Python API, not CLI
- YAML is configuration, not a DSL
- One function call to run simulations: `run_simulation(model)`

**Separation of Concerns**
- **Components**: Domain logic (hydrology, storage, demand)
- **Model**: Container and orchestration
- **Simulation**: Execution engine and time loop
- **Drivers**: Global data providers (climate)

**Explicit Over Implicit**
- Node positions in YAML (not auto-layout)
- Clear error messages with context
- Type hints throughout

### 2.2 Module Structure

```
waterlib/
├── __init__.py              # Public API exports
├── core/                    # Core framework
│   ├── base.py             # Component ABC
│   ├── simple_model.py     # Model container
│   ├── simulation.py       # Simulation engine with file logging
│   ├── loader.py           # YAML loading with inline connection parsing
│   ├── config.py           # Configuration schemas
│   ├── scaffold.py         # Project scaffolding utilities
│   ├── drivers.py          # Driver pattern for climate
│   ├── exceptions.py       # Custom exceptions
│   ├── results.py          # Results handling
│   └── validation.py       # Model validation
├── kernels/                 # 🆕 Pure computational algorithms
│   ├── __init__.py
│   ├── hydrology/          # Rainfall-runoff algorithms
│   │   ├── __init__.py
│   │   ├── snow17.py      # Snow17 kernel (pure functions)
│   │   ├── awbm.py        # AWBM kernel (pure functions)
│   │   └── runoff.py      # Runoff utilities
│   ├── hydraulics/         # Flow structure algorithms
│   │   ├── __init__.py
│   │   ├── weir.py        # Weir equations (pure functions)
│   │   └── spillway.py    # Spillway calculations
│   └── climate/            # Climate and ET algorithms
│       ├── __init__.py
│       ├── et.py          # ET methods (Hargreaves, etc.)
│       └── wgen.py        # WGEN stochastic generator
├── components/              # Graph-connectable components
│   ├── catchment.py        # Orchestrates Snow17+AWBM kernels
│   ├── reservoir.py        # Uses spillway kernel
│   ├── pump.py             # Pump (constant/variable)
│   ├── demand.py           # Demand (municipal/agricultural)
│   ├── diversion.py        # River diversion
│   ├── junction.py         # Flow aggregation
│   └── ...
├── climate.py               # Climate utilities (uses kernels)
├── plotting.py              # Visualization utilities
├── analysis/                # Analysis tools
│   ├── logger.py           # Results logging
│   └── plotting.py         # Advanced plotting
└── utils/                   # Utility functions
    ├── interpolation.py    # Interpolation helpers
    └── path_validation.py  # Path validation
```

### 2.2.1 Kernels vs Components Architecture

**NEW: Kernels Layer** (`waterlib/kernels/`)

Kernels are pure computational algorithms with no graph dependencies:

- **Purpose**: Implement domain-specific calculations (hydrology, hydraulics, climate)
- **Pattern**: Pure functions with dataclasses for inputs/outputs/state
- **Dependencies**: Can only import from other kernels, never from components
- **Testing**: Can be tested in complete isolation
- **Examples**:
  - `snow17_step()` - Snow accumulation/melt physics
  - `awbm_step()` - Rainfall-runoff transformation
  - `weir_discharge()` - Weir flow equation
  - `hargreaves_et()` - ET calculation

**Components Layer** (`waterlib/components/`)

Components are graph nodes that orchestrate kernels:

- **Purpose**: Handle I/O, state management, and graph integration
- **Pattern**: Classes inheriting from `Component` base class
- **Dependencies**: Import and use kernels, never implement core algorithms
- **Testing**: Test orchestration logic and kernel integration
- **Examples**:
  - `Catchment` - Orchestrates Snow17 and AWBM kernels
  - `Reservoir` - Uses spillway kernel for overflow calculations
  - `Pump` - Pure component (no kernel needed)

**Dependency Flow:**
```
YAML Model → Components → Kernels
            (orchestration) (algorithms)
```

**Key Principle:** Kernels never import from components. This ensures:
- Kernels are reusable and testable in isolation
- Clear separation between "what to calculate" (kernels) and "how to wire it" (components)
- Easy to add new components that use existing kernels

### 2.3 Architecture Diagrams

For visual representations of the architecture, see **[Architecture Diagrams](docs/ARCHITECTURE_DIAGRAM.md)**, which includes:

- **System Architecture Overview** - Complete system with all layers
- **Dependency Flow** - How dependencies flow through the system
- **Kernel Organization** - Structure of the kernels directory
- **Component-Kernel Relationship** - How components use kernels
- **Kernel Function Pattern** - Standard pattern for kernel functions
- **Simulation Execution Flow** - Sequence diagram of simulation
- **Data Flow Example** - Detailed data flow through Catchment component
- **Testing Strategy** - Test pyramid visualization
- **Module Dependencies** - External and internal dependencies

These diagrams use Mermaid format and can be viewed in any Markdown viewer that supports Mermaid (GitHub, VS Code, etc.).

### 2.4 Key Classes and Their Roles

| Class/Module | Location | Purpose |
|--------------|----------|---------|
| **Core Framework** | | |
| `Component` | `core.base` | Abstract base for all components |
| `Model` | `core.simple_model` | Container for components and connections |
| `SimulationEngine` | `core.simulation` | Executes simulation loop with file logging |
| `load_model()` | `core.loader` | Loads YAML, parses inline connections, builds graph |
| `create_project()` | `core.scaffold` | Creates scaffolded project structure |
| `Driver` | `core.drivers` | Abstract base for climate data providers |
| `DriverRegistry` | `core.drivers` | Manages global drivers |
| `Results` | `core.results` | Wraps simulation output DataFrame |
| **Kernels (Pure Algorithms)** | | |
| `snow17_step()` | `kernels.hydrology.snow17` | Snow accumulation/melt calculation |
| `awbm_step()` | `kernels.hydrology.awbm` | AWBM rainfall-runoff calculation |
| `weir_discharge()` | `kernels.hydraulics.weir` | Weir flow equation |
| `hargreaves_et()` | `kernels.climate.et` | Hargreaves-Samani ET calculation |
| **Components (Graph Nodes)** | | |
| `Catchment` | `components.catchment` | Orchestrates Snow17 + AWBM kernels |
| `Reservoir` | `components.reservoir` | Storage with spillway (uses weir kernel) |
| `Pump` | `components.pump` | Flow control component |
| `Demand` | `components.demand` | Water demand simulation |

---

## 3. Kernel Development

### 3.1 When to Create a Kernel

Create a kernel when you have:
- A pure computational algorithm (hydrology, hydraulics, climate)
- Logic that could be reused by multiple components
- Complex calculations that benefit from isolated testing
- Domain-specific physics or equations

**Don't create a kernel for:**
- Simple orchestration logic
- Graph-specific operations
- I/O handling
- State management

### 3.2 Kernel Structure Pattern

All kernels follow this pattern:

```python
# waterlib/kernels/domain/algorithm.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class AlgorithmParams:
    """Fixed parameters for the algorithm."""
    param1: float = 1.0
    param2: float = 2.0

@dataclass
class AlgorithmState:
    """State variables that persist between timesteps."""
    state_var1: float = 0.0
    state_var2: float = 0.0

@dataclass
class AlgorithmInputs:
    """Inputs for one timestep."""
    input1: float
    input2: float

@dataclass
class AlgorithmOutputs:
    """Outputs from one timestep."""
    output1: float
    output2: float

def algorithm_step(
    inputs: AlgorithmInputs,
    params: AlgorithmParams,
    state: AlgorithmState
) -> Tuple[AlgorithmState, AlgorithmOutputs]:
    """
    Execute one timestep of the algorithm.

    This is a pure function with no side effects.

    Args:
        inputs: Current timestep inputs
        params: Fixed algorithm parameters
        state: Current state variables

    Returns:
        Tuple of (new_state, outputs)
    """
    # Perform calculations
    result = params.param1 * inputs.input1 + params.param2

    # Update state
    new_state = AlgorithmState(
        state_var1=state.state_var1 + result,
        state_var2=result
    )

    # Create outputs
    outputs = AlgorithmOutputs(
        output1=result,
        output2=new_state.state_var1
    )

    return new_state, outputs
```

### 3.3 Creating a New Kernel

**Step 1: Choose the right subdirectory**
- `kernels/hydrology/` - Rainfall-runoff, snow, infiltration
- `kernels/hydraulics/` - Flow equations, routing, structures
- `kernels/climate/` - ET, weather generation, climate indices

**Step 2: Create the kernel module**

```python
# waterlib/kernels/hydrology/my_algorithm.py
from dataclasses import dataclass
from typing import Tuple
import math

@dataclass
class MyAlgorithmParams:
    """Parameters for my algorithm.

    Attributes:
        coefficient: Scaling coefficient [dimensionless]
        threshold: Threshold value [mm]
    """
    coefficient: float = 1.0
    threshold: float = 10.0

@dataclass
class MyAlgorithmState:
    """State variables for my algorithm.

    Attributes:
        storage: Current storage [mm]
    """
    storage: float = 0.0

@dataclass
class MyAlgorithmInputs:
    """Inputs for one timestep.

    Attributes:
        precipitation: Precipitation [mm/day]
        temperature: Temperature [°C]
    """
    precipitation: float
    temperature: float

@dataclass
class MyAlgorithmOutputs:
    """Outputs from one timestep.

    Attributes:
        runoff: Generated runoff [mm/day]
        storage: Current storage [mm]
    """
    runoff: float
    storage: float

def my_algorithm_step(
    inputs: MyAlgorithmInputs,
    params: MyAlgorithmParams,
    state: MyAlgorithmState
) -> Tuple[MyAlgorithmState, MyAlgorithmOutputs]:
    """Execute one timestep of my algorithm.

    Implements the equation: Q = C * max(S - T, 0)

    Args:
        inputs: Current timestep inputs
        params: Fixed algorithm parameters
        state: Current state variables

    Returns:
        Tuple of (new_state, outputs)
    """
    # Update storage with precipitation
    new_storage = state.storage + inputs.precipitation

    # Calculate runoff
    excess = max(new_storage - params.threshold, 0.0)
    runoff = params.coefficient * excess

    # Update storage after runoff
    new_storage -= runoff

    # Create new state
    new_state = MyAlgorithmState(storage=new_storage)

    # Create outputs
    outputs = MyAlgorithmOutputs(
        runoff=runoff,
        storage=new_storage
    )

    return new_state, outputs

# Helper functions (if needed)
def _calculate_helper(value: float) -> float:
    """Private helper function."""
    return math.sqrt(max(value, 0.0))
```

**Step 3: Update __init__.py**

```python
# waterlib/kernels/hydrology/__init__.py
from waterlib.kernels.hydrology.my_algorithm import (
    my_algorithm_step,
    MyAlgorithmParams,
    MyAlgorithmState,
    MyAlgorithmInputs,
    MyAlgorithmOutputs,
)

__all__ = [
    'my_algorithm_step',
    'MyAlgorithmParams',
    'MyAlgorithmState',
    'MyAlgorithmInputs',
    'MyAlgorithmOutputs',
]
```

**Step 4: Write kernel tests**

```python
# tests/kernels/test_my_algorithm.py
import pytest
from waterlib.kernels.hydrology.my_algorithm import (
    my_algorithm_step,
    MyAlgorithmParams,
    MyAlgorithmState,
    MyAlgorithmInputs,
)

def test_my_algorithm_basic():
    """Test basic algorithm operation."""
    params = MyAlgorithmParams(coefficient=1.0, threshold=10.0)
    state = MyAlgorithmState(storage=5.0)
    inputs = MyAlgorithmInputs(precipitation=10.0, temperature=15.0)

    new_state, outputs = my_algorithm_step(inputs, params, state)

    # Storage should be 5 + 10 = 15
    # Excess = 15 - 10 = 5
    # Runoff = 1.0 * 5 = 5
    # Final storage = 15 - 5 = 10
    assert outputs.runoff == 5.0
    assert outputs.storage == 10.0
    assert new_state.storage == 10.0

def test_my_algorithm_no_runoff():
    """Test when storage is below threshold."""
    params = MyAlgorithmParams(coefficient=1.0, threshold=10.0)
    state = MyAlgorithmState(storage=2.0)
    inputs = MyAlgorithmInputs(precipitation=3.0, temperature=15.0)

    new_state, outputs = my_algorithm_step(inputs, params, state)

    # Storage = 2 + 3 = 5, below threshold
    assert outputs.runoff == 0.0
    assert outputs.storage == 5.0
```

### 3.4 Kernel Best Practices

**Pure Functions**
- No side effects (no modifying global state, no I/O)
- Same inputs always produce same outputs
- Deterministic and reproducible

**Dataclasses for Structure**
- Use `@dataclass` for all parameter/state/input/output structures
- Include type hints for all fields
- Add docstrings describing units and meaning

**No Graph Dependencies**
- Never import from `waterlib.components`
- Never import from `waterlib.core` (except exceptions)
- Only import from other kernels or standard library
- **Enforcement**: This is enforced via flake8 linting and pre-commit hooks (see Section 3.4.1)

**Clear Units**
- Document units in docstrings
- Use consistent units throughout (mm, m³, °C, etc.)
- Convert units at component boundary, not in kernel

**Validation**
- Validate inputs at component level, not kernel level
- Kernels assume valid inputs for performance
- Use assertions for debugging, not validation

### 3.4.1 Architectural Enforcement: Kernel Purity

**Why This Matters**

Kernels are designed as pure computational functions to enable future scaling optimizations. If kernels ever need to be rewritten in Rust or C++ for performance, they must be completely isolated from the component graph structure. This architectural constraint is **strictly enforced** to prevent accidental coupling.

**The Rule**

> **Kernels MUST NOT import from `waterlib.components`**

This ensures:
- Kernels remain pure functions with no graph dependencies
- Future migration to compiled languages (Rust/C++) is straightforward
- Parallel execution and GPU acceleration remain possible
- Mathematical algorithms are portable and reusable

**Automated Enforcement**

This rule is enforced through multiple layers:

1. **Flake8 Linting** (`.flake8` configuration)
   - Custom flake8 plugin checks all `waterlib/kernels/` files
   - Error code: **I900** - "Kernel modules must not import from waterlib.components"
   - Runs during development and CI/CD

2. **Pre-commit Hooks** (`.pre-commit-config.yaml`)
   - Blocks commits that violate the import restriction
   - Fast local check before code reaches CI
   - Script: `scripts/check_kernel_imports.py`

3. **Custom Linter** (`waterlib_lint.py`)
   - AST-based analysis for accurate detection
   - Catches both `from waterlib.components import X` and `import waterlib.components.X`

**Running the Checks**

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run flake8 manually
flake8 waterlib/kernels/

# Run pre-commit on all files
pre-commit run --all-files

# Test the kernel import checker directly
python scripts/check_kernel_imports.py waterlib/kernels/**/*.py
```

**What Happens If You Violate This?**

If you attempt to import from `waterlib.components` in a kernel file:

```python
# ❌ FORBIDDEN - Will fail CI and pre-commit
from waterlib.components.reservoir import Reservoir

# ❌ FORBIDDEN - Will fail CI and pre-commit
import waterlib.components.catchment
```

You'll get:
- Pre-commit hook failure blocking your commit
- Flake8 error during CI/CD
- Clear error message explaining the architectural constraint

**Correct Pattern**

If you need shared logic between kernels and components:
1. Put pure math/algorithms in kernels
2. Put orchestration and graph logic in components
3. Components import and call kernels (never the reverse)

```python
# ✅ CORRECT - Component imports kernel
from waterlib.kernels.hydrology.awbm import awbm_step, AWBMParams

# ✅ CORRECT - Kernel imports other kernels
from waterlib.kernels.climate.et import calculate_pet

# ✅ CORRECT - Kernel imports standard library
import numpy as np
from dataclasses import dataclass
```

---

### 3.5 Backward Compatibility Policy

**Strict Rule: Zero Legacy Support**

During the current development phase, we prioritize **architectural correctness and code cleanliness over backward compatibility**.

* **No Fallbacks:** Do not write logic to support deprecated YAML structures or old API signatures.
* **Fail Fast:** If a schema changes, the loader must raise a `ConfigurationError` for old formats immediately. Do not attempt to "guess" or patch the data.
* **Update Roots:** When changing an API or schema, the `scaffold.py` templates must be updated in the same commit.
* **No Deprecation Warnings:** Do not clutter the logs with deprecation warnings. If a feature is removed, it is gone.

**Rationale:** We currently have no external user base to support. Implementing backward compatibility at this stage introduces technical debt that slows down iteration and complicates the codebase with "dead" logic.

**Example: Site Configuration Refactoring**

When we moved `latitude` and `elevation_m` from `settings.climate.wgen_config` to a top-level `site:` block, we:

1. ✅ Updated `parse_site_config()` to require the new `site:` block
2. ✅ Removed all legacy fallback code immediately
3. ✅ Updated `scaffold.py` templates in the same commit
4. ✅ Made the error message clear and actionable

We did **NOT**:
- ❌ Add deprecation warnings
- ❌ Support both old and new formats
- ❌ Create adapter layers to translate old configs

**Migration Path for Breaking Changes**

If you introduce a breaking change:

1. Update the schema or API in one clean commit
2. Update all templates in `scaffold.py`
3. Update documentation (`README.md`, `API_REFERENCE.md`)
4. Write a clear error message that explains the new format
5. Test that old formats fail with helpful error messages

---

## 4. Component Development

### 4.1 Simulation Execution Flow

The simulation engine executes each timestep in three phases:

**Phase 1: Climate Data Update**
- Climate data for the current timestep is retrieved from `ClimateManager`
- The persistent `DriverRegistry` is updated with current values
- Drivers (precipitation, temperature, ET) are registered/refreshed

**Phase 2: Pre-Step Data Transfer** (`_transfer_data()`)
- Component outputs from the previous timestep are transferred to inputs
- This phase handles three connection types:
  1. **Explicit 'inflows'**: Multiple sources aggregated (Junction, Reservoir)
  2. **Single 'source'**: One-to-one connection (Demand → Reservoir)
  3. **Registered data_connections**: Formal connection tracking from loader
- All component `inputs` dictionaries are cleared and repopulated
- Ensures components have access to data from their dependencies

**Phase 3: Component Execution**
- Components execute in topological order (respecting dependencies)
- Each component's `step(date, drivers)` method is called
- Components read from `self.inputs` and write to `self.outputs`
- Results are collected and returned

**Critical Insight:** The data transfer phase was added to fix a critical bug where components were reading stale data from previous timesteps. This phase ensures that all input data is fresh before any component executes.

### 4.2 Component Lifecycle

Every component follows this lifecycle:

```
1. __init__()              - Parse YAML parameters, validate, initialize state
2. step(date, drivers)     - Called once per timestep, performs calculations
3. outputs                 - Dictionary of output values returned from step()
```

**Component API Signature:**
```python
def step(self, date: datetime, drivers) -> dict:
    """Execute one timestep and return outputs.

    Args:
        date: Current simulation datetime
        drivers: DriverRegistry instance providing climate data

    Returns:
        Dictionary of output values for this timestep
    """
```

**Key Points:**
- `date`: Current simulation datetime for temporal calculations
- `drivers`: DriverRegistry providing climate data access
- `self.inputs`: Dictionary of values from connected components (populated in Phase 2)
- `self.outputs`: Dictionary of values returned to downstream components

### 4.2 Creating a Component That Uses Kernels

When creating a component that uses kernels, follow this pattern:

```python
# waterlib/components/my_component.py
from waterlib.core.base import Component
from waterlib.kernels.hydrology.my_algorithm import (
    my_algorithm_step,
    MyAlgorithmParams,
    MyAlgorithmState,
    MyAlgorithmInputs,
)
from datetime import datetime
from typing import Dict, Any

class MyComponent(Component):
    """Component that uses my_algorithm kernel.

    This component orchestrates the my_algorithm kernel and handles
    I/O, state management, and graph integration.

    Parameters:
        coefficient: Algorithm coefficient [dimensionless]
        threshold: Threshold value [mm]
        initial_storage: Initial storage [mm]

    Inputs:
        precipitation: From drivers (DriverRegistry) [mm/day]
        temperature: From drivers (DriverRegistry) [°C]

    Outputs:
        runoff: Generated runoff [mm/day]
        storage: Current storage [mm]
    """

    def __init__(self, name: str, coefficient: float = 1.0,
                 threshold: float = 10.0, initial_storage: float = 0.0,
                 meta: Dict[str, Any] = None, **kwargs):
        super().__init__(name, meta, **kwargs)

        # Create kernel parameter object
        self.kernel_params = MyAlgorithmParams(
            coefficient=coefficient,
            threshold=threshold
        )

        # Initialize kernel state
        self.kernel_state = MyAlgorithmState(storage=initial_storage)

        # Initialize outputs
        self.outputs = {
            'runoff': 0.0,
            'storage': initial_storage,
        }

        self.logger.info(
            f"Initialized {name} with coefficient={coefficient}, "
            f"threshold={threshold}"
        )

    def step(self, date: datetime, drivers) -> dict:
        """Execute one timestep using the kernel."""
        # Get inputs from drivers (DriverRegistry)
        precip = drivers.get('precipitation').get_value(date)
        temp = drivers.get('temperature').get_value(date)

        # Create kernel input object
        kernel_inputs = MyAlgorithmInputs(
            precipitation=precip,
            temperature=temp
        )

        # Call kernel
        self.kernel_state, kernel_outputs = my_algorithm_step(
            kernel_inputs,
            self.kernel_params,
            self.kernel_state
        )

        # Package outputs for graph
        self.outputs = {
            'runoff': kernel_outputs.runoff,
            'storage': kernel_outputs.storage,
        }

        return self.outputs.copy()
```

### 4.3 Creating a New Component (Without Kernels)

**Step 1: Create the class with Pydantic validation**

```python
# waterlib/components/my_component.py
from waterlib.core.base import Component
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator

class MyComponentConfig(BaseModel):
    """Validated configuration for MyComponent.

    Attributes:
        param1: Description [units]
        param2: Description [units]
    """
    model_config = {'extra': 'forbid'}  # Reject unknown parameters

    param1: float = Field(gt=0, description="Must be positive")
    param2: float = Field(ge=0, le=100, description="Range 0-100")

    @field_validator('param1')
    @classmethod
    def validate_param1_reasonable(cls, v):
        """Additional validation beyond type constraints."""
        if v > 1000:
            raise ValueError(f"param1={v} seems unreasonably high")
        return v

class MyComponent(Component):
    """Brief description of what this component does.

    Longer description with equations, references, etc.

    Parameters:
        param1: Description [units]
        param2: Description [units]

    Inputs:
        input1: Description [units]

    Outputs:
        output1: Description [units]
    """

    def __init__(self, name: str, param1: float, param2: float,
                 meta: Dict[str, Any] = None, **kwargs):
        super().__init__(name, meta, **kwargs)

        # Validate parameters using Pydantic
        try:
            config = MyComponentConfig(param1=param1, param2=param2)
        except Exception as e:
            raise ValueError(
                f"Component '{name}' configuration error: {e}"
            ) from e

        # Store validated parameters
        self.param1 = config.param1
        self.param2 = config.param2

        # Initialize state
        self.state_var = 0.0

        self.logger.info(f"Initialized {name} with param1={param1}")

    def step(self, date: datetime, drivers) -> dict:
        """Execute one timestep."""
        # Get inputs from connected components
        input1 = self.inputs.get('input1', 0.0)

        # Get climate data using type-safe Driver API (preferred)
        precip = drivers.climate.precipitation.get_value(date)
        temp = drivers.climate.temperature.get_value(date)

        # Legacy string-based API still supported (being phased out)
        # precip = drivers.get('precipitation').get_value(date)

        # Perform calculations
        output1 = self.param1 * input1 + self.param2

        # Update state
        self.state_var += output1

        # Store and return outputs
        self.outputs = {
            'output1': output1,
            'state_var': self.state_var,
        }
        return self.outputs.copy()
```

**Why Pydantic?**

Pydantic validation provides several advantages over manual validation:

- **Type Safety**: Automatic type checking and coercion (e.g., `"1.5"` → `1.5`)
- **Declarative**: Constraints defined with the field, not scattered in `__init__`
- **Clear Errors**: Detailed validation messages with field names and values
- **Extra Fields**: `extra='forbid'` catches typos in YAML files
- **Composable**: Validators can be reused across components
- **Self-Documenting**: Field descriptions serve as inline documentation

**Common Pydantic Patterns:**

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class ExampleConfig(BaseModel):
    """Example configuration patterns."""
    model_config = {'extra': 'forbid'}

    # Numeric constraints
    positive: float = Field(gt=0)
    percentage: float = Field(ge=0, le=100)
    count: int = Field(ge=1)

    # String constraints
    mode: str = Field(pattern=r'^(simple|complex)$')
    name: str = Field(min_length=1, max_length=50)

    # Optional with default
    optional_param: float = Field(default=1.0, ge=0)

    # Field-level validation
    @field_validator('positive')
    @classmethod
    def check_reasonable(cls, v):
        if v > 1e6:
            raise ValueError(f"Value {v} seems unreasonably large")
        return v

    # Cross-field validation
    @model_validator(mode='after')
    def check_consistency(self):
        if self.positive < self.percentage:
            raise ValueError("positive must be >= percentage")
        return self
```

**Handling Mutable Types:**

When using mutable default values (dict, list, set), always deep copy to prevent reference mutation:

```python
from copy import deepcopy

class ConfigWithMutables(BaseModel):
    """Configuration with mutable types."""
    my_dict: dict = Field(default_factory=dict)
    my_list: list = Field(default_factory=list)

class ComponentWithMutables(Component):
    def __init__(self, name: str, config_dict: dict = None, **kwargs):
        super().__init__(name, **kwargs)

        config = ConfigWithMutables(my_dict=config_dict or {})

        # Deep copy mutable values to prevent reference sharing
        self.my_dict = deepcopy(config.my_dict)
        self.my_list = deepcopy(config.my_list)
```

**Step 2: Register in component factory**

```python
# waterlib/components/__init__.py
from waterlib.components.my_component import MyComponent

COMPONENT_REGISTRY = {
    'MyComponent': MyComponent,
    # ... other components
}
```

**Step 3: Write tests**

```python
# tests/test_my_component.py
import pytest
from datetime import datetime
from waterlib.components.my_component import MyComponent, MyComponentConfig

def test_my_component_initialization():
    """Test basic component initialization."""
    comp = MyComponent(name='test', param1=1.0, param2=2.0)
    assert comp.param1 == 1.0
    assert comp.param2 == 2.0

def test_my_component_config_validation():
    """Test Pydantic config validation."""
    # Test valid config
    config = MyComponentConfig(param1=1.0, param2=50.0)
    assert config.param1 == 1.0
    assert config.param2 == 50.0

    # Test type coercion
    config = MyComponentConfig(param1="5.5", param2="75")
    assert config.param1 == 5.5
    assert config.param2 == 75.0

def test_my_component_validation_errors():
    """Test validation error messages."""
    # Test param1 <= 0 (violates gt=0)
    with pytest.raises(ValueError, match="Component 'test' configuration error"):
        MyComponent(name='test', param1=-1.0, param2=2.0)

    # Test param2 out of range
    with pytest.raises(ValueError, match="Component 'test' configuration error"):
        MyComponent(name='test', param1=1.0, param2=150.0)

    # Test extra field (caught by extra='forbid')
    with pytest.raises(ValueError, match="Component 'test' configuration error"):
        MyComponent(name='test', param1=1.0, param2=2.0, unknown_param=3.0)

def test_my_component_step():
    """Test component step execution."""
    comp = MyComponent(name='test', param1=2.0, param2=3.0)
    comp.inputs = {'input1': 5.0}

    # Create mock drivers with type-safe API
    from waterlib.core.drivers import DriverRegistry, TimeSeriesDriver
    drivers = DriverRegistry()

    # Mock precipitation and temperature
    class MockTimeSeriesDriver(TimeSeriesDriver):
        def __init__(self, value):
            self.value = value
        def get_value(self, date):
            return self.value

    drivers._drivers['precipitation'] = MockTimeSeriesDriver(10.0)
    drivers._drivers['temperature'] = MockTimeSeriesDriver(20.0)

    outputs = comp.step(datetime(2020, 1, 1), drivers)

    assert outputs['output1'] == 2.0 * 5.0 + 3.0
    assert outputs['output1'] == 13.0
```

**Step 4: Document in COMPONENTS.md**

Add a section describing the component, its parameters, inputs, outputs, and examples.

### 4.4 Component Best Practices

**Parameter Validation (Pydantic 2.0+)**
- Create a `ComponentNameConfig(BaseModel)` class with Field() constraints
- Use `model_config = {'extra': 'forbid'}` to catch typos in YAML
- Validate in `__init__` using try/except with clear error messages
- Store validated values from config object: `self.param = config.param`
- Use `Field(gt=0, le=100, description="...")` for numeric constraints
- Use `@field_validator` for custom field validation
- Use `@model_validator(mode='after')` for cross-field validation
- Wrap Pydantic errors: `f"Component '{name}' configuration error: {e}"`

**State Management**
- Initialize all state variables in `__init__`
- Document state variables in docstring
- Be explicit about units
- Deep copy mutable types (dict, list, set) to prevent reference mutation

**Input Handling**
- Use `self.inputs.get(key, default)` for optional inputs from connected components
- **Type-Safe Driver API (preferred)**:
  - `drivers.climate.precipitation.get_value(date)` - IDE autocompletion
  - `drivers.climate.temperature.get_value(date)` - Design-time error detection
  - `drivers.climate.et.get_value(date)` - No typo runtime errors
- **Legacy String API (being phased out)**:
  - `drivers.get('precipitation').get_value(date)` - Still supported for backwards compatibility
- Validate required inputs exist
- Handle missing data gracefully with appropriate defaults or warnings

**Output Consistency**
- Always return the same keys from `step()`
- Use descriptive output names
- Include units in docstrings

**Logging**
- Use `self.logger` for component-specific logging
- Log initialization parameters
- Log warnings for unusual conditions
- Don't log every timestep (too verbose)

**Why Type-Safe Driver API?**

The new `drivers.climate.attribute` pattern provides:
- **IDE Autocompletion**: See available drivers as you type
- **Design-Time Errors**: Typos caught before running simulation
- **Code Navigation**: Jump to definition with Ctrl+Click
- **Refactoring Safety**: Rename refactoring updates all usages
- **Self-Documenting**: Clear namespace organization (climate, hydraulic, etc.)

Example comparison:
```python
# ❌ Legacy: Runtime error if you typo 'precipitation'
precip = drivers.get('precipitaton').get_value(date)  # Oops!

# ✅ Type-Safe: IDE catches typo immediately
precip = drivers.climate.precipitation.get_value(date)
```

---

## 5. Driver Development

### 5.1 Driver Pattern

Drivers provide global data (climate, prices, etc.) to all components without explicit connections.

**When to use a Driver:**
- Data needed by multiple components
- Data is time-varying but not component-specific
- Want to avoid cluttering YAML with connections

**When NOT to use a Driver:**
- Component-specific data (use component parameters)
- Static data (use YAML settings)
- Data that flows between components (use connections)

### 5.2 Creating a New Driver

```python
# waterlib/core/drivers.py (add to existing file)
class MyDriver(Driver):
    """Description of what this driver provides."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Initialize data source

    def get_value(self, date: datetime) -> float:
        """Get value for specific date."""
        # Implement data retrieval logic
        return value
```

**Register in DriverRegistry:**

```python
# In create_driver_from_config()
if mode == 'my_mode':
    return MyDriver(driver_config)
```

---

### 4.5 Real-World Component Examples

The following components demonstrate Pydantic validation patterns in production:

**1. Catchment Component** (`waterlib/components/catchment.py`)

Orchestrates Snow17 and AWBM kernels with comprehensive validation:

```python
class CatchmentConfig(BaseModel):
    """Catchment configuration with Snow17 and AWBM parameters."""
    model_config = {'extra': 'forbid'}

    area_km2: float = Field(gt=0, description="Catchment area [km²]")
    elevation: float = Field(ge=0, description="Catchment elevation [m]")

    # Snow17 parameters
    scf: float = Field(gt=0, le=2, description="Snow correction factor")
    pxtemp1: float = Field(description="Temperature threshold [°C]")

    # AWBM parameters
    c1: float = Field(ge=0, le=1, description="Surface store capacity fraction")

    @field_validator('scf')
    @classmethod
    def validate_scf_reasonable(cls, v):
        if v < 0.5 or v > 1.5:
            import warnings
            warnings.warn(f"SCF={v} is outside typical range [0.5-1.5]")
        return v
```

**2. LaggedValue Component** (`waterlib/components/logic.py`)

Demonstrates mutable type handling with deep copy:

```python
class LaggedValueConfig(BaseModel):
    """Configuration for time-lagged value storage."""
    model_config = {'extra': 'forbid'}

    source: str | dict = Field(description="Source specification")
    initial_value: float = Field(default=0.0)

class LaggedValue(Component):
    def __init__(self, name: str, source, initial_value: float = 0.0, **kwargs):
        super().__init__(name, **kwargs)

        config = LaggedValueConfig(source=source, initial_value=initial_value)

        # Deep copy mutable source to prevent reference mutation
        from copy import deepcopy
        if isinstance(config.source, dict):
            self.source = deepcopy(config.source)
        else:
            self.source = config.source

        self.current_value = config.initial_value
```

**3. Demand Component** (`waterlib/components/demand.py`)

Shows cross-field validation with `@model_validator`:

```python
class DemandConfig(BaseModel):
    """Demand configuration with mode-specific validation."""
    model_config = {'extra': 'forbid'}

    mode: str = Field(pattern=r'^(constant|variable)$')
    base_demand: float = Field(ge=0, description="Base demand [m³/day]")
    peak_factor: float | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def check_mode_consistency(self):
        if self.mode == 'variable' and self.peak_factor is None:
            raise ValueError("peak_factor required when mode='variable'")
        return self
```

**4. Reservoir Component** (`waterlib/components/reservoir.py`)

Demonstrates multiple field validators and complex constraints:

```python
class ReservoirConfig(BaseModel):
    """Reservoir configuration with physical constraints."""
    model_config = {'extra': 'forbid'}

    capacity: float = Field(gt=0, description="Storage capacity [m³]")
    initial_storage: float = Field(ge=0, description="Initial storage [m³]")
    min_storage: float = Field(ge=0, default=0.0)
    max_release: float = Field(gt=0, description="Max release rate [m³/day]")

    @model_validator(mode='after')
    def check_storage_constraints(self):
        if self.initial_storage > self.capacity:
            raise ValueError(
                f"initial_storage ({self.initial_storage}) > "
                f"capacity ({self.capacity})"
            )
        if self.min_storage > self.capacity:
            raise ValueError(
                f"min_storage ({self.min_storage}) > "
                f"capacity ({self.capacity})"
            )
        return self
```

---

## 6. Testing Strategy

### 6.1 Test Pyramid

```
        /\
       /  \      E2E Tests (few)
      /____\     - Full simulations
     /      \    - YAML loading
    /________\   Integration Tests (some)
   /          \  - Multi-component
  /____________\ Unit Tests (many)
                 - Individual components
                 - Utility functions
```

### 6.2 Kernel Tests

**Test kernels in isolation:**
- Pure function behavior with known inputs/outputs
- Edge cases (zero, negative, extreme values)
- State transitions
- Mathematical correctness
- No mocking needed (pure functions)

**Example:**

```python
def test_snow17_accumulation():
    """Test snow accumulation at cold temperatures."""
    from waterlib.kernels.hydrology.snow17 import snow17_step, Snow17Params, Snow17State, Snow17Inputs

    params = Snow17Params(pxtemp1=0.0, pxtemp2=1.0, scf=1.0)
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

    # At -5°C, all precip should be snow
    assert outputs.snow_mm == 10.0
    assert outputs.rain_mm == 0.0
    # Ice should increase
    assert new_state.w_i > state.w_i
```

### 6.3 Component Tests

**What to test:**
- **Configuration Validation**: Test Pydantic config class directly
- **Parameter Validation**: Test component initialization errors
- **Type Coercion**: Ensure strings convert to correct types
- **Extra Fields**: Test that unknown parameters are rejected
- **Calculation Correctness**: Verify step() computations
- **State Updates**: Check state variables update correctly
- **Edge Cases**: Zero, negative, extreme values
- **Error Handling**: Proper error messages for invalid inputs

**Example Testing Pattern:**

```python
import pytest
from datetime import datetime
from waterlib.components.reservoir import Reservoir, ReservoirConfig

# Test 1: Configuration validation (test Pydantic class directly)
def test_reservoir_config_valid():
    """Test valid reservoir configuration."""
    config = ReservoirConfig(
        capacity=1000.0,
        initial_storage=500.0,
        min_storage=0.0,
        max_release=100.0
    )
    assert config.capacity == 1000.0
    assert config.initial_storage == 500.0

# Test 2: Type coercion (Pydantic automatic conversion)
def test_reservoir_config_type_coercion():
    """Test that strings are coerced to correct types."""
    config = ReservoirConfig(
        capacity="1000",
        initial_storage="500",
        max_release="100"
    )
    assert isinstance(config.capacity, float)
    assert config.capacity == 1000.0

# Test 3: Field validation (Field constraints)
def test_reservoir_config_negative_capacity():
    """Test that negative capacity is rejected."""
    with pytest.raises(ValueError, match="capacity"):
        ReservoirConfig(
            capacity=-1000.0,
            initial_storage=500.0,
            max_release=100.0
        )

# Test 4: Cross-field validation (model_validator)
def test_reservoir_config_initial_exceeds_capacity():
    """Test that initial_storage > capacity is rejected."""
    with pytest.raises(ValueError, match="initial_storage.*capacity"):
        ReservoirConfig(
            capacity=1000.0,
            initial_storage=1500.0,
            max_release=100.0
        )

# Test 5: Extra fields rejected (extra='forbid')
def test_reservoir_config_extra_field():
    """Test that unknown parameters are rejected."""
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        ReservoirConfig(
            capacity=1000.0,
            initial_storage=500.0,
            max_release=100.0,
            unknown_param=42.0
        )

# Test 6: Component initialization wraps Pydantic errors
def test_reservoir_initialization_error():
    """Test that component wraps Pydantic validation errors."""
    with pytest.raises(ValueError, match="Component 'test' configuration error"):
        Reservoir(
            name='test',
            capacity=-1000.0,  # Invalid
            initial_storage=500.0,
            max_release=100.0
        )

# Test 7: Component step execution
def test_reservoir_mass_balance():
    """Test that reservoir conserves mass."""
    res = Reservoir(
        name='test',
        capacity=5000.0,
        initial_storage=1000.0,
        max_release=500.0
    )

    res.inputs = {'inflow': 100.0}

    # Mock drivers for testing
    from waterlib.core.drivers import DriverRegistry
    drivers = DriverRegistry()

    initial = res.outputs.get('storage', 1000.0)
    outputs = res.step(datetime(2020, 1, 1), drivers)
    final = outputs['storage']

    # Storage should increase by inflow (ignoring evap for this test)
    assert final > initial
    assert outputs['outflow'] >= 0

# Test 8: Edge case - zero inflow
def test_reservoir_zero_inflow():
    """Test reservoir with zero inflow."""
    res = Reservoir(
        name='test',
        capacity=5000.0,
        initial_storage=1000.0,
        max_release=500.0
    )

    res.inputs = {'inflow': 0.0}

    from waterlib.core.drivers import DriverRegistry
    drivers = DriverRegistry()

    outputs = res.step(datetime(2020, 1, 1), drivers)

    # Should handle zero inflow without errors
    assert outputs['storage'] >= 0
    assert outputs['outflow'] >= 0
```

**Testing Type-Safe Driver API:**

```python
def test_component_uses_typesafe_drivers():
    """Test that component uses type-safe driver API."""
    from waterlib.components.catchment import Catchment
    from waterlib.core.drivers import DriverRegistry, TimeSeriesDriver
    import pandas as pd

    # Create catchment
    catchment = Catchment(
        name='test',
        area_km2=100.0,
        elevation=1000.0,
        # ... other params
    )

    # Mock drivers with type-safe API
    drivers = DriverRegistry()

    # Create mock time series drivers
    dates = pd.date_range('2020-01-01', periods=10)

    class MockDriver(TimeSeriesDriver):
        def __init__(self, value):
            self.value = value
        def get_value(self, date):
            return self.value

    # Set up climate namespace
    drivers._drivers['precipitation'] = MockDriver(10.0)
    drivers._drivers['temperature'] = MockDriver(5.0)
    drivers._drivers['et'] = MockDriver(2.0)

    # Test that type-safe API works
    precip = drivers.climate.precipitation.get_value(dates[0])
    assert precip == 10.0

    # Test component step with type-safe drivers
    outputs = catchment.step(dates[0], drivers)
    assert 'runoff' in outputs
    assert outputs['runoff'] >= 0
```

### 6.4 Property-Based Tests

Use Hypothesis for testing properties that should hold for all inputs:

```python
from hypothesis import given, strategies as st
from datetime import datetime

@given(
    inflow=st.floats(min_value=0, max_value=1e6),
    capacity=st.floats(min_value=1e6, max_value=1e8),
    initial_pct=st.floats(min_value=0, max_value=1.0)
)
def test_reservoir_never_negative(inflow, capacity, initial_pct):
    """Reservoir storage should never go negative."""
    initial_storage = capacity * initial_pct

    res = Reservoir(
        name='test',
        capacity=capacity,
        initial_storage=initial_storage,
        max_release=1e5
    )

    res.inputs = {'inflow': inflow}

    # Mock drivers for testing
    from waterlib.core.drivers import DriverRegistry
    drivers = DriverRegistry()
    outputs = res.step(datetime(2020, 1, 1), drivers)

    # Storage should never be negative
    assert outputs['storage'] >= 0
    # Storage should never exceed capacity (with spillway)
    assert outputs['storage'] <= capacity * 1.01  # Allow small numerical error

@given(
    demand=st.floats(min_value=0, max_value=1000),
    base_demand=st.floats(min_value=0.1, max_value=500)
)
def test_demand_always_positive(demand, base_demand):
    """Demand should always be non-negative."""
    from waterlib.components.demand import Demand

    d = Demand(
        name='test',
        mode='constant',
        base_demand=base_demand
    )

    from waterlib.core.drivers import DriverRegistry
    drivers = DriverRegistry()
    outputs = d.step(datetime(2020, 1, 1), drivers)

    assert outputs['demand'] >= 0
```

### 6.5 Integration Tests

Test multiple components working together:

```python
def test_catchment_reservoir_system():
    """Test catchment feeding reservoir."""
    # Create components
    catchment = Catchment(name='catch', area_km2=100, ...)
    reservoir = Reservoir(name='res', ...)

    # Connect them
    reservoir.inputs = {'inflow': 0}  # Will be updated

    # Create drivers with climate data
    from waterlib.core.drivers import DriverRegistry
    drivers = DriverRegistry()
    # Add climate drivers here (precipitation, temperature, ET)

    # Run for multiple timesteps
    for date in pd.date_range('2020-01-01', '2020-01-10'):
        # Step catchment
        catch_out = catchment.step(date, drivers)

        # Feed to reservoir
        reservoir.inputs['inflow'] = catch_out['runoff_m3d']
        res_out = reservoir.step(date, drivers)

        # Verify outputs are reasonable
        assert res_out['storage'] >= 0
        assert res_out['storage'] <= reservoir.max_storage_m3
```

### 5.5 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_reservoir.py

# Run with coverage
pytest --cov=waterlib --cov-report=html

# Run property-based tests with more examples
pytest --hypothesis-show-statistics
```

---

## 6. Code Style and Conventions


### 6.1 Python Style

**Follow PEP 8** with these specifics:
- Line length: 100 characters (not 79)
- Indentation: 4 spaces
- Imports: stdlib, third-party, local (separated by blank lines)
- Docstrings: Google style

**Type Hints**
- Use type hints for all function signatures
- Use `Optional[T]` for nullable types
- Use `Dict[str, Any]` for flexible dictionaries
- Use `Union[A, B]` sparingly (prefer single types)

**Example:**

```python
from typing import Dict, List, Optional, Any
from datetime import datetime

def process_data(
    data: Dict[str, float],
    date: datetime,
    threshold: Optional[float] = None
) -> List[float]:
    """Process data for a specific date.

    Args:
        data: Dictionary of values
        date: Processing date
        threshold: Optional threshold for filtering

    Returns:
        List of processed values
    """
    pass
```

### 6.2 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `Reservoir`, `WaterComponent` |
| Functions | snake_case | `run_simulation`, `get_value` |
| Variables | snake_case | `storage_m3`, `max_capacity` |
| Constants | UPPER_SNAKE | `MAX_ITERATIONS`, `DEFAULT_SEED` |
| Private | _leading_underscore | `_validate_params` |

**Units in Variable Names**
- Include units for physical quantities: `storage_m3`, `flow_m3d`, `area_km2`
- Use standard abbreviations: `m3` (cubic meters), `m3d` (cubic meters per day)
- Be consistent across the codebase

### 6.3 Docstring Format

Use Google-style docstrings:

```python
def calculate_flow(
    storage: float,
    capacity: float,
    coefficient: float = 1.0
) -> float:
    """Calculate outflow from storage.

    Uses the equation: Q = C * sqrt(S / S_max)

    Args:
        storage: Current storage [m³]
        capacity: Maximum storage capacity [m³]
        coefficient: Flow coefficient (default=1.0)

    Returns:
        Outflow rate [m³/day]

    Raises:
        ValueError: If storage > capacity

    Example:
        >>> flow = calculate_flow(1000, 5000, 1.5)
        >>> print(f"Flow: {flow:.2f} m³/day")
    """
    if storage > capacity:
        raise ValueError(f"Storage {storage} exceeds capacity {capacity}")

    return coefficient * (storage / capacity) ** 0.5
```

### 6.4 Error Handling

**Use Custom Exceptions**

```python
# waterlib/core/exceptions.py
class WaterlibError(Exception):
    """Base exception for waterlib."""
    pass

class ConfigurationError(WaterlibError):
    """Raised when configuration is invalid."""
    pass

class SimulationError(WaterlibError):
    """Raised when simulation fails."""
    pass
```

**Provide Context**

```python
# Bad
raise ValueError("Invalid value")

# Good
raise ConfigurationError(
    f"Component '{name}' has invalid parameter 'capacity': "
    f"must be > 0, got {capacity}"
)
```

**Fail Fast**
- Validate in `__init__`, not `step()`
- Don't catch exceptions unless you can handle them
- Let exceptions propagate with context

---

## 7. Common Development Tasks

### 7.1 Creating a Scaffolded Project for Testing

When developing or testing new features, use the project scaffolding functionality to quickly set up a complete test environment:

```python
import waterlib
import tempfile
import os

# Create a temporary test project
temp_dir = tempfile.mkdtemp()
project_path = waterlib.create_project(
    "test_feature",
    parent_dir=temp_dir
)

# The project includes:
# - models/baseline.yaml (complete working model)
# - data/wgen_params.csv (climate parameters)
# - data/climate_timeseries.csv (example data)
# - run_model.py (sample script)
# - outputs/ (empty directory for results)

# Test your changes
model = waterlib.load_model(os.path.join(project_path, 'models', 'baseline.yaml'))
results = waterlib.run_simulation(model, output_dir=os.path.join(project_path, 'outputs'))

# Verify outputs
assert os.path.exists(os.path.join(project_path, 'outputs', 'simulation.log'))
assert os.path.exists(os.path.join(project_path, 'outputs', 'results.csv'))
```

**Scaffolded Project Structure:**

```
project_name/
├── README.md                    # Auto-generated project documentation
├── models/
│   └── baseline.yaml            # Complete catchment-reservoir-demand model
├── data/
│   ├── wgen_params.csv          # Monthly weather parameters
│   ├── climate_timeseries.csv   # Sample daily climate data
│   └── README.md                # Data documentation
├── outputs/                     # Results directory (simulation.log, CSV, plots)
├── config/                      # Additional configurations
└── run_model.py                 # Runnable example script
```

The baseline model includes:
- Stochastic climate generation (WGEN)
- Catchment with Snow17 and AWBM kernels
- Reservoir with spillway
- Municipal demand component

This provides a complete, working system for testing changes to the loader, simulation engine, components, or kernels.

### 7.2 Adding a New Component Type

1. Create `waterlib/components/my_component.py`
2. Implement `Component` interface
3. Add to `COMPONENT_REGISTRY` in `components/__init__.py`
4. Write unit tests in `tests/test_my_component.py`
5. Add integration test in `tests/integration/`
6. Document in `COMPONENTS.md`
7. Create example YAML in `examples/`

### 7.3 Adding a New Climate Driver

1. Add driver class to `waterlib/core/drivers.py`
2. Update `create_driver_from_config()` to handle new mode
3. Update `validate_driver_config()` for new mode
4. Write unit tests
5. Update `docs/YAML_SCHEMA.md`
6. Create example configuration

### 7.3 Adding a New Output Format

1. Add method to `Results` class in `core/results.py`
2. Write tests for new format
3. Update API documentation
4. Add example usage

### 7.4 Fixing a Bug

1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Check for similar bugs elsewhere
5. Update documentation if behavior changed

### 7.5 Improving Performance

1. Profile to identify bottleneck: `python -m cProfile script.py`
2. Write performance test to measure improvement
3. Optimize (vectorize, cache, etc.)
4. Verify correctness with existing tests
5. Document performance characteristics

---

## 8. Debugging and Troubleshooting

### 8.1 Logging

**Simulation File Logging**

All simulations automatically create a `simulation.log` file in the output directory that captures detailed execution information:

```python
import waterlib

model = waterlib.load_model('model.yaml')
results = waterlib.run_simulation(
    model,
    output_dir='./results'
)

# simulation.log is automatically created at ./results/simulation.log
# The log is overwritten on each simulation run (not appended)
```

The log file contains:
- Model loading details (components instantiated, graph structure)
- Simulation progress (timestep count, date range)
- Component execution information
- Results saving confirmations
- Network diagram generation status

**Enable Debug Logging**

For additional debugging in the console, enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

import waterlib
model = waterlib.load_model('model.yaml')
```

**Component-Specific Logging**

```python
logging.getLogger('waterlib.Reservoir').setLevel(logging.DEBUG)
```

### 8.2 Common Issues

**Circular Dependencies**

```
CircularDependencyError: Model contains circular dependencies
```

**Solution:** Add a `LaggedValue` component to break the cycle

**Missing Inputs**

```
KeyError: 'inflow'
```

**Solution:** Check that connections are defined correctly in YAML

**Date Range Mismatch**

```
KeyError: Date 2020-01-15 not found in timeseries data
```

**Solution:** Ensure timeseries CSV covers full simulation period

**Type Errors**

```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'float'
```

**Solution:** Check for None values, use `.get(key, default)`

### 8.3 Debugging Techniques

**Print Intermediate Values**

```python
def step(self, date, drivers):
    inflow = self.inputs.get('inflow', 0)
    print(f"[{date}] {self.name}: inflow={inflow}")  # Debug
    # ... rest of calculation
```

**Use Debugger**

```python
import pdb; pdb.set_trace()  # Breakpoint
```

**Visualize Data Flow**

```python
model.visualize(show=True)  # See component connections
```

**Check Execution Order**

```python
print(model.execution_order)  # See component execution sequence
```

---

## 9. Git Workflow

### 9.1 Branch Strategy

- `main` - Stable releases
- `develop` - Integration branch
- `feature/my-feature` - Feature branches
- `bugfix/issue-123` - Bug fix branches

### 9.2 Commit Messages

Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

**Examples:**

```
feat(components): add WaterTreatment component

Implements a water treatment plant component with:
- Capacity constraints
- Treatment efficiency
- Chemical dosing

Closes #45

---

fix(reservoir): correct evaporation calculation

Evaporation was using wrong surface area units.
Changed from m² to km² to match other components.

Fixes #67

---

docs(api): update component reference

Added missing parameters for Pump component
```

### 9.3 Pull Request Process

1. Create feature branch from `develop`
2. Make changes with tests
3. Run full test suite: `pytest`
4. Update documentation
5. Push and create PR
6. Address review comments
7. Squash and merge to `develop`

---

## 10. Release Process

### 10.1 Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### 10.2 Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Version bumped in `__init__.py`
- [ ] Git tag created: `git tag v0.2.0`
- [ ] PyPI package built: `python -m build`
- [ ] Package uploaded: `twine upload dist/*`
- [ ] GitHub release created

---

## 11. Documentation Standards

### 11.1 Documentation Types

| Type | Location | Audience | Purpose |
|------|----------|----------|---------|
| User Guide | `GETTING_STARTED.md` | New users | Tutorial |
| Component Ref | `COMPONENTS.md` | Users | Component details |
| API Ref | `docs/API_REFERENCE.md` | Developers | Python API |
| Dev Guide | `DEVELOPER_GUIDE.md` | Contributors | Architecture |
| YAML Schema | `docs/YAML_SCHEMA.md` | Users | Configuration |

### 11.2 Documentation Structure

**User-Facing Documentation:**
- `README.md` - Project overview, quick start, features
- `GETTING_STARTED.md` - Step-by-step tutorial for new users
- `COMPONENTS.md` - Complete component reference
- `docs/YAML_SCHEMA.md` - YAML configuration reference

**Developer Documentation:**
- `DEVELOPER_GUIDE.md` - This document (architecture, patterns, workflows)
- `docs/ARCHITECTURE_DIAGRAM.md` - Visual architecture with Mermaid diagrams
- `docs/API_REFERENCE.md` - Python API documentation
- `PROJECT_STRUCTURE.md` - Directory structure and organization

**Kernel Documentation:**
- `docs/KERNEL_MIGRATION_GUIDE.md` - Migrating from old to new architecture
- `docs/KERNEL_USAGE_EXAMPLES.md` - Practical kernel usage examples
- Kernel docstrings - In-code documentation for each kernel

**Examples:**
- `examples/` - Working YAML models and Python scripts
- `examples/live_view.ipynb` - Live model watcher notebook

### 11.3 Documentation Updates

**When adding a component:**
- Update `COMPONENTS.md` with full specification
- Add example to `examples/`
- Update `docs/API_REFERENCE.md`
- Update component registry in code

**When adding a kernel:**
- Add kernel module with complete docstrings
- Update kernel `__init__.py` exports
- Add examples to `docs/KERNEL_USAGE_EXAMPLES.md`
- Add tests to `tests/unit/kernels/`

**When changing API:**
- Update docstrings
- Update `docs/API_REFERENCE.md`
- Add migration guide if breaking
- Update examples to match new API

**When fixing a bug:**
- Update relevant documentation if behavior changed
- Add note to CHANGELOG.md
- Update tests to prevent regression

---

## 12. Performance Guidelines

### 12.1 Optimization Priorities

1. **Correctness first** - Don't optimize until it works
2. **Profile before optimizing** - Measure, don't guess
3. **Optimize hot paths** - Focus on code called many times
4. **Vectorize when possible** - Use NumPy for array operations

### 12.2 Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Component step() | < 1ms | Per timestep per component |
| Full simulation (1 year) | < 1s | 10 components, daily timestep |
| Model loading | < 100ms | YAML parsing and validation |
| Visualization | < 2s | Network diagram generation |

### 12.3 Profiling

```python
import cProfile
import pstats

# Profile simulation
cProfile.run('run_simulation(model)', 'profile_stats')

# Analyze results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

---

## 13. Security Considerations

### 13.1 Input Validation

- Validate all YAML inputs
- Check file paths for directory traversal
- Sanitize user-provided strings
- Limit file sizes for CSV uploads

### 13.2 Safe Defaults

- Use safe defaults for optional parameters
- Fail closed (deny by default)
- Validate ranges for physical quantities

### 13.3 Dependency Management

- Pin dependency versions in `pyproject.toml`
- Regularly update dependencies
- Review security advisories

---

## 14. Continuous Integration

### 14.1 CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest --cov=waterlib --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### 14.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

---

## 15. Resources

### Internal Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - User tutorial
- [COMPONENTS.md](COMPONENTS.md) - Component reference
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation
- [docs/ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md) - Architecture overview
- [docs/KERNEL_PURITY_ENFORCEMENT.md](docs/KERNEL_PURITY_ENFORCEMENT.md) - Kernel constraints

### External Resources

**Python**
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [pytest Documentation](https://docs.pytest.org/)

**Hydrology**
- [AWBM Documentation](http://www.toolkit.net.au/awbm)
- [Snow17 Model](https://www.nws.noaa.gov/oh/hrl/nwsrfs/users_manual/part2/_pdf/22snow17.pdf)

---

**Maintained by:** Core Development Team
