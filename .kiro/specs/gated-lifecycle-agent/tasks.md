# Implementation Plan

## Overview

Implement three lightweight enforcement mechanisms to ensure waterlib documentation stays synchronized with code changes. All tasks integrate with existing Kiro workflow and tools.

---

## Tasks

- [x] 1. Create Kiro steering file for waterlib workflow



  - Create `.kiro/steering/waterlib-workflow.md` with context loading rules
  - Include DEVELOPER_GUIDE.md and QA_INFRASTRUCTURE.md loading instructions
  - Add documentation update checklists for components, kernels, and core changes
  - Include architectural constraints (kernel purity, Pydantic validation)
  - Add task execution pattern (lint → test → doc check)
  - Use EARS format examples for requirements
  - **Add backward compatibility policy: "Zero legacy support - breaking changes accepted, fail fast with clear errors"**
  - _Requirements: 2.2, 2.6_

- [x] 2. Create documentation synchronization checker script





  - Create `scripts/check_doc_sync.py` with git diff scanning
  - Implement `get_modified_files()` function using subprocess
  - Implement `determine_required_docs()` to categorize changes
  - Implement `check_docs_updated()` to find missing documentation
  - Add checklist output for COMPONENTS.md updates
  - Add checklist output for API_REFERENCE.md updates
  - Add checklist output for CHANGELOG.md updates
  - Return exit code 0 if synced, 1 if missing docs
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 3. Update pre-commit configuration





  - Add `waterlib-lint` hook to `.pre-commit-config.yaml`
  - Add `doc-sync-check` hook to `.pre-commit-config.yaml`
  - Configure hooks to run on commit stage
  - Test that linter blocks commits with violations
  - Test that doc checker warns about missing updates
  - _Requirements: 5.3, 5.4_

- [ ] 4. Test the complete workflow
  - Make a test change to a component file
  - Run `python scripts/check_doc_sync.py` manually
  - Verify it detects missing COMPONENTS.md update
  - Update COMPONENTS.md
  - Run checker again to verify it passes
  - Test pre-commit hooks with `git commit`
  - Verify Kiro loads steering file context
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 5. Create project cleanup script and update .gitignore
  - Create `scripts/cleanup_temp_files.py` to remove temp files
  - Scan for common temp patterns: `debug_*.py`, `test_*.py` (in root), `temp_*.txt`, `*.tmp`
  - Move debug scripts to `scripts/debug/` directory
  - Move test scripts to `tests/manual/` directory
  - Update `.gitignore` to ignore `scripts/debug/` and `tests/manual/`
  - Update `.gitignore` to ignore `temp_*.txt` and `*.tmp` in root
  - Add pre-commit hook to warn about files in root that should be in subdirectories
  - _Requirements: 10.1, 10.2_

- [ ] 6. Document the new workflow
  - Update QA_INFRASTRUCTURE.md with new enforcement mechanisms
  - Add section explaining the three-layer enforcement
  - Add usage examples for `check_doc_sync.py`
  - Add section on project organization (where to put debug/test scripts)
  - Add troubleshooting guide for common issues
  - Update CHANGELOG.md with new tooling
  - _Requirements: 6.7, 10.5_

---

## Notes

- All tasks use existing tools (git, subprocess, pathlib)
- No new dependencies required
- Integrates seamlessly with Kiro's spec workflow
- Pre-commit hooks provide fast feedback loop
- Documentation checker is simple and maintainable
- Cleanup script helps maintain tidy project structure
