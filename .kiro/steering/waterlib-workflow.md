---
inclusion: always
---

# Waterlib Development Workflow

This file teaches Kiro how to work with the waterlib project and enforces development standards.

## Context Files to Load

When starting any waterlib feature development, load these files into context:

1. **DEVELOPER_GUIDE.md** - Architecture patterns, Kernel/Component separation, Pydantic validation
2. **QA_INFRASTRUCTURE.md** - Testing requirements, pre-commit hooks, documentation standards
3. **COMPONENTS.md** - Existing components for reference
4. **README.md** - High-level project overview

## Architectural Constraints

### Kernel Purity Rule (CRITICAL)
- Kernels (in `waterlib/kernels/`) MUST NOT import from `waterlib/components/`
- This is enforced by `waterlib_lint.py`
- Always run linter before tests: `python waterlib_lint.py && pytest`
- Violation blocks commits via pre-commit hook

### Pydantic Validation (REQUIRED)
- All new components MUST use Pydantic for parameter validation
- Create a `ComponentNameConfig(BaseModel)` class
- Use `model_config = {'extra': 'forbid'}` to catch typos in YAML
- Use `Field()` constraints for validation (gt, ge, le, lt, pattern)
- Wrap Pydantic errors: `f"Component '{name}' configuration error: {e}"`

### Backward Compatibility Policy (ZERO TOLERANCE)
- **NO backward compatibility during rapid development phase**
- **Breaking changes are accepted and encouraged**
- Remove old code immediately - no deprecation warnings
- Fail fast with clear error messages explaining new format
- Update all templates in `scaffold.py` in the same commit
- Do not create adapter layers or fallback logic

## Documentation Synchronization

When modifying code, update these files:

### If adding/modifying a Component:
- [ ] Update `COMPONENTS.md` with parameter table (name, type, units, description)
- [ ] Update `docs/API_REFERENCE.md` if public API changed
- [ ] Update `CHANGELOG.md` under "## Unreleased" section
- [ ] Add example to `examples/` if new component
- [ ] Update `scaffold.py` templates if affects project scaffolding

### If adding/modifying a Kernel:
- [ ] Update `DEVELOPER_GUIDE.md` if new kernel pattern introduced
- [ ] Update `docs/API_REFERENCE.md` if public kernel function
- [ ] Update `CHANGELOG.md` under "## Unreleased" section
- [ ] Ensure kernel has no imports from `waterlib.components`

### If modifying core framework:
- [ ] Update `docs/API_REFERENCE.md` with new signatures
- [ ] Update `DEVELOPER_GUIDE.md` if architecture changed
- [ ] Update `README.md` if user-facing behavior changed
- [ ] Update `CHANGELOG.md` under "## Unreleased" section
- [ ] Update `scaffold.py` if affects project creation

## Task Execution Pattern

For every task, follow this sequence:

1. **Write code** - Implement the feature/fix
2. **Run linter** - `python waterlib_lint.py` (architectural validation)
3. **If linter fails** - Fix architectural issues and return to step 1
4. **Run tests** - `pytest` (functional validation)
5. **If tests fail** - Fix bugs and return to step 4
6. **Check docs** - `python scripts/check_doc_sync.py` (documentation validation)
7. **Update docs** - Address any missing documentation
8. **Mark complete** - Task is done when all checks pass

## Requirements Format

Use EARS (Easy Approach to Requirements Syntax):

- **Event-driven**: WHEN <trigger>, THE <system> SHALL <response>
- **State-driven**: WHILE <condition>, THE <system> SHALL <response>
- **Unwanted event**: IF <condition>, THEN THE <system> SHALL <response>
- **Ubiquitous**: THE <system> SHALL <response>

**Example:**
```
WHEN a user adds a new component, THE system SHALL validate parameters using Pydantic
```

## Testing Strategy

### Unit Tests
- Write unit tests for all new functions/classes
- Test Pydantic validation directly (test the Config class)
- Use descriptive test names: `test_component_rejects_negative_capacity()`
- Mock drivers using `DriverRegistry` for component tests

### Property-Based Tests
- Use Hypothesis for property-based tests where appropriate
- Test invariants that should hold for all inputs
- Example: `@given(st.floats(min_value=0))` for testing with random positive floats

### Test Organization
- Unit tests: `tests/unit/test_<module>.py`
- Integration tests: `tests/integration/test_<feature>.py`
- Kernel tests: `tests/kernels/test_<kernel>.py`
- Manual debug scripts: `scripts/debug/` (not tracked in git)

## Project Organization

### Where to Put Files

**Code:**
- Components: `waterlib/components/`
- Kernels: `waterlib/kernels/<domain>/`
- Core framework: `waterlib/core/`
- Utilities: `waterlib/utils/`

**Tests:**
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Kernel tests: `tests/kernels/`
- Manual test scripts: `tests/manual/` (gitignored)

**Scripts:**
- Production scripts: `scripts/` (tracked)
- Debug scripts: `scripts/debug/` (gitignored)
- Setup scripts: `scripts/setup_*.py`

**Documentation:**
- User docs: `README.md`, `GETTING_STARTED.md`
- API reference: `docs/API_REFERENCE.md`
- Component reference: `COMPONENTS.md`
- Developer guide: `DEVELOPER_GUIDE.md`
- QA infrastructure: `QA_INFRASTRUCTURE.md`

**Temporary Files:**
- Never commit temp files to root directory
- Use `temp_*.txt`, `*.tmp` for temporary outputs
- These are gitignored and cleaned by `scripts/cleanup_temp_files.py`

## Common Patterns

### Creating a New Component

```python
from waterlib.core.base import Component
from pydantic import BaseModel, Field

class MyComponentConfig(BaseModel):
    """Validated configuration."""
    model_config = {'extra': 'forbid'}

    capacity: float = Field(gt=0, description="Capacity [m³]")
    coefficient: float = Field(ge=0, le=1, description="Coefficient [0-1]")

class MyComponent(Component):
    def __init__(self, name: str, capacity: float, coefficient: float, **kwargs):
        super().__init__(name, **kwargs)

        # Validate with Pydantic
        try:
            config = MyComponentConfig(capacity=capacity, coefficient=coefficient)
        except Exception as e:
            raise ValueError(f"Component '{name}' configuration error: {e}") from e

        self.capacity = config.capacity
        self.coefficient = config.coefficient
```

### Creating a New Kernel

```python
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MyKernelParams:
    """Fixed parameters."""
    coefficient: float = 1.0

@dataclass
class MyKernelState:
    """State variables."""
    storage: float = 0.0

@dataclass
class MyKernelInputs:
    """Inputs for one timestep."""
    inflow: float

@dataclass
class MyKernelOutputs:
    """Outputs from one timestep."""
    outflow: float

def my_kernel_step(
    inputs: MyKernelInputs,
    params: MyKernelParams,
    state: MyKernelState
) -> Tuple[MyKernelState, MyKernelOutputs]:
    """Execute one timestep (pure function)."""
    # Calculations here
    new_state = MyKernelState(storage=state.storage + inputs.inflow)
    outputs = MyKernelOutputs(outflow=inputs.inflow * params.coefficient)
    return new_state, outputs
```

## Error Messages

When raising errors, provide context:

**Bad:**
```python
raise ValueError("Invalid value")
```

**Good:**
```python
raise ValueError(
    f"Component '{self.name}' has invalid capacity: "
    f"must be > 0, got {capacity}"
)
```

## Commit Messages

Follow conventional commits:

```
feat(components): add Aquifer component with confined/unconfined modes
fix(reservoir): correct evaporation calculation units
docs(api): update Catchment parameter descriptions
test(kernels): add property tests for AWBM kernel
refactor(core): simplify driver registry initialization
```

## Pre-commit Checklist

Before committing, ensure:
- [ ] `python waterlib_lint.py` passes (architectural validation)
- [ ] `pytest` passes (functional validation)
- [ ] `python scripts/check_doc_sync.py` passes (documentation validation)
- [ ] All modified files are in correct directories
- [ ] No temp files in root directory
- [ ] CHANGELOG.md updated if user-facing change

## When in Doubt

1. Check DEVELOPER_GUIDE.md for patterns
2. Look at existing components for examples
3. Run the linter early and often
4. Ask for clarification rather than guessing
5. Fail fast with clear error messages
