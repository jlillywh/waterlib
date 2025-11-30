# Requirements Document

## Introduction

The Gated Lifecycle Agent is a stateful CLI tool that enforces a disciplined "Waterfall-in-Miniature" development process for every feature in the waterlib project. The goal is to ensure documentation and tests never fall out of sync with code by requiring explicit human approval at each major stage before proceeding.

## Glossary

- **Lifecycle Agent**: The CLI tool that orchestrates the gated workflow
- **Stage**: A major phase in the development workflow (Requirements, Design, Tasks, Execution, Synchronization)
- **Gate**: A human approval checkpoint between stages that pauses execution until Y/N confirmation
- **Planning Directory**: The `planning/` folder where Requirements.md, Design.md, and Tasks.md are stored
- **Self-Healing Loop**: The execution pattern of Write Code → Run Tests → Fix Errors (max 3 iterations)
- **Synchronization**: The final stage that updates all documentation to match implemented code

## Requirements

### Requirement 1: Stage-Based Workflow Execution

**User Story:** As a developer, I want the agent to execute a structured 5-stage workflow, so that every feature follows a consistent development process.

#### Acceptance Criteria

1. WHEN the agent starts, THE Lifecycle Agent SHALL execute stages in the following order: Requirements Engineering, System Design, Task Decomposition, Execution, Synchronization
2. WHEN a stage completes, THE Lifecycle Agent SHALL pause execution and wait for human approval before proceeding to the next stage
3. WHEN a user rejects a stage output, THE Lifecycle Agent SHALL allow the user to request modifications and re-execute that stage
4. WHEN all stages complete successfully, THE Lifecycle Agent SHALL terminate with a success status
5. WHEN a stage fails after maximum retry attempts, THE Lifecycle Agent SHALL terminate with an error status and clear error message

### Requirement 2: Requirements Engineering Stage

**User Story:** As a developer, I want the agent to generate structured requirements from my high-level request, so that I have clear acceptance criteria before design begins.

#### Acceptance Criteria

1. WHEN the Requirements stage starts, THE Lifecycle Agent SHALL accept a user's high-level feature request as input
2. WHEN initializing the session, THE Lifecycle Agent SHALL load DEVELOPER_GUIDE.md and QA_INFRASTRUCTURE.md into the system prompt context to ensure adherence to project-specific coding standards
3. WHEN generating requirements, THE Lifecycle Agent SHALL read README.md and analyze the current code structure
4. WHEN requirements are generated, THE Lifecycle Agent SHALL create or update `planning/Requirements.md` with user stories and acceptance criteria
5. WHEN requirements are complete, THE Lifecycle Agent SHALL display the requirements to the user and prompt for approval (Y/N)
6. WHEN the user approves requirements, THE Lifecycle Agent SHALL proceed to the System Design stage

### Requirement 3: System Design Stage

**User Story:** As a developer, I want the agent to create a detailed design document based on approved requirements, so that I have a clear implementation plan.

#### Acceptance Criteria

1. WHEN the Design stage starts, THE Lifecycle Agent SHALL read the approved `planning/Requirements.md` file
2. WHEN generating design, THE Lifecycle Agent SHALL plan Python class structures, Pydantic configurations, and driver changes
3. WHEN design is generated, THE Lifecycle Agent SHALL create or update `planning/Design.md` with architecture and component specifications
4. WHEN design is complete, THE Lifecycle Agent SHALL display the design to the user and prompt for approval (Y/N)
5. WHEN the user approves design, THE Lifecycle Agent SHALL proceed to the Task Decomposition stage

### Requirement 4: Task Decomposition Stage

**User Story:** As a developer, I want the agent to break down the design into atomic implementation tasks, so that I can track progress and understand the work scope.

#### Acceptance Criteria

1. WHEN the Tasks stage starts, THE Lifecycle Agent SHALL read the approved `planning/Design.md` file
2. WHEN generating tasks, THE Lifecycle Agent SHALL decompose work into atomic steps with clear dependencies
3. WHEN tasks are generated, THE Lifecycle Agent SHALL create or update `planning/Tasks.md` with numbered task list
4. WHEN tasks are complete, THE Lifecycle Agent SHALL display the task list to the user and prompt for approval (Y/N)
5. WHEN the user approves tasks, THE Lifecycle Agent SHALL proceed to the Execution stage

### Requirement 5: Execution Stage with Self-Healing Loop

**User Story:** As a developer, I want the agent to implement tasks with automatic error correction, so that code is validated by tests before moving forward.

#### Acceptance Criteria

1. WHEN the Execution stage starts, THE Lifecycle Agent SHALL execute tasks sequentially from `planning/Tasks.md`
2. WHEN executing a task, THE Lifecycle Agent SHALL follow the pattern: Write Code → Run Architecture Lint → Run pytest → Analyze Results
3. WHEN executing the self-healing loop, THE Lifecycle Agent SHALL execute `python waterlib_lint.py` before running pytest
4. WHEN the linter fails, THE Lifecycle Agent SHALL treat the task as failed immediately and return the architectural error to the agent for fixing
5. WHEN linter passes but tests fail, THE Lifecycle Agent SHALL attempt to fix errors and re-run the full validation (lint + test) up to 3 times maximum
6. WHEN both linter and tests pass, THE Lifecycle Agent SHALL mark the task as complete and proceed to the next task
7. WHEN all tasks complete with passing linter and tests, THE Lifecycle Agent SHALL proceed to the Synchronization stage
8. WHEN the self-healing loop exceeds 3 attempts without success, THE Lifecycle Agent SHALL pause and request human intervention

### Requirement 6: Synchronization Stage

**User Story:** As a developer, I want the agent to automatically update all documentation after code changes, so that docs stay in sync with implementation.

#### Acceptance Criteria

1. WHEN the Synchronization stage starts, THE Lifecycle Agent SHALL scan all modified code files from the Execution stage
2. WHEN updating documentation, THE Lifecycle Agent SHALL distinguish between file types and apply type-specific updates
3. WHEN new Component parameters are detected, THE Lifecycle Agent SHALL update COMPONENTS.md table entries with parameter names, types, units, and descriptions
4. WHEN public method signatures change, THE Lifecycle Agent SHALL update docs/API_REFERENCE.md with new function signatures and parameter documentation
5. WHEN the feature is complete, THE Lifecycle Agent SHALL update CHANGELOG.md with a summary entry under the appropriate version section
6. WHEN high-level features change, THE Lifecycle Agent SHALL update README.md with new feature descriptions and usage examples
7. WHEN all documentation is synchronized, THE Lifecycle Agent SHALL display a summary of changes and mark the workflow as complete

### Requirement 7: State Persistence

**User Story:** As a developer, I want the agent to persist workflow state between runs, so that I can resume work if interrupted.

#### Acceptance Criteria

1. WHEN a stage completes, THE Lifecycle Agent SHALL save the current workflow state to a JSON file
2. WHEN the agent starts, THE Lifecycle Agent SHALL check for existing state and offer to resume from the last completed stage
3. WHEN state is corrupted or invalid, THE Lifecycle Agent SHALL display an error and offer to start fresh
4. WHEN workflow completes successfully, THE Lifecycle Agent SHALL archive the state file with a timestamp
5. WHEN the user requests a fresh start, THE Lifecycle Agent SHALL clear existing state and begin from Requirements stage

### Requirement 8: Human Approval Gates

**User Story:** As a developer, I want explicit control over workflow progression, so that I can review and approve each stage before proceeding.

#### Acceptance Criteria

1. WHEN a stage completes, THE Lifecycle Agent SHALL display the stage output and prompt "Approve and continue? (Y/N)"
2. WHEN the user enters 'Y' or 'yes', THE Lifecycle Agent SHALL proceed to the next stage
3. WHEN the user enters 'N' or 'no', THE Lifecycle Agent SHALL prompt for modification requests
4. WHEN modification requests are provided, THE Lifecycle Agent SHALL re-execute the current stage with the feedback
5. WHEN the user provides invalid input, THE Lifecycle Agent SHALL re-prompt with clear instructions

### Requirement 9: CLI Interface

**User Story:** As a developer, I want a simple command-line interface to start and control the workflow, so that I can integrate it into my development process.

#### Acceptance Criteria

1. WHEN invoked with `python tools/lifecycle_agent.py start "feature description"`, THE Lifecycle Agent SHALL begin a new workflow with the provided feature request
2. WHEN invoked with `python tools/lifecycle_agent.py resume`, THE Lifecycle Agent SHALL resume from the last saved state
3. WHEN invoked with `python tools/lifecycle_agent.py status`, THE Lifecycle Agent SHALL display the current workflow stage and progress
4. WHEN invoked with `python tools/lifecycle_agent.py reset`, THE Lifecycle Agent SHALL clear all state and planning files after confirmation
5. WHEN invoked with invalid arguments, THE Lifecycle Agent SHALL display usage help and exit with error code

### Requirement 10: Error Handling and Logging

**User Story:** As a developer, I want clear error messages and detailed logs, so that I can understand and debug workflow issues.

#### Acceptance Criteria

1. WHEN an error occurs, THE Lifecycle Agent SHALL display a clear error message with context and suggested actions
2. WHEN executing stages, THE Lifecycle Agent SHALL log all actions to `planning/workflow.log` with timestamps
3. WHEN tests fail during execution, THE Lifecycle Agent SHALL capture and display the pytest output
4. WHEN file operations fail, THE Lifecycle Agent SHALL display the file path and permission error details
5. WHEN the workflow completes, THE Lifecycle Agent SHALL display a summary of all stages with timing information
