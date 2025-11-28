# Implementation Plan

- [x] 1. Update WGENParams dataclass with new parameter structure






  - Modify `waterlib/kernels/climate/wgen.py`
  - Replace old parameter structure with monthly lists (pww, pwd, alpha, beta)
  - Add constant temperature parameters (txmd, atx, txmw, tn, atn, cvtx, acvtx, cvtn, acvtn)
  - Add constant radiation parameters (rmd, ar, rmw)
  - Add latitude parameter
  - Implement `__post_init__` validation for list lengths, probability ranges, positive values, and latitude range
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.6, 2.7_

- [ ]* 1.1 Write property test for monthly parameter validation
  - **Property 1: Monthly parameter lists have exactly 12 values**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [ ]* 1.2 Write property test for latitude validation
  - **Property 2: Latitude validation**
  - **Validates: Requirements 2.3**

- [x] 2. Update WGENState dataclass to include current_date




  - Add `current_date: datetime.date` field to WGENState
  - Update docstring to explain date is needed for monthly parameter selection
  - _Requirements: 3.4_

- [x] 3. Implement helper functions for unit conversion and calculations





  - Create `_celsius_to_kelvin(temp_c: float) -> float` function
  - Create `_kelvin_to_celsius(temp_k: float) -> float` function
  - Create `_get_monthly_params(params: WGENParams, month: int) -> Tuple[float, float, float, float]` function
  - Create `_calculate_seasonal_temp(mean, amplitude, day_of_year, latitude) -> float` function using Fourier
  - Create `_calculate_seasonal_radiation(mean, amplitude, day_of_year, latitude) -> float` function using Fourier
  - _Requirements: 2.5, 3.4_

- [ ]* 3.1 Write property test for temperature conversion round-trip
  - **Property 3: Temperature unit conversion round-trip**
  - **Validates: Requirements 2.5**

- [ ]* 3.2 Write unit tests for helper functions
  - Test `_get_monthly_params` with various months (1-12)
  - Test Fourier functions with known inputs/outputs
  - Test edge cases (day_of_year boundaries, latitude extremes)
  - _Requirements: 2.5, 3.4_

- [x] 4. Update wgen_step function to use new parameter structure





  - Modify function signature to accept updated WGENParams and WGENState
  - Extract current month from state.current_date
  - Call `_get_monthly_params` to get monthly precipitation parameters
  - Convert temperature parameters from Celsius to Kelvin internally
  - Apply Fourier functions for seasonal temperature/radiation calculations
  - Update function to return new_state with incremented date
  - Update docstring with new parameter descriptions
  - _Requirements: 2.5, 3.1, 3.3, 3.4_

- [ ]* 4.1 Write property test for function purity
  - **Property 4: Function purity**
  - **Validates: Requirements 3.1**

- [ ]* 4.2 Write property test for return type structure
  - **Property 5: Return type structure**
  - **Validates: Requirements 3.3**

- [ ]* 4.3 Write property test for monthly parameter selection
  - **Property 6: Monthly parameter selection**
  - **Validates: Requirements 3.4**

- [x] 5. Update wgen_params_template.csv file





  - Verify CSV has correct column headers: Month, PWW, PWD, ALPHA, BETA
  - Verify CSV has exactly 12 rows (one per month)
  - Update comments to reflect new interface structure
  - Add example values matching the user's provided data
  - _Requirements: 4.1_
-

- [x] 6. Update WGEN_PARAMETERS_GUIDE.md documentation




  - Document new parameter structure (monthly vs constant)
  - Add section explaining temperature/radiation parameters are constants
  - Document Fourier-based seasonal variation approach
  - Add latitude parameter documentation with valid range
  - Update YAML configuration examples with new parameter names
  - Update CSV format examples
  - Document units: Temperature in Celsius (interface), Precipitation in mm, Radiation in MJ/m²/day
  - _Requirements: 4.2, 4.3, 4.4_

- [x] 7. Update wgen_parameter_estimator.py





  - Modify `estimate_precipitation_params` to return monthly PWW, PWD, ALPHA, BETA
  - Create or update function to estimate constant temperature parameters (TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN)
  - Create or update function to estimate constant radiation parameters (RMD, AR, RMW)
  - Update output format to be compatible with new WGENParams structure
  - Update CLI to output both CSV (monthly params) and YAML snippet (constants)
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 7.1 Write property test for parameter estimation compatibility
  - **Property 7: Parameter estimation output compatibility**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ]* 7.2 Write unit tests for parameter estimation functions
  - Test with synthetic climate data
  - Verify output has correct structure (12 monthly values, scalar constants)
  - Test edge cases (all dry days, all wet days, constant temperature)
  - _Requirements: 5.1, 5.2, 5.3_
-

- [x] 8. Update test files that reference WGEN




  - Update `tests/unit/test_scaffold_data_files.py` to verify new CSV format
  - Update `tests/unit/test_config.py` if it tests WGEN configuration parsing
  - Ensure all existing tests pass with new interface
  - _Requirements: 6.1, 6.2, 6.3, 6.4_
-

- [x] 9. Update API documentation



  - Update `docs/API_REFERENCE.md` with new WGENParams structure
  - Add examples showing monthly precipitation parameters
  - Add examples showing constant temperature/radiation parameters
  - Document the Celsius-to-Kelvin conversion behavior
  - _Requirements: 7.1_  .kiro\specs\wgen-interface-restructure\requirements.md
-


- [x] 11. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.
