# Requirements Document

## Introduction

This document specifies the requirements for restructuring the WGEN (Weather Generator) kernel interface to accept a simplified, standardized parameter structure. The current implementation uses a complex parameter structure that doesn't align with the standard WGEN input format. The new interface will accept monthly precipitation parameters (PWW, PWD, ALPHA, BETA for each of 12 months), constant temperature/radiation parameters (13 scalar values), and latitude.

## Glossary

- **WGEN**: Weather Generator - A stochastic weather simulation model that generates synthetic daily weather data
- **PWW**: Probability of wet day following wet day (dimensionless, 0-1)
- **PWD**: Probability of wet day following dry day (dimensionless, 0-1)
- **ALPHA**: Gamma distribution shape parameter for precipitation (dimensionless, > 0)
- **BETA**: Gamma distribution scale parameter for precipitation (mm, > 0)
- **TXMD**: Mean maximum temperature on dry days (Celsius at interface, converted to Kelvin internally)
- **ATX**: Amplitude of maximum temperature seasonal variation (Celsius at interface, converted to Kelvin internally)
- **TXMW**: Mean maximum temperature on wet days (Celsius at interface, converted to Kelvin internally)
- **TN**: Mean minimum temperature (Celsius at interface, converted to Kelvin internally)
- **ATN**: Amplitude of minimum temperature seasonal variation (Celsius at interface, converted to Kelvin internally)
- **CVTX**: Coefficient of variation for maximum temperature mean (dimensionless)
- **ACVTX**: Coefficient of variation for maximum temperature amplitude (dimensionless)
- **CVTN**: Coefficient of variation for minimum temperature mean (dimensionless)
- **ACVTN**: Coefficient of variation for minimum temperature amplitude (dimensionless)
- **RMD**: Mean solar radiation on dry days (MJ/m²/day)
- **AR**: Amplitude of solar radiation seasonal variation (MJ/m²/day)
- **RMW**: Mean solar radiation on wet days (MJ/m²/day)
- **Latitude**: Geographic latitude of the station (degrees, -90 to 90)
- **Fourier Function**: Mathematical function using sine/cosine to model seasonal variations
- **Kernel**: Pure computational function with no side effects or dependencies on graph structure

## Requirements

### Requirement 1

**User Story:** As a hydrologist, I want to provide monthly precipitation parameters in a standard format, so that I can easily configure WGEN with data from published sources or parameter estimation tools.

#### Acceptance Criteria

1. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for PWW
2. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for PWD
3. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for ALPHA
4. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept 12 monthly values for BETA
5. WHEN monthly precipitation parameters are provided THEN the system SHALL validate that each list contains exactly 12 values

### Requirement 2

**User Story:** As a hydrologist, I want to provide constant temperature and radiation parameters with latitude, so that the system can simulate seasonal temperature and radiation patterns using Fourier functions.

#### Acceptance Criteria

1. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept scalar values for TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN, RMD, AR, and RMW
2. WHEN the WGENParams dataclass is instantiated THEN the system SHALL accept a latitude value in degrees
3. WHEN latitude is provided THEN the system SHALL validate that the value is between -90 and 90 degrees
4. WHEN temperature parameters are provided at the interface THEN the system SHALL accept values in Celsius
5. WHEN temperature calculations are performed internally THEN the system SHALL convert Celsius to Kelvin
6. WHEN radiation parameters are provided THEN the system SHALL accept values in MJ/m²/day
7. WHEN precipitation BETA parameters are provided THEN the system SHALL accept values in millimeters

### Requirement 3

**User Story:** As a developer, I want the WGEN kernel to remain a pure function, so that it maintains consistency with other kernels in the system.

#### Acceptance Criteria

1. WHEN the wgen_step function is called THEN the system SHALL compute outputs without side effects
2. WHEN the wgen_step function is called THEN the system SHALL not depend on graph structure or external state
3. WHEN the wgen_step function is called THEN the system SHALL return a tuple of (new_state, outputs)
4. WHEN the wgen_step function uses monthly parameters THEN the system SHALL select the appropriate month's values based on the current simulation date

### Requirement 4

**User Story:** As a developer, I want to update the parameter template files, so that they reflect the new simplified interface structure.

#### Acceptance Criteria

1. WHEN the wgen_params_template.csv file is updated THEN the system SHALL maintain the 12-month structure with PWW, PWD, ALPHA, BETA columns
2. WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document the new temperature/radiation parameter structure
3. WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document that temperature/radiation parameters are constants with Fourier-based seasonal variation
4. WHEN the WGEN_PARAMETERS_GUIDE.md is updated THEN the system SHALL document the latitude parameter and its valid range

### Requirement 5

**User Story:** As a developer, I want to update the parameter estimation utility, so that it generates parameters in the new format.

#### Acceptance Criteria

1. WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate monthly PWW, PWD, ALPHA, BETA values
2. WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate constant temperature parameters (TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN)
3. WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL estimate constant radiation parameters (RMD, AR, RMW)
4. WHEN the wgen_parameter_estimator.py is updated THEN the system SHALL output parameters in a format compatible with the new WGENParams structure

### Requirement 6

**User Story:** As a developer, I want to update all tests that reference WGEN, so that they validate the new interface structure.

#### Acceptance Criteria

1. WHEN unit tests are updated THEN the system SHALL test WGENParams instantiation with monthly precipitation parameters
2. WHEN unit tests are updated THEN the system SHALL test WGENParams instantiation with constant temperature/radiation parameters
3. WHEN unit tests are updated THEN the system SHALL test parameter validation (12 monthly values, latitude range)
4. WHEN unit tests are updated THEN the system SHALL test that wgen_step correctly selects monthly parameters based on simulation date

### Requirement 7

**User Story:** As a developer, I want to update documentation that references WGEN, so that users understand the new interface.

#### Acceptance Criteria

1. WHEN API_REFERENCE.md is updated THEN the system SHALL document the new WGENParams structure
2. WHEN KERNEL_MIGRATION_GUIDE.md is updated THEN the system SHALL provide examples of the new parameter format
3. WHEN documentation is updated THEN the system SHALL explain the difference between monthly precipitation parameters and constant temperature/radiation parameters
4. WHEN documentation is updated THEN the system SHALL explain how Fourier functions are used with latitude to simulate seasonal patterns
