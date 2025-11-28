# Kernel Purity Architecture Enforcement

## Overview

This document explains the architectural constraint that prevents kernels from importing components, and how it's enforced in the waterlib codebase.

## The Architectural Rule

**Kernels must remain pure functions with no dependencies on the component graph structure.**

Specifically:
- ✅ Components MAY import kernels
- ❌ Kernels MUST NOT import components
- ✅ Kernels MAY import other kernels
- ✅ Kernels MAY import standard library and scientific packages (numpy, etc.)

## Why This Matters

### Scalability & Performance
If waterlib needs to scale to handle large watersheds or long simulations, the computational kernels may need to be rewritten in compiled languages like Rust or C++. By keeping kernels pure and isolated from the graph structure, this future migration becomes straightforward.

### Mathematical Portability
Pure kernel functions can be:
- Extracted and used in other projects
- Tested independently with mathematical rigor
- Parallelized or GPU-accelerated without graph concerns
- Published as standalone algorithms

### Clear Separation of Concerns
- **Kernels**: Pure mathematical/physical algorithms
- **Components**: Graph orchestration and state management
- **Model**: System composition and connections

## Enforcement Mechanisms

### 1. Flake8 Configuration (`.flake8`)

The flake8 configuration includes a custom checker that scans all files in `waterlib/kernels/` for forbidden imports:

```ini
[flake8]
# ... other config ...

[flake8:local-plugins]
extension =
    I9 = waterlib_lint:check_kernel_imports
```

**Error Code: I900**
> "Kernel modules must not import from waterlib.components. Kernels must remain pure functions for scalability."

### 2. Custom Flake8 Plugin (`waterlib_lint.py`)

A custom flake8 plugin uses AST parsing to detect import statements:
- Checks `from waterlib.components import ...`
- Checks `import waterlib.components...`
- Only applies to files in `waterlib/kernels/`

### 3. Pre-commit Hook (`scripts/check_kernel_imports.py`)

A dedicated pre-commit hook provides fast, local enforcement:
- Runs before code is committed
- Uses regex and line-based analysis
- Provides clear error messages with line numbers
- Blocks commits that violate the constraint

### 4. Pre-commit Configuration (`.pre-commit-config.yaml`)

Integrates with the pre-commit framework:
```yaml
- repo: local
  hooks:
    - id: check-kernel-imports
      name: Check kernel import restrictions
      entry: python scripts/check_kernel_imports.py
      language: system
      files: ^waterlib/kernels/.*\.py$
```

## Setup Instructions

### Initial Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   # or
   pip install -e .[dev]
   ```

2. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### Running Checks Manually

**Check all kernel files with flake8:**
```bash
flake8 waterlib/kernels/
```

**Run pre-commit on all files:**
```bash
pre-commit run --all-files
```

**Run only the kernel import check:**
```bash
pre-commit run check-kernel-imports --all-files
```

**Test the script directly:**
```bash
python scripts/check_kernel_imports.py waterlib/kernels/**/*.py
```

### CI/CD Integration

Add to your CI pipeline (GitHub Actions, GitLab CI, etc.):

```yaml
- name: Lint kernel imports
  run: |
    pip install flake8
    flake8 waterlib/kernels/
    python scripts/check_kernel_imports.py waterlib/kernels/**/*.py
```

## Examples

### ❌ Violations (Will Fail)

```python
# waterlib/kernels/hydrology/example.py

# WRONG: Importing from components
from waterlib.components.reservoir import Reservoir

# WRONG: Importing component module
import waterlib.components.catchment

# WRONG: Indirect import via core.base (which has Component)
from waterlib.core.base import Component
```

### ✅ Correct Patterns

```python
# waterlib/kernels/hydrology/example.py

# CORRECT: Standard library
import numpy as np
from dataclasses import dataclass
from typing import Tuple

# CORRECT: Other kernels
from waterlib.kernels.climate.et import calculate_pet

# CORRECT: Core exceptions (not graph-related)
from waterlib.core.exceptions import ValidationError
```

```python
# waterlib/components/catchment.py

# CORRECT: Components import kernels
from waterlib.kernels.hydrology.awbm import awbm_step, AWBMParams
from waterlib.kernels.climate.et import calculate_pet

# This is the correct dependency direction
```

## Error Messages

When a violation is detected, you'll see:

```
❌ Kernel Import Restriction Violations Found:

waterlib/kernels/hydrology/example.py:5: Kernel modules must not import from waterlib.components. Kernels must remain pure functions for scalability.
  Found: from waterlib.components.reservoir import Reservoir

Kernels must remain pure functions without dependencies on components.
This architectural constraint ensures kernels can be rewritten in
Rust/C++ for performance scaling without breaking the system.
```

## Troubleshooting

### Pre-commit hook not running
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check installation
pre-commit run --all-files
```

### False positives in comments
The checker ignores lines starting with `#`, but multi-line strings mentioning `waterlib.components` might trigger warnings. Use `# noqa: I900` to suppress:

```python
# This is fine - in a comment explaining that kernels can't import components
"""
Documentation example showing: from waterlib.components import X  # noqa: I900
"""
```

### Need to temporarily disable
Not recommended, but if absolutely necessary during development:
```bash
git commit --no-verify
```

**Warning:** This bypasses all pre-commit hooks and should only be used in exceptional circumstances.

## Maintenance

### Updating the Rules

1. **Add exceptions** (if needed) in `scripts/check_kernel_imports.py`
2. **Modify AST checking** in `waterlib_lint.py` for edge cases
3. **Update error messages** to improve clarity

### Testing the Enforcement

Create a test file with a violation:
```bash
echo "from waterlib.components.reservoir import Reservoir" > waterlib/kernels/test_violation.py
python scripts/check_kernel_imports.py waterlib/kernels/test_violation.py
rm waterlib/kernels/test_violation.py
```

Expected output: Error message with violation details.

## Future Enhancements

Potential improvements:
1. **Type checking**: Use mypy to enforce import restrictions at type level
2. **Import graph visualization**: Tool to visualize allowed vs forbidden imports
3. **Performance testing**: Benchmark kernel isolation benefits
4. **Rust/C++ bridge**: Prototype showing how isolated kernels can be swapped out

## Questions?

For questions about this architectural constraint:
- See `DEVELOPER_GUIDE.md` Section 3.4.1
- Review existing kernels in `waterlib/kernels/` for examples
- Check `docs/KERNEL_USAGE_EXAMPLES.md` for usage patterns
