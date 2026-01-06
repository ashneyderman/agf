# Chore: Update Branch Naming Pattern to Include worktree_id

## Metadata

agf_id: `agf-014`
prompt: `in `agf/workflow/task_handler.py` line 85 we are generating branch name. Change the pattern to {username}/{worktree_id}-{worktree_name} when worktree_id is not None`

## Chore Description

Update the `_get_branch_name()` method in `agf/workflow/task_handler.py` to generate branch names using the pattern `{username}/{worktree_id}-{worktree_name}` when `worktree_id` is not None. When `worktree_id` is None, the method should fall back to the current pattern `{username}/{worktree_name}`.

This change allows branch names to include the worktree identifier (e.g., JIRA ticket ID, GitHub issue number) extracted from the worktree header in markdown files, making it easier to correlate branches with their corresponding tickets/issues.

Examples:
- With worktree_id: `alex/SCHIP-7899-feature-auth`
- Without worktree_id: `alex/feature-auth`

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py:85` - Contains the `_get_branch_name()` method that needs to be updated to conditionally include `worktree_id` in the branch name pattern
- `agf/task_manager/models.py:43-61` - Contains the `Worktree` model definition showing the `worktree_id` field (line 49) which is optional and can be None
- `tests/agf/workflow/test_task_handler.py:99-106` - Contains the existing test `test_get_branch_name()` that validates branch name generation and needs to be updated to test both scenarios (with and without worktree_id)

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update _get_branch_name() Method

- Modify the `_get_branch_name()` method in `agf/workflow/task_handler.py` (lines 85-96)
- Add conditional logic to check if `worktree.worktree_id` is not None
- When `worktree_id` is not None, return `{username}/{worktree_id}-{worktree_name}`
- When `worktree_id` is None, return `{username}/{worktree_name}` (current behavior)
- Update the method's docstring to reflect the new conditional pattern

### 2. Update Unit Tests

- Update `test_get_branch_name()` in `tests/agf/workflow/test_task_handler.py` (lines 99-106)
- Rename existing test to `test_get_branch_name_without_worktree_id()` to be more specific
- Add new test `test_get_branch_name_with_worktree_id()` that:
  - Creates a `Worktree` object with `worktree_id="SCHIP-7899"` and `worktree_name="test-feature"`
  - Verifies the branch name is `alex/SCHIP-7899-test-feature`
- Ensure both tests use consistent username (e.g., "alex") via environment variable mocking

### 3. Validate Changes

- Run unit tests to ensure both scenarios work correctly
- Verify the method handles None worktree_id gracefully
- Verify the method generates correct branch names when worktree_id is provided

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerHelpers::test_get_branch_name_without_worktree_id -v` - Test branch name without worktree_id
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerHelpers::test_get_branch_name_with_worktree_id -v` - Test branch name with worktree_id
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles

## Notes

- This change is backward compatible - when `worktree_id` is None (default), the branch naming behavior remains unchanged
- The worktree_id field was added in agf-005 and is extracted from curly braces in markdown worktree headers (e.g., `## Git Worktree feature-auth {SCHIP-7899}`)
- The change only affects the branch name generation, not the worktree directory path or any other functionality
