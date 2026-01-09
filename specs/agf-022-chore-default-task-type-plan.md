# Chore: Default Task Type to Plan

## Metadata

agf_id: `agf-022`
prompt: `in agf/workflow/task_handler.py make task_type default to plan if no tags found task source. Make sure to add tests and verify that all existing tests are still passing.`

## Chore Description

Update the `WorkflowTaskHandler._get_task_type()` method in `agf/workflow/task_handler.py` to return `"plan"` as the default task type when no valid task type tags (`chore`, `feature`, `plan`) are found in the task's tags. This changes the current behavior from returning `None` (which causes task failure) to defaulting to `"plan"` for graceful handling of tasks without explicit type tags.

Additionally, update the `handle_task()` method to remove the error handling for missing task types since the default will now handle this case.

## Relevant Files

Use these files to complete the chore:

- `agf/workflow/task_handler.py` - Contains the `_get_task_type()` method (line 363-376) that needs to be modified to default to `"plan"` and the `handle_task()` method (line 378-468) where the error handling for missing task types should be removed
- `tests/agf/workflow/test_task_handler.py` - Contains comprehensive unit tests for `WorkflowTaskHandler` including tests for `_get_task_type()` (class `TestWorkflowTaskHandlerTaskType` lines 766-829) that need to be updated to reflect the new default behavior, and tests for `handle_task()` with missing task types (line 1052-1083) that need to be modified

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Modify _get_task_type() to Default to "plan"

- Update the `_get_task_type()` method in `agf/workflow/task_handler.py` (lines 363-376)
- Change the return statement from `return None` to `return "plan"` when no valid task type tag is found
- Update the method's docstring to document the new default behavior

### 2. Remove Task Type Error Handling from handle_task()

- Remove the error handling block in `handle_task()` method (lines 410-420) that checks for missing task types and fails the task
- Since `_get_task_type()` now always returns a valid task type, this error handling is no longer needed
- The task type detection should simply assign the result without validation

### 3. Update Unit Tests for _get_task_type()

- Modify `test_get_task_type_none()` in `tests/agf/workflow/test_task_handler.py` (lines 799-807)
- Change assertion from `assert handler._get_task_type(task) is None` to `assert handler._get_task_type(task) == "plan"`
- Update test name and docstring to reflect that it tests default behavior
- Modify `test_get_task_type_empty_tags()` (lines 809-817)
- Change assertion from `assert handler._get_task_type(task) is None` to `assert handler._get_task_type(task) == "plan"`
- Update test docstring to reflect default behavior

### 4. Update Integration Test for Missing Task Type

- Modify `test_handle_task_missing_task_type()` in `tests/agf/workflow/test_task_handler.py` (lines 1052-1083)
- Change test to verify successful execution with default "plan" task type instead of failure
- Mock the agent execution results for all three phases (plan, implement, commit)
- Update assertions to check for task completion (TaskStatus.COMPLETED) instead of failure
- Remove assertions checking for error recording
- Update test name and docstring to reflect that it tests default task type behavior

### 5. Run All Unit Tests

- Execute `uv run pytest tests/agf/workflow/test_task_handler.py -v` to run all workflow task handler tests
- Verify all tests pass including the modified tests
- Review any test failures and fix them before proceeding

### 6. Run Full Test Suite

- Execute `uv run pytest tests/ -v` to run the complete test suite
- Ensure no regressions were introduced in other modules
- Verify all tests across the entire codebase still pass

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerTaskType -v` - Verify task type detection tests pass with new default behavior
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerSDLCFlow::test_handle_task_missing_task_type -v` - Verify the updated integration test passes
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all workflow task handler tests
- `uv run pytest tests/ -v` - Run the complete test suite to ensure no regressions
- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify Python code compiles without syntax errors

## Notes

This change improves the robustness of the task handling system by providing a sensible default instead of failing when task type tags are missing. The `"plan"` task type is a reasonable default as it represents the planning phase which is appropriate for tasks that haven't been categorized yet.

The change maintains backward compatibility - tasks with explicit type tags will continue to work exactly as before. Only tasks without valid type tags will see different behavior (successful execution with plan workflow instead of immediate failure).
