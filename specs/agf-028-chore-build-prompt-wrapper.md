# Chore: Add build prompt wrapper function

## Metadata

agf_id: `agf-028`
prompt: `add prompt wrapper function that calls @agf_commands/build.md similar to what was done for create commit wrapper.`

## Chore Description

Add a `_run_build` wrapper method to `WorkflowTaskHandler` that executes the `build` prompt. This method will be similar to existing wrapper methods like `_create_commit` and `_run_implement`. The build prompt takes two parameters: `adw_id` (worktree_id or task_id) and `task_description`, and returns a string summary of the implementation work (not JSON output).

The build command is designed for direct task implementation without creating a plan first, making it useful for simpler tasks that don't require the full planning phase.

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler` class where the new `_run_build` method needs to be added, following the pattern of existing wrapper methods like `_run_implement` (lines 327-350) and `_create_commit` (lines 352-374)
- `agf_commands/build.md` - The prompt definition that specifies the expected parameters (`adw_id`, `task_description`) and output format (string summary)
- `tests/agf/workflow/test_task_handler.py` - Contains tests for other prompt wrappers in `TestWorkflowTaskHandlerPromptWrappers` class; new tests for `_run_build` should follow the same pattern

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `_run_build` method to `WorkflowTaskHandler`

- In `agf/workflow/task_handler.py`, add a new method `_run_build` after the existing `_run_implement` method (around line 350)
- The method signature should be: `def _run_build(self, worktree: Worktree, task: Task) -> str:`
- The method should:
  - Get the worktree path using `self._get_worktree_path(worktree)`
  - Create a `CommandTemplate` with:
    - `namespace=self.config.commands_namespace`
    - `prompt="build"`
    - `params=[worktree.worktree_id or task.task_id, task.description]`
    - `model=ModelType.STANDARD`
    - `json_output=False`
  - Execute the command using `self._execute_command(worktree_path, command_template)`
  - Return `result.output.strip()`
- Add proper docstring following the pattern of `_run_implement`

### 2. Add unit tests for `_run_build`

- In `tests/agf/workflow/test_task_handler.py`, add a new test method `test_run_build_success` in the `TestWorkflowTaskHandlerPromptWrappers` class (after the `test_run_implement_success` test)
- The test should:
  - Mock `AgentRunner.run_command` to return a successful result with string output containing a summary
  - Call `handler._run_build(sample_worktree, sample_task)`
  - Verify the result contains the expected summary string (stripped)
  - Verify `AgentRunner.run_command` was called with correct `CommandTemplate` parameters:
    - `prompt="build"`
    - `params=["abc123", "Test task description"]` (falls back to task_id when worktree_id is None)
    - `model="standard"`
    - `json_output=False`

- Add a second test method `test_run_build_uses_worktree_id` to verify worktree_id is used when available:
  - Create a worktree with `worktree_id="agf-028"`
  - Verify the command template params use worktree_id: `params=["agf-028", "Test task description"]`

### 3. Validate the implementation

- Run tests to ensure all tests pass including the new tests
- Run type checking to ensure no type errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers::test_run_build_success -v` - Run the specific new test
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers -v` - Run all prompt wrapper tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The `_run_build` method is designed for direct task implementation without a planning phase
- The method follows the same parameter pattern as `_run_plan`, `_run_chore`, and `_run_feature` (using `worktree.worktree_id or task.task_id` for the first parameter)
- The output format matches `_run_implement` (string summary, not JSON)
- This wrapper is not yet integrated into the main `handle_task` workflow - it's a utility method that can be used for "build" type tasks in the future
- The model type is `STANDARD` (not `THINKING`) since build tasks are direct implementations without extensive planning
