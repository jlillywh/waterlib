# Changelog

All notable changes to this project will be documented in this file.

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
