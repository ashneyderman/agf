# Plan: Auto-create GitHub PR when worktree tasks complete

## Metadata

agf_id: `agf-027`
prompt: `when all tasks in the worktree are completed and --testing parameter is off call create github pr wrapper to create the PR.`
task_type: enhancement
complexity: simple

## Task Description

After all tasks in a worktree are completed successfully, automatically create a GitHub pull request by calling the `_create_github_pr` wrapper method. This should only occur when the `--testing` CLI parameter is off (i.e., `self.config.testing` is `False`). The feature integrates the existing `_create_github_pr` wrapper into the workflow completion flow.

## Objective

When the final task in a worktree is marked as COMPLETED and testing mode is disabled, automatically invoke the create-github-pr prompt to create a pull request for the worktree's branch.

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler.handle_task()` where the PR creation logic needs to be added after task completion (after line 537), and the `_create_github_pr` method (lines 400-422) that will be called
- `agf/task_manager/models.py` - Contains `TaskStatus` enum and `Worktree`/`Task` models used to check task completion status
- `tests/agf/workflow/test_task_handler.py` - Contains tests for `WorkflowTaskHandler`; new tests should be added to verify auto-PR creation behavior

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add helper method to check if all worktree tasks are completed

- In `agf/workflow/task_handler.py`, add a new method `_all_worktree_tasks_completed(self, worktree_name: str) -> bool` before the `handle_task` method
- The method should:
  - Get the fresh worktree from task_manager using `self.task_manager.get_worktree(worktree_name)`
  - Return `False` if worktree is None or has no tasks
  - Check if ALL tasks in the worktree have `status == TaskStatus.COMPLETED`
  - Return `True` only if all tasks are completed

### 2. Add PR creation phase to handle_task after successful completion

- In the `handle_task` method, after the task status is updated to COMPLETED (after line 536), add a new phase:
- Check two conditions:
  1. `not self.config.testing` (testing mode is off)
  2. `self._all_worktree_tasks_completed(worktree.worktree_name)` (all tasks done)
- If both conditions are true:
  - Log "All worktree tasks completed - creating GitHub PR"
  - Call `self._create_github_pr(worktree, task)`
  - Log the PR result
- Wrap the PR creation in a try/except to log errors but not fail the task (task is already completed)

### 3. Add unit tests for the helper method

- In `tests/agf/workflow/test_task_handler.py`, add a new test class `TestWorkflowTaskHandlerPRCreation`
- Add test `test_all_worktree_tasks_completed_true` - all tasks have COMPLETED status
- Add test `test_all_worktree_tasks_completed_false_mixed_status` - some tasks not completed
- Add test `test_all_worktree_tasks_completed_empty_worktree` - worktree with no tasks returns False
- Add test `test_all_worktree_tasks_completed_worktree_not_found` - worktree doesn't exist returns False

### 4. Add integration tests for auto-PR creation

- Add test `test_handle_task_creates_pr_when_all_tasks_completed` that:
  - Sets up mock with testing=False
  - Mocks task_manager.get_worktree to return worktree where all tasks are COMPLETED
  - Verifies `_create_github_pr` is called after task completion
- Add test `test_handle_task_skips_pr_in_testing_mode` that:
  - Sets up mock with testing=True
  - Verifies `_create_github_pr` is NOT called even if all tasks completed
- Add test `test_handle_task_skips_pr_when_tasks_remaining` that:
  - Sets up mock with testing=False
  - Mocks task_manager.get_worktree to return worktree with some NOT_STARTED tasks
  - Verifies `_create_github_pr` is NOT called

### 5. Validate the implementation

- Run all tests to ensure no regressions
- Run type checking to verify no type errors

## Acceptance Criteria

- When all tasks in a worktree are COMPLETED and testing=False, `_create_github_pr` is automatically called
- When testing=True, PR creation is skipped regardless of task completion status
- When some tasks in the worktree are not COMPLETED, PR creation is skipped
- PR creation failures are logged but do not cause the task to fail (task already succeeded)
- All existing tests continue to pass
- New tests cover the auto-PR creation scenarios

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPRCreation -v` - Run the new PR creation tests
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The `_create_github_pr` method already exists and is tested (lines 400-422 in task_handler.py)
- The PR creation is a "fire and forget" operation - errors are logged but don't affect task success
- The task_manager must be queried for the fresh worktree state since task status was just updated
- This enhancement only applies to the full SDLC flow path (not testing mode path)
