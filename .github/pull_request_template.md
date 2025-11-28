## Description

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] ⚡ Performance improvement

## The "Definition of Done" Checklist

### 1. Architecture & Quality
- [ ] **Kernel Purity:** I have verified that no files in `waterlib/kernels/` import from `waterlib/components/`.
- [ ] **Pydantic Validation:** If I added a component, I used a `Config` class with strict validation (no manual `if` checks in `__init__`).
- [ ] **Type Hints:** All new functions and arguments have type hints.

### 2. Testing
- [ ] **Unit Tests:** Added tests for new features/bug fixes.
- [ ] **Passes Local:** Ran `pytest` and all tests passed.

### 3. Documentation
- [ ] **Docstrings:** Updated/added Google-style docstrings.
- [ ] **API Reference:** If API changed, updated `docs/API_REFERENCE.md`.
- [ ] **Component Reference:** If I changed parameters, I updated `COMPONENTS.md` (tables, examples).
- [ ] **Developer Guide:** If I changed architecture, I updated `DEVELOPER_GUIDE.md`.

### 4. Examples & Scaffolding
- [ ] **Broken Examples:** I checked `examples/` to ensure my changes didn't break existing scripts.
- [ ] **New Example:** If this is a new feature, I added a script to `examples/` demonstrating how to use it.
- [ ] **Scaffolding:** If I added files, I updated `waterlib/core/scaffold.py` to include them in `create_project()`.
