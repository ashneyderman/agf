# Chore: Add create-github-pr prompt wrapper function

## Metadata

agf_id: `agf-027`
prompt: `add prompt wrapper function that calls @agf_commands/create-github-pr.md similar to what was done to create other wrappers.`

## Chore Description

Add a `_create_github_pr` wrapper method to `WorkflowTaskHandler` that executes the `create-github-pr` prompt. This method will follow the existing pattern established by `_create_commit` and `_create_empty_commit` methods. The create-github-pr prompt requires one parameter (`agf_id`) and returns a string output (the result of `gh pr view` command), not JSON.

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler` class where the new `_create_github_pr` method needs to be added, following the pattern of `_create_commit` method (lines 352-374) and `_create_empty_commit` method (lines 376-398)
- `agf_commands/create-github-pr.md` - The prompt definition that specifies the expected parameter (`agf_id`) and output format (string from `gh pr view` command)
- `tests/agf/workflow/test_task_handler.py` - Contains tests for `_create_commit`, `_create_empty_commit`, and other prompt wrappers; new tests for `_create_github_pr` should follow the same pattern (see `TestWorkflowTaskHandlerPromptWrappers` class)

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `_create_github_pr` method to `WorkflowTaskHandler`

- In `agf/workflow/task_handler.py`, add a new method `_create_github_pr` after the existing `_create_empty_commit` method (after line 398)
- The method signature should be: `def _create_github_pr(self, worktree: Worktree, task: Task) -> str:`
- The method should:
  - Get the worktree path using `self._get_worktree_path(worktree)`
  - Create a `CommandTemplate` with:
    - `namespace=self.config.commands_namespace`
    - `prompt="create-github-pr"`
    - `params=[worktree.worktree_id or task.task_id]` (use worktree_id if available, otherwise fall back to task_id)
    - `model=ModelType.STANDARD`
    - `json_output=False` (the prompt returns string output from `gh pr view`)
  - Execute the command using `self._execute_command(worktree_path, command_template)`
  - Return `result.output.strip()` (the PR view result as a string)
- Add proper docstring following the pattern of `_create_commit` and `_run_implement`

### 2. Add unit tests for `_create_github_pr`

- In `tests/agf/workflow/test_task_handler.py`, add a new test method `test_create_github_pr_success` in the `TestWorkflowTaskHandlerPromptWrappers` class
- The test should:
  - Mock `AgentRunner.run_command` to return a successful result with string output containing PR view information
  - Call `handler._create_github_pr(sample_worktree, sample_task)`
  - Verify the result contains expected PR view output (stripped)
  - Verify `AgentRunner.run_command` was called with correct `CommandTemplate` parameters:
    - `prompt="create-github-pr"`
    - `params=["abc123"]` (task_id as fallback when worktree_id is None)
    - `model="standard"`
    - `json_output=False`

### 3. Add test for worktree_id usage

- Add a second test method `test_create_github_pr_uses_worktree_id` that:
  - Creates a worktree with `worktree_id="agf-027"`
  - Verifies that `params=["agf-027"]` is passed to the CommandTemplate (uses worktree_id when available)

### 4. Validate the implementation

- Run tests to ensure all tests pass including the new tests
- Run type checking to ensure no type errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers::test_create_github_pr_success -v` - Run the specific new test
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers::test_create_github_pr_uses_worktree_id -v` - Run the worktree_id test
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The `_create_github_pr` method returns a string (output of `gh pr view`), similar to `_run_implement`, not a dict like `_create_commit`
- The method uses `worktree.worktree_id or task.task_id` pattern consistent with other wrapper methods (`_run_plan`, `_run_chore`, `_run_feature`)
- The prompt handles the logic of checking if a PR already exists and either creating one or reporting that it exists
- This wrapper is not yet integrated into the main `handle_task` workflow - it's a utility method that can be called when needed
