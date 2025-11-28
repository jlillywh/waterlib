# Implementation Plan

- [x] 1. Create kernel directory structure





  - Create `waterlib/kernels/` directory
  - Create `waterlib/kernels/__init__.py` with module docstring
  - Create `waterlib/kernels/hydrology/` subdirectory
  - Create `waterlib/kernels/hydrology/__init__.py`
  - Create `waterlib/kernels/hydraulics/` subdirectory
  - Create `waterlib/kernels/hydraulics/__init__.py`
  - Create `waterlib/kernels/climate/` subdirectory
  - Create `waterlib/kernels/climate/__init__.py`
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 10.1_

- [x] 2. Extract and move Snow17 kernel





  - Extract pure Snow17 algorithm logic from `waterlib/components/snow17.py`
  - Create dataclasses for Snow17Params, Snow17State, Snow17Inputs, Snow17Outputs
  - Create `waterlib/kernels/hydrology/snow17.py` with pure `snow17_step()` function
  - Move helper functions (_interpolate_temperature, _calculate_melt_factor, etc.) to kernel
  - Update `waterlib/kernels/hydrology/__init__.py` to export Snow17 functions
  - _Requirements: 2.2, 2.5_

- [x] 2.1 Write unit tests for Snow17 kernel


  - Test snow17_step with known input/output pairs
  - Test snow accumulation at cold temperatures
  - Test melt at warm temperatures
  - Test rain-on-snow events
  - Test state transitions (w_i, w_q, ait, deficit)
  - _Requirements: 2.2_

- [x] 3. Extract and move AWBM kernel





  - Extract pure AWBM algorithm logic from `waterlib/components/awbm.py`
  - Create dataclasses for AWBMParams, AWBMState, AWBMInputs, AWBMOutputs
  - Create `waterlib/kernels/hydrology/awbm.py` with pure `awbm_step()` function
  - Move _calculate_awbm_update static method to kernel as main function
  - Update `waterlib/kernels/hydrology/__init__.py` to export AWBM functions
  - _Requirements: 2.3, 2.5_

- [x] 3.1 Write unit tests for AWBM kernel


  - Test awbm_step with known input/output pairs
  - Test surface store overflow
  - Test baseflow/surface flow splitting
  - Test routing store recession
  - Test state transitions for all 5 stores
  - _Requirements: 2.3_
-

- [x] 4. Extract and move weir kernel




  - Extract weir equation logic from `waterlib/components/weir.py`
  - Create dataclasses for WeirParams, WeirInputs, WeirOutputs
  - Create `waterlib/kernels/hydraulics/weir.py` with pure `weir_discharge()` function
  - Include spillway calculation functions
  - Update `waterlib/kernels/hydraulics/__init__.py` to export weir functions
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 4.1 Write unit tests for weir kernel


  - Test weir_discharge with various head values
  - Test zero discharge when head <= 0
  - Test discharge increases with head^1.5
  - Test different weir coefficients and widths
  - _Requirements: 3.2_

- [x] 5. Extract and move Hargreaves ET kernel





  - Extract Hargreaves-Samani calculation from `waterlib/components/hargreaves.py`
  - Create dataclasses for ETParams, ETInputs, ETOutputs
  - Create `waterlib/kernels/climate/et.py` with `hargreaves_et()` function
  - Move _calculate_ra helper function to kernel
  - Make extensible for future ET methods (Penman-Monteith, etc.)
  - Update `waterlib/kernels/climate/__init__.py` to export ET functions
  - _Requirements: 4.2, 4.4, 4.5_

- [x] 5.1 Write unit tests for Hargreaves ET kernel


  - Test hargreaves_et with known input/output pairs
  - Test ET calculation across different latitudes
  - Test ET calculation across different seasons (day of year)
  - Test with various temperature ranges
  - Test extraterrestrial radiation calculation
  - _Requirements: 4.2_

- [x] 6. Create WGEN kernel placeholder





  - Create `waterlib/kernels/climate/wgen.py` with module docstring
  - Add placeholder for WGEN implementation (to be completed in wgen-integration spec)
  - Create dataclasses for WGENParams, WGENState, WGENOutputs
  - Update `waterlib/kernels/climate/__init__.py` to export WGEN functions
  - _Requirements: 4.3, 4.4, 8.1, 8.4_
-

- [x] 7. Update Catchment component to use kernels




  - Update `waterlib/components/catchment.py` imports to use `waterlib.kernels.hydrology`
  - Refactor Catchment.__init__ to create kernel parameter objects
  - Refactor Catchment.step to call snow17_step and awbm_step kernels
  - Remove old algorithm code, keep only orchestration logic
  - Ensure Catchment remains a single graph node with same external interface
  - _Requirements: 5.1, 7.1, 7.2, 7.4_

- [x] 7.1 Write unit tests for updated Catchment component


  - Test Catchment initialization with kernel parameters
  - Test Catchment.step orchestrates both kernels correctly
  - Test Catchment outputs match expected format
  - Test Catchment with various input combinations
  - _Requirements: 7.1, 7.2_

- [x] 8. Update Reservoir component to use weir kernel





  - Update `waterlib/components/reservoir.py` imports to use `waterlib.kernels.hydraulics`
  - Refactor spillway logic to call weir_discharge kernel
  - Remove old weir equation code from Reservoir
  - Ensure Reservoir maintains same external interface
  - _Requirements: 5.1_

- [x] 8.1 Write unit tests for updated Reservoir component


  - Test Reservoir with spillway using weir kernel
  - Test spillway activation at max storage
  - Test spillway discharge calculation
  - _Requirements: 5.1_
- [x] 9. Update climate utilities to use ET kernel




- [ ] 9. Update climate utilities to use ET kernel

  - Update `waterlib/climate.py` imports to use `waterlib.kernels.climate`
  - Refactor any ET calculation code to call hargreaves_et kernel
  - Remove old Hargreaves calculation code
  - _Requirements: 5.1_

- [x] 10. Update all test imports





  - Search for all test files importing from old paths
  - Update test imports to use `waterlib.kernels.*` for kernel code
  - Update test imports to use `waterlib.components.*` for component code
  - Ensure no old import paths remain (e.g., `from waterlib.components.snow17`)
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 10.1 Write property test for kernel import isolation


  - **Property 1: Kernel Import Isolation**
  - **Validates: Requirements 1.3, 5.2**

- [x] 10.2 Write property test for component kernel imports


  - **Property 2: Component Kernel Imports**
  - **Validates: Requirements 5.1**

- [x] 10.3 Write property test for no circular dependencies


  - **Property 3: No Circular Dependencies**
  - **Validates: Requirements 5.3**

- [x] 10.4 Write property test for import path migration completeness


  - **Property 4: Import Path Migration Completeness**
  - **Validates: Requirements 5.5**

- [x] 10.5 Write property test for test import consistency


  - **Property 5: Test Import Consistency**
  - **Validates: Requirements 6.1, 6.2, 6.4**
-

- [x] 11. Run full test suite and fix failures




  - Run pytest on entire test suite
  - Fix any import errors
  - Fix any test failures due to refactoring
  - Ensure all existing tests pass with new structure
  - _Requirements: 6.3_

- [x] 12. Update kernel __init__.py exports





  - Review `waterlib/kernels/hydrology/__init__.py` and ensure all functions exported
  - Review `waterlib/kernels/hydraulics/__init__.py` and ensure all functions exported
  - Review `waterlib/kernels/climate/__init__.py` and ensure all functions exported
  - Add __all__ lists to each __init__.py for explicit exports
  - _Requirements: 10.2, 10.3_

- [x] 12.1 Write property test for kernel __init__ exports


  - **Property 6: Kernel __init__ Exports**
  - **Validates: Requirements 10.2**

- [x] 13. Remove old component files if fully migrated





  - Check if `waterlib/components/snow17.py` is still needed (likely yes, as wrapper)
  - Check if `waterlib/components/awbm.py` is still needed (likely yes, as wrapper)
  - Check if `waterlib/components/hargreaves.py` is still needed (likely yes, as wrapper)
  - Remove any files that are no longer needed
  - Add deprecation warnings to any backward compatibility shims
  - _Requirements: 5.5_
-

- [x] 14. Update documentation




  - Update developer guide to explain kernel vs component distinction
  - Document kernel development patterns (pure functions, dataclasses)
  - Document how components should use kernels
  - Add examples of kernel usage
  - Create migration guide for any external users
  - Update architecture diagrams to show kernel layer
  - _Requirements: 1.5_

- [x] 15. Final checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
