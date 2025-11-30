# Design Document: Waterlib Development Workflow Enforcement

## Overview

This design implements enforcement mechanisms to ensure all waterlib files stay synchronized when making changes. The solution integrates with Kiro's existing spec workflow and adds three key enforcement layers:

1. **Kiro Steering Rules** - Teach Kiro about waterlib's architecture and documentation requirements
2. **Pre-commit Validation** - Block commits that violate architectural rules or skip documentation
3. **Documentation Sync Checklist** - Automated reminders for which files need updates

**Core Problem Being Solved:**
When adding/modifying a component, it's easy to forget to update COMPONENTS.md, API_REFERENCE.md, or CHANGELOG.md. This design ensures Kiro automatically reminds you and validates completeness before allowing the feature to be marked "done".

## Architecture

### Three-Layer Enforcement

```
┌─────────────────────────────────────────────────────────┐
│                    Kiro Spec Workflow                    │
│         (Built-in: Requirements → Design → Tasks)        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐            ┌──────▼──────┐
   │  Layer 1 │            │   Layer 2   │
   │  Kiro    │            │ Pre-commit  │
   │ Steering │            │   Hooks     │
   └────┬─────┘            └──────┬──────┘
        │                         │
        │    ┌────────────────────┘
        │    │
   ┌────▼────▼─────┐
   │    Layer 3    │
   │ Documentation │
   │ Sync Checker  │
   └───────────────┘
```

### Layer Responsibilities

**Layer 1: Kiro Steering Rules** (`.kiro/steering/waterlib-workflow.md`)
- Loads DEVELOPER_GUIDE.md and QA_INFRASTRUCTURE.md into context
- Teaches Kiro about Kernel/Component separation
- Teaches Kiro about Pydantic validation patterns
- Provides documentation update checklist template
- Enforces EARS requirements format

**Layer 2: Pre-commit Hooks** (`.pre-commit-config.yaml` + `scripts/`)
- Runs `waterlib_lint.py` before allowing commit
- Blocks commits with architectural violations
- Fast feedback loop (catches errors before Kiro runs tests)

**Layer 3: Documentation Sync Checker** (`scripts/check_doc_sync.py`)
- Scans git diff for modified files
- Generates checklist of documentation files that need updates
- Kiro runs this at end of task execution
- Blocks task completion until all docs updated

## Components and Interfaces

### 1. Kiro Steering File

```markdown
# .kiro/steering/waterlib-workflow.md
---
inclusion: always
---

# Waterlib Development Workflow

This file teaches Kiro how to work with the waterlib project.

## Context Files to Load

When starting any waterlib feature development, load these files into context:

1. **DEVELOPER_GUIDE.md** - Architecture patterns, Kernel/Component separation, Pydantic validation
2. **QA_INFRASTRUCTURE.md** - Testing requirements, pre-commit hooks, documentation standards
3. **COMPONENTS.md** - Existing components for reference
4. **README.md** - High-level project overview

## Architectural Constraints

### Kernel Purity Rule
- Kernels (in `waterlib/kernels/`) MUST NOT import from `waterlib/components/`
- This is enforced by `waterlib_lint.py`
- Always run linter before tests: `python waterlib_lint.py && pytest`

### Pydantic Validation
- All new components MUST use Pydantic for parameter validation
- Create a `ComponentNameConfig(BaseModel)` class
- Use `model_config = {'extra': 'forbid'}` to catch typos
- Use `Field()` constraints for validation

## Documentation Synchronization

When modifying code, update these files:

### If adding/modifying a Component:
- [ ] Update `COMPONENTS.md` with parameter table
- [ ] Update `docs/API_REFERENCE.md` if public API changed
- [ ] Update `CHANGELOG.md` under "## Unreleased"
- [ ] Add example to `examples/` if new component

### If adding/modifying a Kernel:
- [ ] Update `DEVELOPER_GUIDE.md` if new kernel pattern
- [ ] Update `docs/API_REFERENCE.md` if public kernel function
- [ ] Update `CHANGELOG.md` under "## Unreleased"

### If modifying core framework:
- [ ] Update `docs/API_REFERENCE.md` with new signatures
- [ ] Update `DEVELOPER_GUIDE.md` if architecture changed
- [ ] Update `README.md` if user-facing behavior changed
- [ ] Update `CHANGELOG.md` under "## Unreleased"

## Task Execution Pattern

For every task:
1. Write code
2. Run `python waterlib_lint.py` (architectural validation)
3. If linter fails, fix architectural issues and return to step 1
4. Run `pytest` (functional validation)
5. If tests fail, fix bugs and return to step 4
6. Run `python scripts/check_doc_sync.py` (documentation validation)
7. Update any missing documentation
8. Mark task complete

## Requirements Format

Use EARS (Easy Approach to Requirements Syntax):
- WHEN <trigger>, THE <system> SHALL <response>
- WHILE <condition>, THE <system> SHALL <response>
- IF <condition>, THEN THE <system> SHALL <response>

## Testing Strategy

- Write unit tests for all new functions/classes
- Use Hypothesis for property-based tests where appropriate
- Test Pydantic validation directly (test the Config class)
- Mock drivers using `DriverRegistry` for component tests
```

### 2. Documentation Sync Checker

```python
# scripts/check_doc_sync.py
"""
Check if documentation is synchronized with code changes.

This script:
1. Gets list of modified files from git
2. Determines which documentation files need updates
3. Outputs a checklist for Kiro to verify
4. Returns exit code 1 if any docs are missing updates
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Set

def get_modified_files() -> List[str]:
    """Get list of modified files from git."""
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD'],
        capture_output=True,
        text=True
    )
    return [f for f in result.stdout.strip().split('\n') if f]

def determine_required_docs(modified_files: List[str]) -> Set[str]:
    """Determine which documentation files need updates."""
    required_docs = set()

    for file in modified_files:
        # Component changes
        if 'waterlib/components/' in file and file.endswith('.py'):
            required_docs.add('COMPONENTS.md')
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

        # Kernel changes
        elif 'waterlib/kernels/' in file and file.endswith('.py'):
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

        # Core framework changes
        elif 'waterlib/core/' in file and file.endswith('.py'):
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('DEVELOPER_GUIDE.md')
            required_docs.add('CHANGELOG.md')

        # Climate utilities
        elif 'waterlib/climate.py' in file:
            required_docs.add('README.md')
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

    return required_docs

def check_docs_updated(required_docs: Set[str], modified_files: List[str]) -> Set[str]:
    """Check which required docs are missing from modified files."""
    modified_set = set(modified_files)
    missing_docs = required_docs - modified_set
    return missing_docs

def main():
    """Main entry point."""
    print("🔍 Checking documentation synchronization...")

    modified_files = get_modified_files()

    if not modified_files:
        print("✅ No modified files detected")
        return 0

    print(f"\n📝 Modified files ({len(modified_files)}):")
    for file in modified_files:
        print(f"  - {file}")

    required_docs = determine_required_docs(modified_files)

    if not required_docs:
        print("\n✅ No documentation updates required")
        return 0

    missing_docs = check_docs_updated(required_docs, modified_files)

    if not missing_docs:
        print("\n✅ All required documentation is updated")
        return 0

    print("\n❌ Missing documentation updates:")
    for doc in sorted(missing_docs):
        print(f"  - {doc}")

    print("\n📋 Documentation Update Checklist:")
    print("=" * 60)

    if 'COMPONENTS.md' in missing_docs:
        print("\n[ ] COMPONENTS.md")
        print("    - Add/update parameter table for modified component")
        print("    - Update description if behavior changed")
        print("    - Add example YAML if new component")

    if 'docs/API_REFERENCE.md' in missing_docs:
        print("\n[ ] docs/API_REFERENCE.md")
        print("    - Update function signatures")
        print("    - Update parameter descriptions")
        print("    - Add new public functions/classes")

    if 'CHANGELOG.md' in missing_docs:
        print("\n[ ] CHANGELOG.md")
        print("    - Add entry under '## Unreleased'")
        print("    - Use format: '- Added/Fixed/Changed: <description>'")

    if 'DEVELOPER_GUIDE.md' in missing_docs:
        print("\n[ ] DEVELOPER_GUIDE.md")
        print("    - Update architecture diagrams if structure changed")
        print("    - Update patterns section if new pattern introduced")

    if 'README.md' in missing_docs:
        print("\n[ ] README.md")
        print("    - Update feature list if user-facing change")
        print("    - Update examples if API changed")

    print("\n" + "=" * 60)
    print("\n💡 After updating docs, run this script again to verify")

    return 1

if __name__ == '__main__':
    sys.exit(main())
```

### 3. Pre-commit Hook Enhancement

```yaml
# .pre-commit-config.yaml (additions)

repos:
  # ... existing hooks ...

  - repo: local
    hooks:
      - id: waterlib-lint
        name: Waterlib Architecture Lint
        entry: python waterlib_lint.py
        language: system
        pass_filenames: false
        always_run: true

      - id: doc-sync-check
        name: Documentation Sync Check
        entry: python scripts/check_doc_sync.py
        language: system
        pass_filenames: false
        stages: [commit]
```

**How it works:**
1. Developer makes code changes
2. Runs `git commit`
3. Pre-commit automatically runs:
   - `waterlib_lint.py` - Blocks if architectural violations
   - `check_doc_sync.py` - Warns if docs need updates (doesn't block)
4. Developer fixes issues and commits again

## Data Models

### DocSyncResult

```python
@dataclass
class DocSyncResult:
    """Result from documentation sync check."""
    required_docs: Set[str]         # Docs that need updates
    missing_docs: Set[str]          # Docs not yet updated
    modified_files: List[str]       # Code files that were changed
    is_synced: bool                 # True if all docs updated
```

## Error Handling

### Linter Failures

When `waterlib_lint.py` fails:
1. Pre-commit hook blocks the commit
2. Error message shows which file violates kernel purity
3. Developer fixes the import
4. Commits again

### Documentation Sync Failures

When `check_doc_sync.py` detects missing docs:
1. Script outputs checklist of required updates
2. Kiro sees this output and reminds user
3. User updates documentation
4. Runs check again to verify
5. Marks task complete once all docs updated

### Test Failures

When pytest fails:
1. Kiro attempts to fix (built-in retry logic)
2. After 2-3 attempts, asks user for help
3. User provides guidance or fixes manually
4. Kiro continues with next task

## Testing Strategy

### Test the Documentation Sync Checker

```python
# tests/test_check_doc_sync.py

def test_component_change_requires_docs():
    """Test that component changes flag required docs."""
    modified_files = ['waterlib/components/reservoir.py']
    required = determine_required_docs(modified_files)

    assert 'COMPONENTS.md' in required
    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required

def test_kernel_change_requires_docs():
    """Test that kernel changes flag required docs."""
    modified_files = ['waterlib/kernels/hydrology/awbm.py']
    required = determine_required_docs(modified_files)

    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required
    assert 'COMPONENTS.md' not in required  # Kernels don't affect components

def test_all_docs_updated():
    """Test detection when all docs are updated."""
    modified_files = [
        'waterlib/components/reservoir.py',
        'COMPONENTS.md',
        'docs/API_REFERENCE.md',
        'CHANGELOG.md'
    ]
    required = determine_required_docs(modified_files)
    missing = check_docs_updated(required, modified_files)

    assert len(missing) == 0
```

### Test Pre-commit Integration

```bash
# Manual test of pre-commit hooks
# 1. Make a change that violates kernel purity
echo "from waterlib.components.reservoir import Reservoir" > waterlib/kernels/test.py

# 2. Try to commit
git add waterlib/kernels/test.py
git commit -m "Test"

# Expected: Pre-commit blocks with error message

# 3. Fix the violation
rm waterlib/kernels/test.py

# 4. Commit succeeds
git commit -m "Test"
```

## Implementation Notes

### Phase 1: Immediate Value (This Week)
1. Create `.kiro/steering/waterlib-workflow.md` with context loading rules
2. Create `scripts/check_doc_sync.py` for documentation validation
3. Update `.pre-commit-config.yaml` to include doc sync check
4. Test with next waterlib feature

### Phase 2: Refinement (As Needed)
1. Improve `check_doc_sync.py` heuristics based on real usage
2. Add more specific documentation templates to steering file
3. Create helper scripts for common doc update patterns

### Dependencies

```python
# No new dependencies required
# Uses existing: git, waterlib_lint.py, pytest, pre-commit
```

### File Structure

```
.kiro/
└── steering/
    └── waterlib-workflow.md    # Kiro context and rules

scripts/
├── check_doc_sync.py           # Documentation sync checker
└── check_kernel_imports.py     # Existing linter

.pre-commit-config.yaml          # Enhanced with doc sync check

planning/
├── <feature-name-1>/           # Feature-specific directory (Kiro creates)
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── <feature-name-2>/
    └── ...
```

## Future Enhancements

1. **AST-Based Doc Updates**: Parse Python files to automatically update COMPONENTS.md parameter tables
2. **Smart Changelog Generation**: Analyze git commits to suggest changelog entries
3. **Documentation Diff Preview**: Show what will change in docs before committing
4. **Component Template Generator**: Quick scaffolding for new components with all docs pre-filled
5. **Validation Dashboard**: Web UI showing documentation coverage and sync status
