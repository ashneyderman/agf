# Chore: Improve Next Task Selection

## Metadata

agf_id: `agf-007`
prompt: `prompts/af-improve-next-task-selection.md`

## Chore Description

Improve the task selection logic in the task manager to ensure that only one task per worktree is eligible for selection at a time, and that a task is only eligible if all tasks above it in the same worktree have been successfully completed.

The current implementation in `fetch_next_available_tasks()` allows multiple tasks per worktree to be selected and doesn't enforce the sequential completion requirement within each worktree. The new logic should:

1. Return a list of tuples `(Worktree, Task)` instead of just `Task` objects
2. Only allow a single task per worktree to be eligible for selection
3. Only select a task if all tasks above it (lower sequence numbers) in the same worktree have status `COMPLETED`
4. Skip worktrees where the next eligible task is blocked by failed or in-progress tasks

## Relevant Files

Use these files to complete the chore:

- `task_manager/manager.py:164` - Contains the `fetch_next_available_tasks()` method that needs to be modified
- `task_manager/models.py` - Defines `Task`, `Worktree`, and `TaskStatus` models needed for the implementation
- `tests/task_manager/test_manager.py:309` - Contains test class `TestTaskManagerFetchNextAvailable` with tests that need to be reviewed and updated
- `tests/task_manager/test_integration.py:84` - Contains `test_blocked_task_transitions()` which tests blocked task behavior and may need updates
- `tests/task_manager/test_integration.py:152` - Contains `test_multiple_worktrees_workflow()` which tests multi-worktree scenarios and may need updates

### New Files

No new files need to be created.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze Current Implementation

- Review the current `fetch_next_available_tasks()` method at `task_manager/manager.py:164`
- Review the helper method `_is_task_available()` at `task_manager/manager.py:225`
- Understand the current logic and identify what needs to change
- Review the examples in the prompt to understand the expected behavior

### 2. Update `fetch_next_available_tasks()` Method

- Change return type from `list[Task]` to `list[tuple[Worktree, Task]]`
- Modify logic to select only one task per worktree
- Implement rule: a task is eligible only if all tasks above it (lower sequence numbers) have status `COMPLETED`
- Ensure tasks with status `NOT_STARTED` are only selected if they are the first incomplete task in their worktree
- Handle the count parameter to limit total results across all worktrees

### 3. Update or Remove `_is_task_available()` Helper

- Evaluate whether `_is_task_available()` is still needed or if its logic should be integrated into `fetch_next_available_tasks()`
- If keeping it, update it to match the new selection rules
- If removing it, integrate its logic directly into the main method

### 4. Review and Update Unit Tests

- Review all tests in `tests/task_manager/test_manager.py:309` (class `TestTaskManagerFetchNextAvailable`)
- Update tests to expect `list[tuple[Worktree, Task]]` return type instead of `list[Task]`
- Add new tests for the "only one task per worktree" rule
- Add new tests for the "all tasks above must be completed" rule
- Update test assertions to unpack tuples where necessary
- Ensure tests cover edge cases from the prompt examples

### 5. Review and Update Integration Tests

- Review `tests/task_manager/test_integration.py:84` - `test_blocked_task_transitions()`
- Review `tests/task_manager/test_integration.py:152` - `test_multiple_worktrees_workflow()`
- Update these tests to work with the new return type `list[tuple[Worktree, Task]]`
- Verify they still test the correct behavior under the new rules
- Add integration tests for the specific examples in the prompt if not already covered

### 6. Add Test Cases for Prompt Examples

- Create test cases that match the three examples from the prompt:
  - "Git Worktree feature 0": Task 2 in progress, Task 3 not eligible
  - "Git Worktree feature 1": Task 1 completed, Task 2 eligible
  - "Git Worktree feature 2": Task 2 failed, Task 3 not eligible
- Ensure these tests pass with the new implementation

### 7. Run All Tests and Validate

- Run the full test suite to ensure no regressions
- Fix any failing tests
- Verify all new behavior works as expected

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/task_manager/test_manager.py::TestTaskManagerFetchNextAvailable -v` - Run unit tests for fetch_next_available_tasks
- `uv run pytest tests/task_manager/test_integration.py::TestEndToEndWorkflow::test_blocked_task_transitions -v` - Run integration test for blocked tasks
- `uv run pytest tests/task_manager/test_integration.py::TestEndToEndWorkflow::test_multiple_worktrees_workflow -v` - Run integration test for multiple worktrees
- `uv run pytest tests/task_manager/ -v` - Run all task manager tests
- `uv run pytest tests/ -v` - Run full test suite to ensure no regressions

## Notes

- The key change is ensuring that within each worktree, only the first incomplete task (where all preceding tasks are COMPLETED) is eligible
- Tasks with status IN_PROGRESS, BLOCKED, COMPLETED, or FAILED are never eligible
- If a worktree has a FAILED task, no tasks below it in that worktree are eligible
- If a worktree has an IN_PROGRESS task, no tasks below it in that worktree are eligible
- The method should return tuples of (Worktree, Task) so callers can see which worktree each task belongs to
- Consider whether BLOCKED status still makes sense with the new logic, or if it becomes redundant
