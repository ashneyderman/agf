# Chore: Remove Unused WorktreeInput Model

## Metadata

agf_id: `agf-009`
prompt: `looks like WorktreeInput is unused anymore. Please verify it is not needed and remove if so.`

## Chore Description

Verify that the `WorktreeInput` model is no longer used in the codebase and remove it if unused. This model was previously used by the now-removed `add_tasks()` method for parsing JSON task data. After the implementation of `refresh_from_source()` in af-008, the `add_tasks()` method was removed, potentially making `WorktreeInput` obsolete.

This cleanup will:
- Verify no production code uses `WorktreeInput`
- Remove the model definition if unused
- Remove or update related tests
- Remove from package exports
- Ensure all tests still pass

## Relevant Files

Use these files to complete the chore:

- `task_manager/models.py` - Contains the `WorktreeInput` class definition (lines 59-64)
- `task_manager/__init__.py` - Exports `WorktreeInput` in `__all__` list
- `tests/task_manager/test_models.py` - Contains one test for `WorktreeInput` parsing
- `specs/feature-af-008-tasks-manager-refresh.md` - Documentation mentioning potential removal
- `specs/plan-af-004-task-management.md` - Original plan that introduced `WorktreeInput`

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Verify WorktreeInput is Not Used in Production Code

- Search all Python files in `task_manager/`, `agentic_flow/`, and `apps/` directories for `WorktreeInput` usage
- Confirm it's only referenced in:
  - Model definition (`task_manager/models.py`)
  - Package exports (`task_manager/__init__.py`)
  - Test file (`tests/task_manager/test_models.py`)
  - Documentation/specs files
- Verify no imports or usage in any production code

### 2. Remove WorktreeInput from Models

- Remove the `WorktreeInput` class definition from `task_manager/models.py` (lines 59-64)
- This includes the class definition and its docstring

### 3. Remove WorktreeInput from Package Exports

- Remove `WorktreeInput` from the import statement in `task_manager/__init__.py` (line 3)
- Remove `'WorktreeInput'` from the `__all__` list in `task_manager/__init__.py` (line 12)

### 4. Remove or Update WorktreeInput Test

- Remove the `test_worktree_input_parsing` test from `tests/task_manager/test_models.py`
- Remove the `WorktreeInput` import from `tests/task_manager/test_models.py` (line 3)
- This test is no longer relevant since the model is being removed

### 5. Validate All Tests Pass

- Run all task_manager tests to ensure nothing broke
- Run Python syntax check on modified files
- Verify imports work correctly without `WorktreeInput`

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile task_manager/*.py` - Verify syntax of all task_manager modules
- `uv run pytest tests/task_manager/ -v` - Run all task_manager tests
- `uv run python -c "from task_manager import Task, Worktree, TaskStatus, TaskManager; print('Imports work')"` - Verify package imports
- `grep -r "WorktreeInput" task_manager/ --include="*.py" | grep -v "__pycache__"` - Verify WorktreeInput is completely removed from production code
- `grep -r "WorktreeInput" tests/task_manager/ --include="*.py" | grep -v "__pycache__"` - Verify WorktreeInput is removed from tests

## Notes

### Why WorktreeInput is No Longer Needed

The `WorktreeInput` model was designed to support the `add_tasks()` method, which:
- Accepted raw JSON-like data for adding tasks
- Required a separate input model for validation
- Was used for incremental task additions

After implementing `refresh_from_source()` (af-008):
- The `add_tasks()` method was removed entirely
- Task additions now happen via source refresh
- No JSON parsing input model is needed
- Tasks are loaded directly from `TaskSource.list_worktrees()` which returns `Worktree` objects

### Impact Assessment

Removing `WorktreeInput` has minimal impact:
- **Production code**: No usage found
- **Tests**: Only one test (`test_worktree_input_parsing`) uses it
- **Documentation**: Mentioned in specs as potentially removable
- **Public API**: Was exported but not used externally

This is safe to remove as it's truly unused after the af-008 changes.

### Alternative Approach

If there's any concern about removing it entirely, we could:
1. Keep the model but mark it as deprecated
2. Add a comment indicating it's maintained for backward compatibility

However, since there's no evidence of external usage and it was only introduced in af-004 (recently), clean removal is preferred.
