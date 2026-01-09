# Chore: Add empty-commit prompt wrapper function

## Metadata

agf_id: `agf-025`
prompt: `add prompt wrapper function that calls @agf_commands/empty-commit.md similar to what was done for create commit wrapper.`

## Chore Description

Add a `_create_empty_commit` wrapper method to `WorkflowTaskHandler` that executes the `empty-commit` prompt. This method will be similar to the existing `_create_commit` method but will create empty commits for testing purposes. The empty-commit prompt requires two parameters: `agf_id` and `prompt`, and returns a JSON object with `commit_sha` and `commit_message`.

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler` class where the new `_create_empty_commit` method needs to be added, following the pattern of `_create_commit` method (lines 344-365)
- `agf_commands/empty-commit.md` - The prompt definition that specifies the expected parameters (`agf_id`, `prompt`) and output format (`commit_sha`, `commit_message`)
- `agf_commands/create-commit.md` - Reference for how the existing create-commit prompt is structured
- `tests/agf/workflow/test_task_handler.py` - Contains tests for `_create_commit` and other prompt wrappers; new tests for `_create_empty_commit` should follow the same pattern (see `TestWorkflowTaskHandlerPromptWrappers` class)

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `_create_empty_commit` method to `WorkflowTaskHandler`

- In `agf/workflow/task_handler.py`, add a new method `_create_empty_commit` after the existing `_create_commit` method (after line 365)
- The method signature should be: `def _create_empty_commit(self, worktree: Worktree, task: Task, agf_id: str, prompt: str) -> dict:`
- The method should:
  - Get the worktree path using `self._get_worktree_path(worktree)`
  - Create a `CommandTemplate` with:
    - `prompt="empty-commit"`
    - `params=[agf_id, prompt]`
    - `model=ModelType.STANDARD`
    - `json_output=True`
  - Execute the command using `self._execute_command(worktree_path, command_template)`
  - Return `result.json_output`
- Add proper docstring following the pattern of `_create_commit`

### 2. Add unit tests for `_create_empty_commit`

- In `tests/agf/workflow/test_task_handler.py`, add a new test method `test_create_empty_commit_success` in the `TestWorkflowTaskHandlerPromptWrappers` class
- The test should:
  - Mock `AgentRunner.run_command` to return a successful result with JSON output containing `commit_sha` and `commit_message`
  - Call `handler._create_empty_commit(sample_worktree, sample_task, "agf-025", "test prompt message")`
  - Verify the result contains expected `commit_sha` and `commit_message`
  - Verify `AgentRunner.run_command` was called with correct `CommandTemplate` parameters:
    - `prompt="empty-commit"`
    - `params=["agf-025", "test prompt message"]`
    - `model="standard"`
    - `json_output=True`

### 3. Validate the implementation

- Run tests to ensure all tests pass including the new test
- Run type checking to ensure no type errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers::test_create_empty_commit_success -v` - Run the specific new test
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The `_create_empty_commit` method is designed for testing purposes and creates commits without actual file changes
- The method requires explicit `agf_id` and `prompt` parameters unlike `_create_commit` which has no parameters
- The output format matches `_create_commit` (dict with `commit_sha` and `commit_message`)
- This wrapper is not yet integrated into the main `handle_task` workflow - it's a utility method for testing scenarios
