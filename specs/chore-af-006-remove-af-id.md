# Chore: Remove af_id Field from Worktree Model

## Metadata

af_id: `af-006`
prompt: `let's remove af_id on worktree models`

## Chore Description

Remove the `af_id` field from the `Worktree` model since we now have `worktree_id` field that serves the purpose of identifying worktrees. The `af_id` was previously used to store identifiers extracted from curly braces in worktree headers, but this functionality has been replaced by `worktree_id` in chore af-005.

This change requires:
1. Removing the `af_id` field from the `Worktree` model class
2. Removing the `af_id` parameter from `Worktree` object creation in `TaskManager`
3. Updating all tests that reference or assert on `af_id`
4. Ensuring no other code depends on the `af_id` field

## Relevant Files

Use these files to complete the chore:

- `task_manager/models.py` - Contains the `Worktree` model class where we need to remove the `af_id` field (line 46)
- `task_manager/manager.py` - Creates `Worktree` objects with `af_id` parameter that needs to be removed (line 74)
- `tests/task_manager/test_models.py` - Contains tests that reference `af_id` field (lines 73, 106-107)
- `tests/task_manager/test_manager.py` - Contains test that creates `Worktree` with `af_id` parameter (line 50)

### New Files

No new files need to be created for this chore.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Remove af_id Field from Worktree Model

- Remove the `af_id` field from the `Worktree` class in `task_manager/models.py` (line 46)
- Remove the import of `generate_short_id` if it's no longer used after this change (check if `Task` model still uses it)

### 2. Remove af_id from TaskManager

- Remove the `af_id=generate_short_id(6)` parameter from `Worktree` object creation in `task_manager/manager.py` (line 74)
- Ensure no other references to `af_id` exist in the manager

### 3. Update Unit Tests for Worktree Model

- Remove `af_id="WT0001"` parameter from `test_worktree_creation()` in `tests/task_manager/test_models.py` (line 68)
- Remove the assertion `assert worktree.af_id == "WT0001"` from the same test (line 73)
- Update `test_worktree_auto_generates_af_id()` test:
  - Rename the test to `test_worktree_defaults()` or similar
  - Remove assertions about `af_id` auto-generation (lines 106-107)
  - Keep the assertion that `worktree_id` defaults to `None` (line 108)

### 4. Update Manager Tests

- Remove `af_id="EXWT01"` parameter from `Worktree` creation in `tests/task_manager/test_manager.py` (line 50)
- Verify no other tests in this file reference `af_id`

### 5. Verify No Other References

- Search the entire codebase for any remaining references to `af_id` that would break
- Ensure markdown parser and other components don't depend on `af_id`
- Spec documents and agent commands may reference `af_id` but don't need updating as they're documentation

### 6. Validate All Changes

- Run all tests to ensure they pass
- Verify that the `Worktree` model works correctly without `af_id`
- Confirm no regressions in existing functionality
- Ensure code compiles without errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/task_manager/test_models.py -v` - Verify Worktree model tests pass
- `uv run pytest tests/task_manager/test_manager.py -v` - Verify manager tests pass
- `uv run pytest tests/task_manager/test_markdown_source.py -v` - Verify Markdown parser tests still pass
- `uv run pytest tests/task_manager/ -v` - Run all task_manager tests to ensure no regressions
- `uv run python -m py_compile task_manager/*.py` - Ensure all Python files compile without errors
- `grep -r "\.af_id" task_manager/ tests/task_manager/` - Verify no remaining references to af_id in code

## Notes

- The `generate_short_id` function should remain in `utils.py` as it's still used by the `Task` model for generating `task_id`
- The import of `generate_short_id` in `models.py` should remain as it's used by the `Task` model's default_factory
- Spec files and agent command files may still reference `af_id` in their documentation, but these are historical and don't need to be updated
- After this change, worktrees will only be identified by `worktree_name` and optionally `worktree_id` (from markdown headers)
