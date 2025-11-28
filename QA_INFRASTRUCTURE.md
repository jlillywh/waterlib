# Quality Assurance Infrastructure - V1.2 Lock-down

This document describes the QA infrastructure implemented for waterlib v1.2 to ensure documentation stays synchronized with code and architectural constraints remain enforced.

## Files Created/Updated

### 1. Pull Request Template
**Location:** `.github/pull_request_template.md`

Forces every PR to complete a "Definition of Done" checklist covering:
- **Architecture & Quality**: Kernel purity, Pydantic validation, type hints
- **Testing**: Unit tests and local test runs
- **Documentation**: Docstrings, API reference, component reference, developer guide
- **Examples & Scaffolding**: Verify examples work, add new examples, update scaffold

### 2. Issue Templates
**Location:** `.github/ISSUE_TEMPLATE/`

Two templates to standardize issue creation:
- **feature_request.yml**: New features with implementation plan checklist
- **bug_report.yml**: Bug reports with reproduction steps and impact assessment

### 3. Architecture Enforcement Script
**Location:** `scripts/check_kernel_imports.py`

AST-based Python script that:
- Scans all files in `waterlib/kernels/`
- Fails if any kernel imports from `waterlib/components/`
- Returns exit code 1 on violations (blocks CI/CD)
- Provides clear error messages with line numbers

### 4. Pre-commit Configuration
**Location:** `.pre-commit-config.yaml`

Git hook configuration that:
- Runs on every commit
- Enforces trailing whitespace, EOF, YAML checks
- Automatically runs kernel purity check
- Blocks commits that violate architectural constraints

## How It Works

### For Contributors

1. **Make changes** to code/docs
2. **Run tests**: `pytest`
3. **Try to commit**: `git commit -m "..."`
4. **Pre-commit runs automatically**:
   - ✅ Passes: Commit succeeds
   - ❌ Fails: Fix violations, try again

### For PR Reviews

When opening a PR, the template appears with the full "Definition of Done" checklist. Reviewers can quickly verify:
- Architecture constraints maintained
- Docs updated
- Examples still work
- Tests added

### Setup

```bash
# Install pre-commit hooks (one-time)
pip install pre-commit
pre-commit install

# Test manually
python scripts/check_kernel_imports.py

# Run all pre-commit checks
pre-commit run --all-files
```

## What This Prevents

### Documentation Drift
- ❌ Adding a component without updating COMPONENTS.md
- ❌ Changing API without updating API_REFERENCE.md
- ❌ Breaking examples without noticing

### Architecture Violations
- ❌ Kernels importing from components
- ❌ Missing Pydantic validation in new components
- ❌ Missing type hints

### Scaffolding Issues
- ❌ Adding files without updating `create_project()`
- ❌ New features not available to users via scaffold

## Testing the Infrastructure

```bash
# Test kernel purity check passes
python scripts/check_kernel_imports.py
# Expected: ✅ Kernel purity check passed.

# Test pre-commit hooks
pre-commit run --all-files
# Expected: All hooks pass

# Create a violation (test)
echo "from waterlib.components.reservoir import Reservoir" > waterlib/kernels/test.py
python scripts/check_kernel_imports.py
# Expected: ❌ ARCHITECTURE VIOLATION
rm waterlib/kernels/test.py
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Architecture Checks
  run: |
    python scripts/check_kernel_imports.py

- name: Pre-commit Checks
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

## Enforcement Philosophy

This infrastructure embodies the principle: **"Make the right thing easy, the wrong thing hard."**

- Want to add a feature? The checklist reminds you to document it.
- Want to violate architecture? Pre-commit blocks your commit.
- Want to merge? PR template ensures nothing was forgotten.

## Version

- **Created:** 2025-11-27
- **For:** waterlib v1.2
- **Status:** Active
