# Requirements Document

## Introduction

This specification addresses the need to separate computational kernels (pure algorithms) from graph components (system nodes) in the waterlib architecture. Currently, algorithmic implementations like Snow17, AWBM, and Hargreaves are mixed with graph-level components in the `waterlib/components/` directory, creating architectural confusion and making it difficult to distinguish between "what can be connected in YAML" versus "what is a black-box calculation."

This refactor establishes a clear separation: kernels are pure computational functions that live in `waterlib/kernels/`, while components are graph nodes that orchestrate kernels and live in `waterlib/components/`.

## Glossary

- **Kernel**: A pure computational algorithm or function that performs a specific calculation (e.g., Snow17 snow accumulation, AWBM rainfall-runoff, Hargreaves ET calculation). Kernels have no knowledge of the graph structure.
- **Component**: A graph node that can be defined in YAML and connected to other components. Components may use kernels internally but handle I/O, state management, and graph integration.
- **Graph Node**: A component that appears in the YAML model definition and can be connected via the connections section.
- **Black Box**: A computational unit whose internal logic is hidden from the graph structure - users don't connect to its internals.
- **Hydrology Kernel**: Algorithms related to water movement through catchments (Snow17, AWBM, runoff generation).
- **Hydraulics Kernel**: Algorithms related to water movement through structures (weir equations, spillway calculations).
- **Climate Kernel**: Algorithms related to weather and evapotranspiration (Hargreaves-Samani, WGEN stochastic generation).
- **WGEN**: Weather generator for stochastic climate data generation.
- **Catchment Component**: A graph node that uses Snow17 and AWBM kernels internally but presents a unified interface.

## Requirements

### Requirement 1

**User Story:** As a developer, I want kernels separated from components, so that I can clearly distinguish between pure algorithms and graph nodes.

#### Acceptance Criteria

1. WHEN the codebase is examined THEN the system SHALL have a `waterlib/kernels/` directory containing pure computational algorithms
2. WHEN the codebase is examined THEN the system SHALL have a `waterlib/components/` directory containing only graph-connectable components
3. WHEN a kernel is examined THEN it SHALL have no dependencies on the graph structure or component system
4. WHEN a component is examined THEN it SHALL orchestrate one or more kernels but not implement core algorithms directly
5. WHEN the directory structure is reviewed THEN the separation SHALL be immediately obvious to new developers

### Requirement 2

**User Story:** As a developer, I want hydrology kernels organized together, so that I can find and maintain rainfall-runoff algorithms easily.

#### Acceptance Criteria

1. WHEN the kernels directory is examined THEN the system SHALL have a `waterlib/kernels/hydrology/` subdirectory
2. WHEN the hydrology directory is examined THEN it SHALL contain `snow17.py` with the Snow17 algorithm
3. WHEN the hydrology directory is examined THEN it SHALL contain `awbm.py` with the AWBM algorithm
4. WHEN the hydrology directory is examined THEN it SHALL contain `runoff.py` with runoff generation utilities
5. WHEN hydrology kernels are imported THEN they SHALL be importable from `waterlib.kernels.hydrology`

### Requirement 3

**User Story:** As a developer, I want hydraulics kernels organized together, so that I can find and maintain flow structure algorithms easily.

#### Acceptance Criteria

1. WHEN the kernels directory is examined THEN the system SHALL have a `waterlib/kernels/hydraulics/` subdirectory
2. WHEN the hydraulics directory is examined THEN it SHALL contain `weir.py` with weir flow equations
3. WHEN the hydraulics directory is examined THEN it SHALL contain spillway calculation functions
4. WHEN hydraulics kernels are imported THEN they SHALL be importable from `waterlib.kernels.hydraulics`

### Requirement 4

**User Story:** As a developer, I want climate kernels organized together, so that I can find and maintain ET and weather generation algorithms easily.

#### Acceptance Criteria

1. WHEN the kernels directory is examined THEN the system SHALL have a `waterlib/kernels/climate/` subdirectory
2. WHEN the climate directory is examined THEN it SHALL contain `et.py` with evapotranspiration calculation methods
3. WHEN the climate directory is examined THEN it SHALL contain `wgen.py` with the WGEN stochastic weather generator
4. WHEN climate kernels are imported THEN they SHALL be importable from `waterlib.kernels.climate`
5. WHEN the ET module is examined THEN it SHALL contain Hargreaves-Samani and be extensible for other methods

### Requirement 5

**User Story:** As a developer, I want components to import from kernels, so that the dependency direction is clear and maintainable.

#### Acceptance Criteria

1. WHEN a component imports a kernel THEN it SHALL use absolute imports from `waterlib.kernels`
2. WHEN a kernel is examined THEN it SHALL NOT import from `waterlib.components`
3. WHEN the import structure is analyzed THEN kernels SHALL have no circular dependencies with components
4. WHEN a component uses a kernel THEN the import SHALL be explicit and traceable
5. WHEN the codebase is refactored THEN all imports SHALL be updated to reflect the new structure

### Requirement 6

**User Story:** As a developer, I want existing tests to be updated, so that they reflect the new import structure without breaking.

#### Acceptance Criteria

1. WHEN tests import kernels THEN they SHALL use the new `waterlib.kernels` import paths
2. WHEN tests import components THEN they SHALL continue to use `waterlib.components` import paths
3. WHEN the test suite is run THEN all tests SHALL pass with the new structure
4. WHEN a test file is examined THEN imports SHALL be consistent with the new architecture
5. WHEN tests are updated THEN they SHALL be updated once and remain stable

### Requirement 7

**User Story:** As a developer, I want the Catchment component to remain a single graph node, so that users don't need to wire Snow17 and AWBM separately in YAML.

#### Acceptance Criteria

1. WHEN a YAML model is created THEN users SHALL define Catchment as a single component
2. WHEN Catchment is instantiated THEN it SHALL internally use Snow17 and AWBM kernels
3. WHEN Catchment is examined THEN it SHALL hide the internal kernel orchestration from users
4. WHEN Catchment is connected in YAML THEN it SHALL expose only high-level inputs and outputs
5. WHEN the architecture is reviewed THEN Catchment SHALL serve as the model for kernel-using components

### Requirement 8

**User Story:** As a developer, I want WGEN to have a proper home in the kernels structure, so that stochastic climate generation is architecturally consistent.

#### Acceptance Criteria

1. WHEN WGEN is implemented THEN it SHALL be placed in `waterlib/kernels/climate/wgen.py`
2. WHEN WGEN is examined THEN it SHALL be a pure computational kernel with no graph dependencies
3. WHEN WGEN is used THEN it SHALL be called by climate utility components or global utilities
4. WHEN the climate kernels directory is reviewed THEN WGEN SHALL sit alongside ET methods logically
5. WHEN future climate kernels are added THEN they SHALL follow the same organizational pattern

### Requirement 9

**User Story:** As a developer, I want the refactor to happen before fixing broken tests, so that I don't waste time fixing tests twice.

#### Acceptance Criteria

1. WHEN the refactor is planned THEN it SHALL be executed before test fixing work begins
2. WHEN files are moved THEN imports SHALL be updated immediately
3. WHEN the refactor is complete THEN tests SHALL be updated once to reflect the new structure
4. WHEN the refactor is complete THEN subsequent test fixes SHALL work with the stable structure
5. WHEN the timeline is reviewed THEN the refactor SHALL be recognized as a prerequisite for test stabilization

### Requirement 10

**User Story:** As a developer, I want clear __init__.py files in kernel directories, so that imports are clean and discoverable.

#### Acceptance Criteria

1. WHEN a kernel subdirectory is created THEN it SHALL include an `__init__.py` file
2. WHEN a kernel __init__.py is examined THEN it SHALL expose the main classes and functions from that subdirectory
3. WHEN a developer imports from kernels THEN they SHALL be able to use clean import syntax
4. WHEN the kernel API is reviewed THEN the __init__.py files SHALL serve as documentation of available kernels
5. WHEN new kernels are added THEN they SHALL be registered in the appropriate __init__.py file
