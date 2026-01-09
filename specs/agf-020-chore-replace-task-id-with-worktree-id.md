# Chore: Replace task_id with worktree_id in SDLC wrapper methods

## Metadata

agf_id: `agf-020`
prompt: `in `agf/workflow/task_handler.py` wrappers for plan, chore and feature specify replace first parameter passed to the command template to be worktree.worktree_id. Make sure all existing tests are still passing.`

## Chore Description

Update the three SDLC wrapper methods (`_run_plan`, `_run_chore`, and `_run_feature`) in `agf/workflow/task_handler.py` to use `worktree.worktree_id` as the first parameter passed to the command template instead of `task.task_id`. This change ensures that the agf_id used in these planning phases comes from the worktree configuration rather than individual task IDs.

The worktree_id should be used as-is if it exists, otherwise maintain the current behavior of using task.task_id as a fallback.

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py:247-314` - Contains the three wrapper methods that need to be updated:
  - `_run_plan` (lines 247-268) - Currently passes `task.task_id` as first param
  - `_run_chore` (lines 270-291) - Currently passes `task.task_id` as first param
  - `_run_feature` (lines 293-314) - Currently passes `task.task_id` as first param
- `tests/agf/workflow/test_task_handler.py:454-636` - Contains unit tests for the wrapper methods that verify the params passed to command templates
- `agf/task_manager/models.py:43-61` - Worktree model definition showing worktree_id is optional (str | None)

### New Files

No new files need to be created.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update _run_plan method

- Modify the `_run_plan` method at line 263 to use `worktree.worktree_id or task.task_id` as the first parameter
- Change from `params=[task.task_id, task.description]` to `params=[worktree.worktree_id or task.task_id, task.description]`

### 2. Update _run_chore method

- Modify the `_run_chore` method at line 286 to use `worktree.worktree_id or task.task_id` as the first parameter
- Change from `params=[task.task_id, task.description]` to `params=[worktree.worktree_id or task.task_id, task.description]`

### 3. Update _run_feature method

- Modify the `_run_feature` method at line 309 to use `worktree.worktree_id or task.task_id` as the first parameter
- Change from `params=[task.task_id, task.description]` to `params=[worktree.worktree_id or task.task_id, task.description]`

### 4. Update test expectations for worktree with worktree_id

- Update test `test_run_plan_success` to use a worktree with worktree_id set and verify it's passed instead of task_id
- Update test `test_run_chore_success` to use a worktree with worktree_id set and verify it's passed instead of task_id
- Update test `test_run_feature_success` to use a worktree with worktree_id set and verify it's passed instead of task_id

### 5. Add new test cases for fallback behavior

- Add test `test_run_plan_fallback_to_task_id` to verify that when worktree_id is None, task_id is used
- Add test `test_run_chore_fallback_to_task_id` to verify that when worktree_id is None, task_id is used
- Add test `test_run_feature_fallback_to_task_id` to verify that when worktree_id is None, task_id is used

### 6. Run all tests and validate

- Execute `uv run pytest tests/agf/workflow/test_task_handler.py -v` to ensure all existing tests pass
- Verify no regressions were introduced
- Check that both worktree_id and fallback scenarios work correctly

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers -v` - Test all wrapper methods including new test cases
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests to ensure no regressions
- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the modified file compiles without syntax errors

## Notes

- The worktree_id is optional (str | None), so we need to use the fallback pattern `worktree.worktree_id or task.task_id`
- This ensures backward compatibility for worktrees that don't have a worktree_id set
- The change affects only the planning phase wrappers, not the implementation or commit phases
- Tests already use worktrees without worktree_id (sample_worktree fixture), so we need to add test cases with worktree_id set explicitly
