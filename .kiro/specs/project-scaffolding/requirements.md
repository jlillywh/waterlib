# Requirements Document

## Introduction

This document specifies the requirements for a project scaffolding feature in waterlib. The feature will provide users with a programmatic way to create new waterlib projects with proper directory structure and starter files, eliminating manual setup and reducing errors.

## Glossary

- **Waterlib**: The water resource modeling Python library
- **Project**: A user's working directory containing models, data, and configuration files
- **Scaffold**: The process of automatically creating directory structure and starter files
- **Starter Files**: Template configuration files and examples provided in new projects
- **Project Root**: The top-level directory of a scaffolded project

## Requirements

### Requirement 1

**User Story:** As a waterlib user, I want to create a new project with proper directory structure programmatically, so that I can start modeling immediately without manual setup.

#### Acceptance Criteria

1. WHEN a user calls the create_project function with a project name, THE Waterlib SHALL create a new directory with that name
2. WHEN a user calls create_project with a project name that already exists, THE Waterlib SHALL raise an error and prevent overwriting
3. WHEN create_project executes successfully, THE Waterlib SHALL create subdirectories for models, data, outputs, and config
4. WHEN create_project executes successfully, THE Waterlib SHALL return the absolute path to the created project root
5. WHERE a user specifies a custom parent directory, THE Waterlib SHALL create the project in that location

### Requirement 2

**User Story:** As a waterlib user, I want starter files included in my new project, so that I have working examples to learn from and modify.

#### Acceptance Criteria

1. WHEN create_project executes, THE Waterlib SHALL generate a README.md file with project documentation
2. WHEN create_project executes, THE Waterlib SHALL generate a sample model configuration file
3. WHEN create_project executes, THE Waterlib SHALL generate a sample Python script demonstrating basic usage
4. WHEN create_project executes, THE Waterlib SHALL generate a default wgen_params.csv in the data directory
5. WHEN create_project executes, THE Waterlib SHALL generate example timeseries climate data files in the data directory
6. WHEN starter files are created, THE Waterlib SHALL use valid syntax and runnable code
7. WHERE a user opts out of starter files, THE Waterlib SHALL create only the directory structure

### Requirement 3

**User Story:** As a waterlib user, I want the scaffolding function accessible through Python API, so that I can integrate it into my workflows and scripts.

#### Acceptance Criteria

1. WHEN a user imports waterlib, THE Waterlib SHALL expose create_project at the top level
2. WHEN create_project is called, THE Waterlib SHALL accept a project name as a required string parameter
3. WHEN create_project is called, THE Waterlib SHALL accept an optional parent_dir parameter
4. WHEN create_project is called, THE Waterlib SHALL accept an optional include_examples boolean parameter
5. WHEN create_project completes, THE Waterlib SHALL log the created directory structure

### Requirement 4

**User Story:** As a waterlib user, I want clear error messages when scaffolding fails, so that I can understand and fix the problem.

#### Acceptance Criteria

1. WHEN a project name contains invalid filesystem characters, THE Waterlib SHALL raise a ValueError with a descriptive message
2. WHEN the parent directory does not exist, THE Waterlib SHALL raise a FileNotFoundError with the missing path
3. WHEN the user lacks write permissions, THE Waterlib SHALL raise a PermissionError with a clear explanation
4. WHEN any error occurs during scaffolding, THE Waterlib SHALL clean up partially created directories
5. WHEN an error is raised, THE Waterlib SHALL include the project name and attempted path in the error message

### Requirement 5

**User Story:** As a waterlib developer, I want the scaffolding code to be maintainable and testable, so that we can evolve the feature over time.

#### Acceptance Criteria

1. WHEN the scaffolding module is implemented, THE Waterlib SHALL separate directory creation from file generation logic
2. WHEN starter file templates are defined, THE Waterlib SHALL store them as string constants or separate template files
3. WHEN the module is structured, THE Waterlib SHALL place scaffolding code in waterlib.core.scaffold
4. WHEN functions are implemented, THE Waterlib SHALL include docstrings with parameter descriptions and examples
5. WHEN the API is designed, THE Waterlib SHALL follow existing waterlib naming conventions and patterns
