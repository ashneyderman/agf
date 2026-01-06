# Plan: Workflow Task Handler

## Metadata

agf_id: `agf-013`
prompt: `prompts/agf-workflow-task-handler.md`
task_type: feature
complexity: medium

## Task Description

Create a workflow task handler to provide a standardized way to process tasks within the workflow system. The handler will initialize git worktrees, execute agentic prompts, and manage task status transitions to ensure consistency, efficiency, and traceability across different workflows.

## Objective

Implement a reusable task handler that:
- Manages git worktree lifecycle (creation, validation, and initialization)
- Executes tasks using the AgentRunner with proper configuration
- Handles task status transitions (NOT_STARTED → IN_PROGRESS → SUCCESS/FAILURE)
- Provides error handling and logging for traceability
- Serves as the foundation for automated workflow execution

## Problem Statement

Currently, the Agentic Flow system has task management (TaskManager), agent execution (AgentRunner), and git worktree utilities (git_repo.py), but lacks a unified handler that orchestrates these components to execute tasks in isolated git worktrees. This creates several challenges:

1. No standardized way to prepare a worktree for task execution
2. No validation of worktree state before executing tasks (uncommitted changes)
3. No automatic task status tracking during execution
4. Manual integration required between TaskManager, AgentRunner, and git_repo utilities
5. Inconsistent error handling across different workflow implementations

## Solution Approach

Create a `WorkflowTaskHandler` class in the `agf/workflow` package that:

1. **Worktree Management**: Uses `git_repo.py` functions to create or validate worktrees with branch naming convention `{username}/{worktree_name}`
2. **State Validation**: Checks for uncommitted changes before task execution and fails fast if detected
3. **Status Tracking**: Updates task status through TaskManager at key execution points
4. **Agent Integration**: Constructs and executes agent prompts using AgentRunner with proper configuration
5. **Error Handling**: Catches exceptions and marks tasks as FAILED with error details
6. **Logging**: Provides detailed logging for troubleshooting and audit trails

The handler will be invoked by trigger scripts (like `process_tasks.py`) to execute individual tasks in a consistent manner.

## Relevant Files

Use these files to complete the task:

- `agf/git_repo.py` - Git worktree management functions (mk_worktree, rm_worktree) (lines 42-206)
- `agf/agent/runner.py` - AgentRunner for executing agents (lines 11-53)
- `agf/agent/base.py` - AgentConfig and AgentResult models (lines 150-194)
- `agf/task_manager/manager.py` - TaskManager for status updates (lines 95-143)
- `agf/task_manager/models.py` - Task, Worktree, and TaskStatus models (lines 1-61)
- `agf/config/models.py` - EffectiveConfig model (lines 174-229)
- `agf/triggers/process_tasks.py` - Reference for integration patterns (lines 99-138)

### New Files

- `agf/workflow/__init__.py` - Package initialization, exports WorkflowTaskHandler
- `agf/workflow/task_handler.py` - Core WorkflowTaskHandler implementation
- `tests/agf/workflow/test_task_handler.py` - Unit tests for task handler

## Implementation Phases

### Phase 1: Foundation

Create the `agf/workflow` package structure and define the `WorkflowTaskHandler` class interface with method signatures and docstrings.

### Phase 2: Core Implementation

Implement worktree initialization logic, task status updates, agent execution integration, and error handling with proper logging.

### Phase 3: Integration & Polish

Add comprehensive unit tests, update process_tasks.py to use the handler, and validate end-to-end workflow execution.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Package Structure

- Create directory `agf/workflow/` if it doesn't exist
- Create empty `agf/workflow/__init__.py` file (will populate later)
- Create empty `agf/workflow/task_handler.py` file

### 2. Define WorkflowTaskHandler Class Interface

- Import required modules in `task_handler.py`:
  - `import os` and `import os.path` for path operations
  - `from pathlib import Path` for path handling
  - `import subprocess` for git status checks
  - `from datetime import datetime` for logging timestamps
  - `from git import Repo` for git operations
  - Import from agf modules: `EffectiveConfig`, `TaskManager`, `Task`, `Worktree`, `TaskStatus`, `AgentRunner`, `AgentConfig`, `AgentResult`
  - Import `mk_worktree` from `agf.git_repo`
- Create `WorkflowTaskHandler` class with constructor taking `config: EffectiveConfig` and `task_manager: TaskManager`
- Add class docstring explaining purpose and usage
- Store config and task_manager as instance variables

### 3. Implement Logging Helper Method

- Add private method `_log(self, message: str) -> None`
- Format with timestamp: `[YYYY-MM-DD HH:MM:SS] {message}`
- Use `print()` for output (can be replaced with proper logging later)
- Add docstring explaining logging format

### 4. Implement Username Detection

- Add private method `_get_username(self) -> str`
- Use `os.getenv("USER")` to get current username
- Fallback to `"unknown"` if USER not set
- Add docstring explaining username detection for branch naming
- This will be used in branch naming: `{username}/{worktree_name}`

### 5. Implement Worktree Path Construction

- Add private method `_get_worktree_path(self, worktree: Worktree) -> str`
- Construct path as: `{config.project_dir}/{config.worktrees}/{worktree.worktree_name}`
- Use `os.path.join()` for path joining
- Return absolute path
- Add docstring explaining path construction logic

### 6. Implement Branch Name Construction

- Add private method `_get_branch_name(self, worktree: Worktree) -> str`
- Return `f"{self._get_username()}/{worktree.worktree_name}"`
- Add docstring explaining branch naming convention
- This follows the requirement: branch named `{whoami}/{worktree.worktree_name}`

### 7. Implement Uncommitted Changes Check

- Add private method `_has_uncommitted_changes(self, worktree_path: str) -> bool`
- Initialize `Repo(worktree_path)` to access git repository
- Check for uncommitted changes:
  - Use `repo.is_dirty()` to check for modified files
  - Use `repo.untracked_files` to check for untracked files
- Return `True` if either condition is met, `False` otherwise
- Add docstring explaining validation logic
- Add error handling for git command failures

### 8. Implement Branch Checkout Validation

- Add private method `_validate_branch_checkout(self, worktree_path: str, expected_branch: str) -> bool`
- Initialize `Repo(worktree_path)`
- Get current branch name using `repo.active_branch.name`
- Compare with expected_branch
- Return `True` if matches, `False` otherwise
- Add docstring explaining branch validation
- Add error handling for detached HEAD state

### 9. Implement Worktree Initialization Logic

- Add private method `_initialize_worktree(self, worktree: Worktree) -> str`
- Get worktree path using `_get_worktree_path()`
- Get branch name using `_get_branch_name()`
- Check if worktree directory exists:
  - **If NOT exists**:
    - Log "Creating worktree at {path} with branch {branch}"
    - Call `mk_worktree(project_dir=config.project_dir, target_dir=worktree_path, branch_name=branch_name)`
    - Log "Worktree created successfully"
  - **If exists**:
    - Log "Worktree directory exists, validating state"
    - Validate branch checkout using `_validate_branch_checkout()`
    - If wrong branch, raise `ValueError("Expected branch {expected} but found {actual}")`
    - Check for uncommitted changes using `_has_uncommitted_changes()`
    - If uncommitted changes found, raise `ValueError("Worktree has uncommitted changes")`
    - Log "Worktree validation passed"
- Return absolute worktree path
- Add comprehensive docstring with error conditions
- Wrap in try-except to catch and re-raise with context

### 10. Implement Agent Execution Logic

- Add private method `_execute_agent_task(self, task: Task, worktree_path: str) -> AgentResult`
- Construct prompt string: `f"/agf:test-prompt {task.task_id} {task.description}"`
- Get model from config: resolve model type to concrete model using `config.model_type` and `config.agents`
  - Access `config.agents[config.agent]` to get `AgentModelConfig`
  - Use model_type (thinking/standard/light) to get concrete model name
  - Example: `model = config.agents[config.agent].standard` if `config.model_type == "standard"`
- Create `AgentConfig(model=model, working_dir=worktree_path)`
- Log "Executing agent {agent} with model {model}"
- Call `AgentRunner.run(agent_name=config.agent, prompt=prompt, config=agent_config)`
- Log "Agent execution completed: success={result.success}, exit_code={result.exit_code}"
- Return `AgentResult`
- Add docstring explaining agent execution parameters

### 11. Implement Main Handler Method

- Add public method `handle_task(self, worktree: Worktree, task: Task) -> bool`
- Add docstring explaining complete workflow and return value (True for success, False for failure)
- Log "Starting task handler for task {task.task_id} in worktree {worktree.worktree_name}"
- Wrap entire logic in try-except block:
  - **Try block**:
    1. Call `_initialize_worktree(worktree)` to get worktree_path
    2. Update task status to IN_PROGRESS using `task_manager.update_task_status(worktree.worktree_name, task.task_id, TaskStatus.IN_PROGRESS)`
    3. Call `_execute_agent_task(task, worktree_path)` to get result
    4. If `result.success` is True:
       - Update status to COMPLETED with optional commit_sha from result
       - Log "Task {task.task_id} completed successfully"
       - Return True
    5. Else:
       - Update status to FAILED
       - Call `task_manager.mark_task_error(worktree.worktree_name, task.task_id, result.error or "Agent execution failed")`
       - Log "Task {task.task_id} failed: {error}"
       - Return False
  - **Except block**:
    1. Catch all exceptions as `e`
    2. Log "Error handling task {task.task_id}: {str(e)}"
    3. Update status to FAILED
    4. Call `task_manager.mark_task_error(worktree.worktree_name, task.task_id, str(e))`
    5. Return False

### 12. Update Package Exports

- Edit `agf/workflow/__init__.py`
- Add import: `from agf.workflow.task_handler import WorkflowTaskHandler`
- Add to `__all__`: `["WorkflowTaskHandler"]`
- Add module docstring explaining workflow package purpose

### 13. Create Test File Structure

- Create directory `tests/agf/workflow/` if it doesn't exist
- Create `tests/agf/workflow/__init__.py` as empty file
- Create `tests/agf/workflow/test_task_handler.py`

### 14. Write Unit Tests for Helper Methods

- Import required testing modules: `pytest`, `unittest.mock`, `tempfile`, `os`
- Import handler: `from agf.workflow import WorkflowTaskHandler`
- Import models for mocking
- Create `TestWorkflowTaskHandlerHelpers` test class
- Test `_get_username()`:
  - Mock `os.getenv` to return "testuser"
  - Assert username equals "testuser"
  - Test fallback when USER not set
- Test `_get_worktree_path()`:
  - Create mock config with known paths
  - Create mock worktree with name "test-worktree"
  - Assert path construction is correct
- Test `_get_branch_name()`:
  - Mock username as "alex"
  - Create worktree with name "feature-123"
  - Assert branch name is "alex/feature-123"

### 15. Write Unit Tests for Worktree Validation

- Create `TestWorkflowTaskHandlerWorktree` test class
- Test `_has_uncommitted_changes()`:
  - Use temporary git repository for testing
  - Test clean worktree returns False
  - Create uncommitted file and test returns True
  - Test with staged changes returns True
- Test `_validate_branch_checkout()`:
  - Create temp repo with specific branch
  - Test validation passes for correct branch
  - Checkout different branch and test validation fails

### 16. Write Integration Test for Handler

- Create `TestWorkflowTaskHandlerIntegration` test class
- Use pytest fixtures to create:
  - Temporary git repository with main branch
  - Mock EffectiveConfig with temp paths
  - Mock TaskManager with in-memory task source
  - Sample Worktree and Task objects
- Test `handle_task()` success path:
  - Mock AgentRunner.run to return successful AgentResult
  - Call handle_task and assert returns True
  - Verify task status updated to COMPLETED
  - Verify worktree created with correct branch
- Test `handle_task()` failure path:
  - Mock AgentRunner.run to return failed AgentResult
  - Call handle_task and assert returns False
  - Verify task status updated to FAILED
  - Verify error recorded

### 17. Write Test for Uncommitted Changes Validation

- Create test that:
  - Creates worktree with task handler
  - Manually adds uncommitted file to worktree
  - Attempts to handle another task in same worktree
  - Verifies handler raises ValueError
  - Verifies task marked as FAILED

### 18. Run Unit Tests

- Execute: `uv run pytest tests/agf/workflow/test_task_handler.py -v`
- Verify all tests pass
- Fix any failing tests
- Ensure test coverage for all public methods

### 19. Update process_tasks.py to Use Handler

- Import WorkflowTaskHandler in `agf/triggers/process_tasks.py`
- Modify `process_task()` function:
  - Create WorkflowTaskHandler instance with config and task_manager
  - Call `handler.handle_task(worktree, task)` instead of simulated sleep
  - Remove sleep simulation logic
  - Keep logging of task information
- Update function docstring to reflect real execution
- This integrates the handler into the existing trigger

### 20. Create Manual Test Script

- Create `examples/test_workflow_handler.py` for manual testing
- Script should:
  - Set up temporary git repository
  - Create sample tasks.md file with test tasks
  - Initialize EffectiveConfig with temp paths
  - Initialize TaskManager with markdown source
  - Create WorkflowTaskHandler instance
  - Fetch and handle one task
  - Print results and verify worktree created
- Add script docstring with usage instructions

### 21. Validate Worktree Creation

- Run manual test script
- Verify worktree directory created at correct path
- Verify branch name follows `{username}/{worktree_name}` convention
- Use `git worktree list` to confirm worktree registration
- Check worktree has files checked out correctly

### 22. Validate Agent Execution

- Run manual test with real AgentRunner
- Verify agent receives correct prompt format: `/agf:test-prompt {task_id} {description}`
- Verify agent runs in correct working directory (worktree path)
- Verify agent uses correct model from config
- Check agent output for errors

### 23. Validate Status Transitions

- Run manual test and observe logs
- Verify task status changes: NOT_STARTED → IN_PROGRESS → COMPLETED
- For failure case, create task that will fail and verify: NOT_STARTED → IN_PROGRESS → FAILED
- Verify status persisted to task source (markdown file)

### 24. Test Error Scenarios

- Test with invalid project directory (should fail gracefully)
- Test with git errors during worktree creation (should mark task FAILED)
- Test with agent execution timeout (should mark task FAILED)
- Test with already-existing worktree with wrong branch (should fail)
- Test with worktree containing uncommitted changes (should fail)
- Verify all errors are logged and task marked FAILED

## Testing Strategy

### Unit Tests

Focus on isolated testing of individual methods:
- Helper methods (_get_username, _get_worktree_path, _get_branch_name)
- Git validation methods (_has_uncommitted_changes, _validate_branch_checkout)
- Mock external dependencies (git operations, AgentRunner, TaskManager)

### Integration Tests

Test complete workflows with real dependencies:
- End-to-end task handling with temporary git repositories
- Status transitions through TaskManager
- Worktree lifecycle (creation, validation, reuse)

### Manual Tests

Validate behavior in realistic scenarios:
- Real agent execution with /agf:test-prompt skill
- Multiple tasks in same worktree (sequential execution)
- Error recovery and status tracking

### Edge Cases

- Empty worktree name
- Invalid characters in worktree name
- Concurrent access to same worktree (should detect uncommitted changes)
- Missing project directory
- Git repository not initialized
- Agent configuration errors

## Acceptance Criteria

- `WorkflowTaskHandler` class exists in `agf/workflow/task_handler.py`
- Handler accepts `EffectiveConfig` and `TaskManager` in constructor
- `handle_task()` method accepts `Worktree` and `Task` parameters
- Worktree created using `mk_worktree()` if directory doesn't exist
- Worktree validated for correct branch and clean state if directory exists
- Task status updated to IN_PROGRESS before agent execution
- Agent executed with correct prompt format: `/agf:test-prompt {task_id} {description}`
- Agent receives `AgentConfig` with correct model and working_dir
- Task status updated to COMPLETED on success with commit_sha if available
- Task status updated to FAILED on error with error message recorded
- Uncommitted changes in existing worktree cause task to fail
- Wrong branch in existing worktree causes task to fail
- All errors logged with timestamps
- Method returns True on success, False on failure
- Unit tests achieve >80% code coverage
- Integration tests validate end-to-end workflow
- Package exports `WorkflowTaskHandler` from `__init__.py`

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/*.py` - Verify Python files compile without syntax errors
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run unit tests with verbose output
- `uv run pytest tests/agf/workflow/test_task_handler.py --cov=agf.workflow --cov-report=term` - Check test coverage
- `uv run python -c "from agf.workflow import WorkflowTaskHandler; print('Import successful')"` - Verify package exports
- `uv run python examples/test_workflow_handler.py` - Run manual integration test
- `git worktree list` - Verify worktrees created correctly

## Notes

### Branch Naming Convention

The handler uses `{username}/{worktree_name}` for branch naming:
- `username` is obtained from `os.getenv("USER")` with fallback to "unknown"
- This matches the requirement from the prompt: `{whoami}/{worktree.worktree_name}`
- Example: user "alex" with worktree "feature-auth" → branch "alex/feature-auth"

### Worktree Path Construction

Worktrees are created at: `{project_dir}/{worktrees_dir}/{worktree_name}`
- `project_dir` comes from `EffectiveConfig.project_dir`
- `worktrees_dir` comes from `EffectiveConfig.worktrees` (typically ".worktrees")
- Example: `/home/alex/project/.worktrees/feature-auth`

### Model Resolution

The handler resolves the concrete model from configuration:
1. Get agent name from `config.agent` (e.g., "claude-code")
2. Get model type from `config.model_type` (e.g., "standard")
3. Lookup concrete model: `config.agents[agent].standard` (e.g., "sonnet")
4. Pass to AgentConfig for execution

### Error Handling Strategy

The handler follows a fail-fast approach:
- Validation errors (uncommitted changes, wrong branch) fail immediately
- All exceptions are caught, logged, and task marked FAILED
- Errors are recorded in task source for visibility
- Handler never raises exceptions to caller (returns False instead)

### Integration with process_tasks.py

After implementation, `process_tasks.py` will be updated to:
1. Import and instantiate `WorkflowTaskHandler`
2. Replace simulated sleep with `handler.handle_task(worktree, task)`
3. This provides real task execution instead of simulation
4. All task status tracking happens inside the handler

### Future Enhancements

After this feature is complete, consider:
- Support for cleanup of old worktrees (garbage collection)
- Configurable branch naming patterns
- Support for custom agent prompts (not hardcoded to /agf:test-prompt)
- Parallel execution of multiple tasks in different worktrees
- Worktree pooling/reuse optimization
- Integration with git hooks for validation
- Metrics collection (execution time, success rate)
