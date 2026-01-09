# Chore: Use branch_prefix Setting in Task Handler

## Metadata

agf_id: `agf-023`
prompt: `use branch_prefix setting in agf/workflow/task_handler.py when creating or verifying branch creation. if setting is specified it overrides current {username} prefix.`

## Chore Description

Integrate the `branch_prefix` configuration setting into the `WorkflowTaskHandler` class so that when creating or verifying git branches, the configured prefix is used instead of the `USER` environment variable. If `branch_prefix` is set in the configuration, it should override the default username-based prefix.

## Status: ALREADY COMPLETED

This chore has already been implemented as part of commit `73384a6 feat: add customizable branch prefix configuration`.

The implementation in `agf/workflow/task_handler.py` at lines 87-108 already:
1. Uses `self.config.branch_prefix` when it is set
2. Falls back to `self._get_username()` (which uses `USER` env var) when `branch_prefix` is `None`

## Relevant Files

- `agf/workflow/task_handler.py:87-108` - `_get_branch_name()` method that already uses `branch_prefix`
- `agf/config/models.py:93` - `branch_prefix` field in `AGFConfig`
- `agf/config/models.py:168` - `branch_prefix` field in `CLIConfig`
- `agf/config/models.py:235` - `branch_prefix` field in `EffectiveConfig`
- `tests/agf/workflow/test_task_handler.py:121-165` - Tests for custom `branch_prefix` usage

## Implementation (Already Complete)

The `_get_branch_name()` method in `task_handler.py` implements the requested behavior:

```python
def _get_branch_name(self, worktree: Worktree) -> str:
    """Construct the branch name for the worktree.

    The prefix is determined by:
    - config.branch_prefix if set
    - USER environment variable if branch_prefix is None
    """
    prefix = self.config.branch_prefix if self.config.branch_prefix else self._get_username()
    if worktree.worktree_id is not None:
        return f"{prefix}/{worktree.worktree_id}-{worktree.worktree_name}"
    return f"{prefix}/{worktree.worktree_name}"
```

## Validation Commands

Execute these commands to verify the implementation:

- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerHelpers::test_get_branch_name_with_custom_prefix -v` - Test custom prefix
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerHelpers::test_get_branch_name_fallback_to_user -v` - Test fallback to USER
- `uv run pytest tests/ -v` - Run all tests

## Notes

This chore was already completed as part of the broader `branch_prefix` configuration feature. See `specs/agf-023-chore-branch-prefix-setting.md` for the full implementation details.
