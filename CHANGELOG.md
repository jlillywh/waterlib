# Changelog

All notable changes to this project will be documented in this file.

## [1.1.2] - 2025-11-29
### Added
- **NEW COMPONENT**: `MetStation` component for recording and persisting climate driver data
  - Records precipitation, temperature (tmin/tmax), solar radiation, and reference ET
  - Configurable logging: choose which climate variables to record via direct parameters
  - Export methods: `to_dataframe()` and `export_csv(path)`
  - Useful for validating climate inputs and analyzing weather patterns
  - Works with any climate mode (WGEN, timeseries, or stochastic)
  - Automatically receives climate data from DriverRegistry (no explicit connections needed)
  - 13 comprehensive unit tests covering all functionality and edge cases
  - **YAML format**: Parameters passed directly (e.g., `log_precip: true`), not nested under `config:`

### Changed
- **Temperature data format**: DriverRegistry now provides temperature as `{'tmin': x, 'tmax': y}` dict instead of scalar average
  - Catchment component updated to handle both dict and scalar formats (backward compatible)
  - Enables components to access both tmin and tmax when needed
  - MetStation can now properly record both temperature values
- **Solar radiation driver**: Now properly registered in DriverRegistry when available
- Updated project scaffolding template to include commented-out MetStation example
- Enhanced sample script to automatically export climate data if MetStation is enabled

### Documentation
- Added MetStation to API_REFERENCE.md with complete Python API documentation
- Added MetStation to YAML_SCHEMA.md with configuration examples
- Added MetStation to COMPONENTS.md with detailed usage guide
- Enhanced climate data documentation in README.md, GETTING_STARTED.md, and COMPONENTS.md:
  - How to switch between WGEN and timeseries modes
  - Mixed mode examples (WGEN + timeseries)
  - Emphasis on source-agnostic component design
  - Type-safe DriverRegistry API examples
- Updated all documentation to show new temperature dict format

### Fixed
- Temperature driver registration now provides full tmin/tmax data instead of just average
- Solar radiation driver now properly registered when configured
- **MetStation parameter structure**: Fixed inconsistency - parameters are now passed directly in YAML (matching standard component pattern) instead of nested under `config:` key
  - YAML: `log_precip: true` (not `config: {log_precip: true}`)
  - Python: `MetStation(drivers, log_precip=True)` (not `MetStation(drivers, config=...)`)
  - Consistent with other components like Reservoir, Catchment, etc.

### Development Tooling
- **NEW**: Kiro steering file (`.kiro/steering/waterlib-workflow.md`) for automated workflow guidance
  - Loads DEVELOPER_GUIDE.md and QA_INFRASTRUCTURE.md into Kiro context
  - Enforces kernel purity rule and Pydantic validation patterns
  - Provides documentation synchronization checklists
  - Defines task execution pattern (lint → test → doc check)
- **NEW**: Documentation sync checker (`scripts/check_doc_sync.py`)
  - Scans git diff to detect which docs need updates
  - Generates checklist for COMPONENTS.md, API_REFERENCE.md, CHANGELOG.md
  - Integrated into pre-commit hooks for automatic validation
- **ENHANCED**: Pre-commit configuration with new hooks
  - `waterlib-lint`: Enforces kernel purity (blocks commits with violations)
  - `doc-sync-check`: Warns about missing documentation updates
  - Provides fast feedback loop during development

---

## [1.1.1] - 2025-11-28
### Fixed
- **CRITICAL**: Scaffold template now includes proper data connections between reservoir and demand
  - Previously generated models had 0% demand fulfillment due to missing connections
  - Added bidirectional data_connections: reservoir→demand (outflow) and demand→reservoir (release)
  - New projects created with `create_project()` now work correctly out of the box
- Reservoir evaporation now properly accesses ET data from DriverRegistry
- Fixed attribute check order: now checks for `.climate` before `.get()` to ensure modern driver access takes priority
- Baseline scaffold model now demonstrates lake evaporation functionality

### Changed
- Reservoir component now supports both legacy `global_data.get('evaporation')` and modern `drivers.climate.et` access patterns
- Updated version to 1.1.1

### Technical Details
- DriverRegistry has both `.get()` method (for legacy compatibility) and `.climate` attribute (for modern access)
- Original code checked `hasattr(global_data, 'get')` first, which matched DriverRegistry but used wrong accessor
- Fixed by checking `hasattr(global_data, 'climate')` first, ensuring ET values are properly retrieved
- Scaffold template was missing the data_connections block that enables water transfer between components

---

## [1.1.0] - 2025-11-28
### Added
- **NEW COMPONENT**: `Pump` component for active water withdrawal with intelligent control
  - Deadband control mode: Three-tier operation (conservation/normal/drawdown) based on storage level
  - Proportional control mode: Flow proportional to control error with capacity limiting
  - Withdrawal pump semantics: error = current - target (positive when above target)
  - Demand-aware operation: Respects downstream demand requests when provided
  - Seasonal target support: Lookup table with linear interpolation between day-of-year points
  - Example: Reservoir pump that withdraws water when storage is above target, supplies demand while maintaining minimum storage
- **YAML data_connections**: Components can now receive explicit data inputs beyond automatic inflow connections
  - New `data_connections` field in component YAML configuration
  - Format: `source: component.output`, `output: output_name`, `input: input_name`
  - Enables feedback control scenarios: pump monitors reservoir.storage, receives demand.demand
  - Registered connections are processed before each timestep via `_transfer_data()`
  - Example: `data_connections: [{source: reservoir.storage, output: storage, input: reservoir.storage}]`
- Enhanced loader to process YAML `data_connections` fields automatically
- All 14 pump unit tests validating both control modes and edge cases

### Changed
- Updated version to 1.1.0 (significant feature additions)
- Pump component now part of core component library

### Documentation
- Added comprehensive pump documentation to COMPONENTS.md with control mode examples
- Added data_connections schema documentation to YAML_SCHEMA.md
- Updated baseline.yaml example model to demonstrate pump with data_connections

---

## [1.0.9] - 2025-11-28
### Fixed
- Fixed reservoir component not receiving inflows from upstream components. The reservoir now correctly sums all indexed inflow inputs (`inflow_1`, `inflow_2`, etc.) that are set by the simulation engine when processing the `inflows` configuration.
- Previously, reservoirs would remain at initial storage even when receiving significant runoff from catchments, as the component was only checking for a single `inflow` key instead of the indexed keys.

### Changed
- Updated version to 1.0.9.

---

## [1.0.8] - 2025-11-28
### Fixed
- **CRITICAL**: Fixed simulation results bug where all timesteps after the first showed identical values. Root cause was components returning direct references to `self.outputs` dictionary instead of copies, causing all timesteps to point to the same object that only reflected the final state.
- Modified all component classes (`Catchment`, `Reservoir`, `Pump`, `Diversion`, `Demand`, `Junction`, `Logic`) to return `self.outputs.copy()` instead of `self.outputs`.
- This ensures each timestep captures independent values that vary with changing climate inputs and component states.
- Impact: Simulations now correctly produce varying results across timesteps (e.g., 318+ unique runoff values instead of 1 frozen value).

### Changed
- Updated version to 1.0.8.

---

## [1.0.7] - 2025-11-27
### Added
- Project scaffolding now appends a "Component Interfaces" section to the generated README.md, summarizing the outputs for each core component (Catchment, Reservoir, Demand, Pump, RiverDiversion, Junction, Weir) for end-user convenience. This is extracted from COMPONENTS.md.
- End users can now easily reference output column names for analysis directly in their project README.

### Changed
- Incremented version to1.0.7 in waterlib/__init__.py.

---

## [1.0.6] -2025-11-27
### Changed
- Updated `GETTING_STARTED.md` to reference `run_model.py` instead of `custom_script.py` in all relevant sections, ensuring documentation matches the actual project scaffolding output.
- Incremented version to1.0.6 in `waterlib/__init__.py`.

### Procedure
- Documentation update follows guidelines in `DEVELOPER_GUIDE.md`.
- No code or API changes.

---
