# Implementation Plan

- [x] 1. Create scaffold module with core infrastructure





  - Create `waterlib/core/scaffold.py` with module docstring
  - Implement input validation helper `_validate_project_name()`
  - Implement platform-specific invalid character detection
  - Add logging configuration
  - _Requirements: 4.1, 5.3_

- [ ]* 1.1 Write property test for project name validation
  - **Property 14: Invalid character rejection**
  - **Validates: Requirements 4.1**

- [x] 2. Implement directory structure creation





  - Implement `_create_directory_structure()` to create models/, data/, outputs/, config/
  - Implement `_cleanup_on_error()` for error recovery
  - Handle parent directory validation
  - _Requirements: 1.1, 1.3, 1.5, 4.2, 4.4_

- [ ]* 2.1 Write property test for directory structure
  - **Property 3: Standard subdirectory structure**
  - **Validates: Requirements 1.3**

- [ ]* 2.2 Write property test for cleanup on error
  - **Property 16: Cleanup on error**
  - **Validates: Requirements 4.4**

- [x] 3. Implement file template generation





  - Implement `_generate_readme()` with project name interpolation
  - Implement `_generate_sample_model()` with YAML template
  - Implement `_generate_sample_script()` with Python template
  - Store templates as module-level string constants
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 3.1 Write property test for README generation
  - **Property 6: README generation**
  - **Validates: Requirements 2.1**

- [ ]* 3.2 Write property test for generated file validity
  - **Property 12: Generated file validity**
  - **Validates: Requirements 2.6**

- [x] 4. Implement data file generation





  - Implement `_generate_wgen_params()` to write WGEN params from module constant
  - Implement `_generate_climate_timeseries()` to write example climate data
  - Implement `_generate_data_readme()` to document data files
  - Store all data file content as string constants in scaffold.py
  - Write constants to data/ directory in the project
  - _Requirements: 2.4, 2.5_

- [ ]* 4.1 Write property test for WGEN parameters generation
  - **Property 9: WGEN parameters generation**
  - **Validates: Requirements 2.4**
  - Verify CSV is written from module constant, not copied from external file

- [ ]* 4.2 Write property test for climate timeseries generation
  - **Property 10: Climate timeseries generation**
  - **Validates: Requirements 2.5**
  - Verify CSV contains valid date, precip, temp, and ET columns

- [ ]* 4.3 Write property test for data README generation
  - **Property 11: Data directory README generation**
  - **Validates: Requirements 2.5**
  - Verify README exists in data directory and contains documentation

- [x] 5. Implement main create_project function





  - Implement `create_project()` with full signature
  - Add comprehensive docstring with parameters and examples
  - Implement overwrite parameter handling
  - Implement include_examples parameter handling
  - Return absolute path to created project
  - Add error handling with descriptive messages
  - _Requirements: 1.1, 1.2, 1.4, 2.6, 3.2, 3.3, 3.4, 4.5_

- [ ]* 5.1 Write property test for directory creation
  - **Property 1: Directory creation for valid names**
  - **Validates: Requirements 1.1**

- [ ]* 5.2 Write property test for existing directory protection
  - **Property 2: Existing directory protection**
  - **Validates: Requirements 1.2**

- [ ]* 5.3 Write property test for absolute path return
  - **Property 4: Absolute path return value**
  - **Validates: Requirements 1.4**

- [ ]* 5.4 Write property test for custom parent directory
  - **Property 5: Custom parent directory placement**
  - **Validates: Requirements 1.5**

- [ ]* 5.5 Write property test for minimal structure without examples
  - **Property 13: Minimal structure without examples**
  - **Validates: Requirements 2.7**

- [ ]* 5.6 Write property test for error message completeness
  - **Property 17: Error message completeness**
  - **Validates: Requirements 4.5**

- [x] 6. Expose create_project in waterlib API





  - Import create_project in `waterlib/core/__init__.py`
  - Export create_project in `waterlib/__init__.py`
  - Add to __all__ list
  - Update module docstring
  - _Requirements: 3.1_

- [ ]* 6.1 Write unit test for API exposure
  - Verify create_project is accessible from waterlib top level
  - Verify function signature is correct
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 7. Add integration tests
  - Test complete workflow: create project, verify all files, load YAML
  - Test project creation with custom parent directory
  - Test project creation without examples
  - Test that generated Python script is executable
  - _Requirements: 2.5_

- [x] 8. Update documentation





  - Add create_project to API reference documentation
  - Add usage examples to README or getting started guide
  - Document the generated project structure
  - Add troubleshooting section for common errors
  - _Requirements: 5.4_

- [x] 9. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
