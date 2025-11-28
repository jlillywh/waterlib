# Requirements Document

## Introduction

This specification addresses a critical configuration parameter naming inconsistency in waterlib's climate driver system. The documentation and examples consistently show climate drivers configured with a `params:` nested dictionary (e.g., `precipitation.params.mean_annual`), but the `DriverConfig` dataclass does not accept a `params` parameter, causing runtime errors when users follow the documentation.

This inconsistency creates a poor user experience where following the official documentation results in immediate errors. The fix will align the code implementation with the documented API, ensuring users can successfully run examples from the getting started guide.

## Glossary

- **DriverConfig**: A dataclass in `waterlib/core/config.py` that configures a single climate driver (precipitation, temperature, or ET)
- **Climate Driver**: A component that provides climate data (precipitation, temperature, evapotranspiration) to the model
- **Stochastic Mode**: Climate generation mode that uses statistical parameters to generate synthetic data
- **Timeseries Mode**: Climate mode that loads historical data from CSV files
- **YAML Configuration**: The model.yaml file format used to define waterlib models
- **Getting Started Guide**: The primary user documentation at `GETTING_STARTED.md`
- **YAML Schema**: The reference documentation at `docs/YAML_SCHEMA.md`

## Requirements

### Requirement 1

**User Story:** As a waterlib user, I want to configure climate drivers using the documented `params:` syntax, so that I can follow the getting started guide without encountering errors.

#### Acceptance Criteria

1. WHEN a user configures a climate driver with `params:` nested dictionary THEN the system SHALL accept and parse the configuration without errors
2. WHEN the DriverConfig class is instantiated with a `params` parameter THEN it SHALL extract the nested parameters correctly
3. WHEN a user follows the getting started guide examples THEN the system SHALL run successfully without configuration errors
4. WHEN the DriverConfig.from_dict method is called with a dictionary containing `params` THEN it SHALL flatten the nested structure appropriately
5. WHEN backward compatibility is required THEN the system SHALL support both the old flat structure and the new nested `params:` structure

### Requirement 2

**User Story:** As a waterlib developer, I want the code implementation to match the documented API, so that users trust the documentation and have a consistent experience.

#### Acceptance Criteria

1. WHEN the DriverConfig dataclass is examined THEN it SHALL have a structure that supports the documented `params:` syntax
2. WHEN ClimateSettings.from_dict parses driver configurations THEN it SHALL handle both nested `params:` dictionaries and flat parameter structures
3. WHEN the configuration parsing logic is reviewed THEN it SHALL be clear and maintainable
4. WHEN new climate parameters are added THEN they SHALL follow the established `params:` pattern
5. WHEN the code is refactored THEN all existing tests SHALL continue to pass

### Requirement 3

**User Story:** As a waterlib user, I want clear documentation that matches the actual implementation, so that I can configure my models correctly the first time.

#### Acceptance Criteria

1. WHEN the getting started guide is reviewed THEN all climate configuration examples SHALL use the correct syntax
2. WHEN the YAML schema documentation is reviewed THEN it SHALL accurately describe the DriverConfig structure
3. WHEN the README examples are reviewed THEN they SHALL use the correct configuration syntax
4. WHEN the API reference is reviewed THEN it SHALL document the correct parameter structure
5. WHEN example YAML files are reviewed THEN they SHALL use the correct configuration syntax

### Requirement 4

**User Story:** As a waterlib user, I want helpful error messages when I misconfigure climate drivers, so that I can quickly identify and fix configuration problems.

#### Acceptance Criteria

1. WHEN a user provides invalid climate configuration THEN the system SHALL raise a ConfigurationError with a clear message
2. WHEN a user mixes flat and nested parameter syntax incorrectly THEN the system SHALL provide guidance on the correct format
3. WHEN a required parameter is missing THEN the error message SHALL specify which parameter is missing and where it should be placed
4. WHEN a user provides an unexpected parameter THEN the error message SHALL list the valid parameters for that driver mode
5. WHEN configuration parsing fails THEN the error message SHALL include the component name and configuration block that failed

### Requirement 5

**User Story:** As a waterlib developer, I want comprehensive tests for climate configuration parsing, so that configuration errors are caught before users encounter them.

#### Acceptance Criteria

1. WHEN the test suite is run THEN it SHALL include tests for nested `params:` syntax
2. WHEN the test suite is run THEN it SHALL include tests for flat parameter syntax (backward compatibility)
3. WHEN the test suite is run THEN it SHALL include tests for mixed valid and invalid configurations
4. WHEN the test suite is run THEN it SHALL include tests for all documented examples from the getting started guide
5. WHEN the test suite is run THEN it SHALL include tests for error messages and validation

### Requirement 6

**User Story:** As a waterlib user, I want the project scaffolding to generate correct configuration files, so that generated projects work immediately without modification.

#### Acceptance Criteria

1. WHEN create_project generates a baseline.yaml file THEN it SHALL use the correct climate configuration syntax
2. WHEN the generated baseline.yaml is loaded THEN it SHALL parse without errors
3. WHEN the generated run_model.py script is executed THEN it SHALL run successfully
4. WHEN the scaffolding templates are reviewed THEN they SHALL use the documented `params:` syntax
5. WHEN users create new projects THEN they SHALL receive working examples that match the documentation

### Requirement 7

**User Story:** As a waterlib developer, I want a migration guide for users with existing models, so that they can update their configurations if needed.

#### Acceptance Criteria

1. WHEN a migration guide is created THEN it SHALL explain the difference between old and new syntax
2. WHEN a migration guide is created THEN it SHALL provide examples of converting old configurations to new format
3. WHEN backward compatibility is maintained THEN the migration guide SHALL note that old configurations still work
4. WHEN the migration guide is reviewed THEN it SHALL include a script or tool to automatically convert old configurations
5. WHEN users need to update configurations THEN they SHALL have clear, actionable guidance

### Requirement 8

**User Story:** As a waterlib user, I want consistent parameter naming across all climate driver modes, so that I can easily understand and modify configurations.

#### Acceptance Criteria

1. WHEN stochastic mode is configured THEN it SHALL use `params:` for nested parameters
2. WHEN timeseries mode is configured THEN it SHALL use flat parameters (file, column) at the driver level
3. WHEN the configuration structure is reviewed THEN the distinction between modes SHALL be clear and logical
4. WHEN users switch between modes THEN the parameter structure SHALL be intuitive
5. WHEN the configuration is validated THEN mode-specific parameters SHALL be checked appropriately

### Requirement 9

**User Story:** As a waterlib developer, I want the DriverConfig class to be extensible, so that new climate driver modes can be added easily.

#### Acceptance Criteria

1. WHEN a new driver mode is added THEN the DriverConfig class SHALL accommodate it without major refactoring
2. WHEN mode-specific parameters are needed THEN they SHALL be handled through the `params:` structure or mode-specific fields
3. WHEN the DriverConfig class is reviewed THEN it SHALL follow Python dataclass best practices
4. WHEN new functionality is added THEN existing configurations SHALL remain valid
5. WHEN the architecture is reviewed THEN the separation between mode and parameters SHALL be clear

### Requirement 10

**User Story:** As a waterlib user, I want example models in the examples directory to work correctly, so that I can learn from working code.

#### Acceptance Criteria

1. WHEN example YAML files are loaded THEN they SHALL parse without configuration errors
2. WHEN example Python scripts are run THEN they SHALL execute successfully
3. WHEN the examples directory is reviewed THEN all climate configurations SHALL use the correct syntax
4. WHEN users copy examples THEN they SHALL receive working code that matches the documentation
5. WHEN examples are updated THEN they SHALL be tested to ensure they remain functional
