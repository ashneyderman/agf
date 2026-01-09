# Chore: Add `--testing` CLI option to `agf` CLI

## Metadata

agf_id: `agf-025`
prompt: `add --testing option to agf CLI. If specified, run the agent in testing mode. Testing mode means we are not going to call plan/chore/feature and implement but will call only empty commit wrapper`

## Chore Description

Add a `--testing` CLI flag to the `agf` CLI (`process_tasks.py`). When this flag is specified, the `WorkflowTaskHandler` will skip the normal SDLC workflow (plan/chore/feature -> implement -> commit) and instead only call the `_create_empty_commit` wrapper method. This enables testing the infrastructure without running actual agent prompts.

The implementation requires:
1. Adding the `--testing` flag to the CLI options in `process_tasks.py`
2. Adding a `testing` field to `CLIConfig` and `EffectiveConfig` models
3. Modifying `WorkflowTaskHandler.handle_task()` to check for testing mode and call `_create_empty_commit` instead of the full SDLC flow
4. Adding tests for the new functionality

## Relevant Files

Use these files to complete the chore:

- `agf/triggers/process_tasks.py` - The CLI entry point where the `--testing` option needs to be added (around line 282-336 where other options are defined)
- `agf/config/models.py` - Contains `CLIConfig` and `EffectiveConfig` models that need the new `testing` field
- `agf/config/loader.py` - Contains `merge_configs` function that may need to handle the `testing` field
- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler.handle_task()` method that needs to check testing mode and call `_create_empty_commit` instead of the full SDLC flow
- `tests/agf/workflow/test_task_handler.py` - Contains tests for `WorkflowTaskHandler`; new tests for testing mode should be added

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `testing` field to `CLIConfig` in `agf/config/models.py`

- Add a new field `testing: bool = False` to the `CLIConfig` class (around line 168, after `branch_prefix`)
- Update the class docstring to document the new field

### 2. Add `testing` field to `EffectiveConfig` in `agf/config/models.py`

- Add a new field `testing: bool` to the `EffectiveConfig` class (around line 235, after `branch_prefix`)
- Update the class docstring to document the new field

### 3. Update `merge_configs` in `agf/config/loader.py` to handle `testing` field

- Read the file to understand the current `merge_configs` implementation
- Update the function to include `testing` field from `CLIConfig` in the `EffectiveConfig`

### 4. Add `--testing` CLI option to `process_tasks.py`

- Add a new `@click.option` decorator for `--testing` flag (after `--branch-prefix` option, around line 336):
  ```python
  @click.option(
      "--testing",
      is_flag=True,
      default=False,
      help="Run in testing mode (skip SDLC phases, only create empty commits)",
  )
  ```
- Add `testing: bool` parameter to the `main` function signature
- Pass `testing=testing` to `CLIConfig` constructor
- Add logging to show testing mode status

### 5. Modify `WorkflowTaskHandler.handle_task()` to support testing mode

- Add `testing` check at the beginning of the method (after worktree initialization and status update to IN_PROGRESS)
- If `self.config.testing` is True:
  - Get `agf_id` from `worktree.worktree_id or task.task_id`
  - Call `self._create_empty_commit(worktree, task, agf_id, task.description)`
  - Skip phases 1, 2, and 3 (planning, implementation, commit)
  - Update task status to COMPLETED with the commit SHA from `_create_empty_commit`
  - Return True
- If `self.config.testing` is False, continue with the existing SDLC flow

### 6. Add unit tests for testing mode

- In `tests/agf/workflow/test_task_handler.py`, add a new test class `TestWorkflowTaskHandlerTestingMode`
- Add test method `test_handle_task_testing_mode_success`:
  - Create config with `testing=True`
  - Mock `AgentRunner.run_command` to return successful result with JSON output containing `commit_sha` and `commit_message`
  - Call `handler.handle_task(worktree, task)`
  - Verify `AgentRunner.run_command` was called exactly once with `empty-commit` prompt
  - Verify task status was updated to COMPLETED with the commit SHA
- Add test method `test_handle_task_testing_mode_uses_worktree_id`:
  - Create worktree with `worktree_id`
  - Verify the `agf_id` passed to `_create_empty_commit` is the `worktree_id`
- Add test method `test_handle_task_testing_mode_fallback_to_task_id`:
  - Create worktree without `worktree_id`
  - Verify the `agf_id` passed to `_create_empty_commit` falls back to `task_id`

### 7. Update the `mock_config` fixture for testing mode support

- Update the `mock_config` fixture to include `testing=False` in the `EffectiveConfig`

### 8. Validate the implementation

- Run tests to ensure all tests pass including the new tests
- Run the code compilation check to ensure no syntax errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/config/models.py` - Verify config models compile
- `uv run python -m py_compile agf/config/loader.py` - Verify loader compiles
- `uv run python -m py_compile agf/triggers/process_tasks.py` - Verify CLI compiles
- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify task handler compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerTestingMode -v` - Run the specific new tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `uv run agf/triggers/process_tasks.py --help` - Verify the new `--testing` option appears in help

## Notes

- The `--testing` flag is designed to allow developers to test the full task processing pipeline without incurring agent costs
- In testing mode, the `_create_empty_commit` method still creates actual git commits, but they are empty commits with a test message
- The testing mode still requires a valid tasks file and project directory
- Testing mode respects all other CLI options (dry-run, single-run, etc.)
