# Chore: Add worktree_id Field to Worktree Model

## Metadata

agf_id: `agf-005`
prompt: `prompts/af-worktree-id.md`

## Chore Description

Add support for extracting and storing `worktree_id` from worktree header lines in Markdown files. The `worktree_id` will be parsed from curly braces `{}` in the worktree header line (e.g., `## Git Worktree feature-auth {SCHIP-7899}` where `worktree_id="SCHIP-7899"`). When no worktree_id is provided, the default value will be `None`.

This change requires:
1. Adding a `worktree_id` field to the `Worktree` model
2. Updating the Markdown parser to extract `worktree_id` from headers (currently it extracts `agf_id`)
3. Updating all existing tests that create or validate `Worktree` objects

## Relevant Files

Use these files to complete the chore:

- `task_manager/models.py` - Contains the `Worktree` model class where we need to add the `worktree_id` field
- `task_manager/markdown_source.py` - Contains the `MarkdownTaskSource` class that parses worktree headers and needs to extract `worktree_id` instead of `agf_id` from curly braces
- `tests/task_manager/test_models.py` - Contains tests for the `Worktree` model that need to be updated to include `worktree_id` in test cases
- `tests/task_manager/test_markdown_source.py` - Contains tests for parsing worktree headers that need validation for `worktree_id` extraction
- `tests/task_manager/test_manager.py` - May contain integration tests that create `Worktree` objects
- `tests/task_manager/test_integration.py` - May contain integration tests that validate `Worktree` objects

### New Files

No new files need to be created for this chore.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Worktree Model

- Add `worktree_id: str | None = None` field to the `Worktree` class in `task_manager/models.py`
- Position the field appropriately in the model (suggest after `worktree_name` and before `agf_id`)
- Ensure the field defaults to `None` when not provided

### 2. Update Markdown Parser

- Modify `_parse_worktree_header()` method in `task_manager/markdown_source.py`
- Change the regex extraction logic to extract the value in curly braces as `worktree_id` instead of `agf_id`
- Update the return type from `tuple[str, str | None]` to `tuple[str, str | None]` (remains the same, but now returns `worktree_id`)
- Update the `list_worktrees()` method to assign the extracted value to `worktree_id` instead of `agf_id`
- Update docstrings and comments to reflect that curly braces now contain `worktree_id`

### 3. Update Unit Tests for Worktree Model

- Update `test_worktree_creation()` in `tests/task_manager/test_models.py` to include `worktree_id` parameter
- Update `test_worktree_with_tasks()` to include `worktree_id` if needed
- Update `test_worktree_auto_generates_agf_id()` to verify `worktree_id` defaults to `None` when not provided
- Add new test case to verify `worktree_id` can be set and retrieved correctly

### 4. Update Markdown Parser Tests

- Update `test_list_worktrees_parses_multiple_worktrees()` in `tests/task_manager/test_markdown_source.py`
- Change assertions from checking `agf_id` values (e.g., `"af_wt_001"`) to checking `worktree_id` values
- Update `test_parses_worktree_without_agf_id()` test name and assertions to reflect `worktree_id` instead of `agf_id`
- Update `test_parse_worktree_header_with_agf_id()` test name to `test_parse_worktree_header_with_worktree_id()`
- Update `test_parse_worktree_header_without_agf_id()` test name to `test_parse_worktree_header_without_worktree_id()`
- Update assertions to verify `worktree_id` instead of `agf_id`

### 5. Update Test Fixtures

- Review and update `tests/task_manager/fixtures/example_tasks.md` if it contains worktree headers with values in curly braces
- Review and update `tests/task_manager/fixtures/single_worktree.md` to ensure consistency
- Update any other fixture files that may contain worktree definitions
- Ensure fixture files reflect that values in `{}` are now `worktree_id`

### 6. Update Integration and Manager Tests

- Search for any `Worktree` object creation in `tests/task_manager/test_manager.py`
- Search for any `Worktree` object creation in `tests/task_manager/test_integration.py`
- Update any test cases that validate `agf_id` from parsed headers to validate `worktree_id` instead
- Ensure all tests create `Worktree` objects with appropriate `worktree_id` values

### 7. Validate All Changes

- Run all tests to ensure they pass
- Verify that the parsing logic correctly extracts `worktree_id` from curly braces
- Verify that `worktree_id` defaults to `None` when not provided
- Confirm no regressions in existing functionality

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/task_manager/test_models.py -v` - Verify Worktree model tests pass
- `uv run pytest tests/task_manager/test_markdown_source.py -v` - Verify Markdown parser tests pass
- `uv run pytest tests/task_manager/test_manager.py -v` - Verify manager tests pass
- `uv run pytest tests/task_manager/test_integration.py -v` - Verify integration tests pass
- `uv run pytest tests/task_manager/ -v` - Run all task_manager tests to ensure no regressions
- `uv run python -m py_compile task_manager/*.py` - Ensure all Python files compile without errors

## Notes

- The key difference is that previously `agf_id` was extracted from curly braces in the worktree header
- Now `worktree_id` should be extracted from curly braces instead
- The `agf_id` field in the `Worktree` model should remain, but will auto-generate a value when not explicitly provided
- This change maintains backward compatibility as both fields support `None` as a default value
- Pay special attention to test fixture files that demonstrate the expected format
