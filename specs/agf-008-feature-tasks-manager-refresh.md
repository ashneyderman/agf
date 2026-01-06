# Feature: Task Manager Refresh from Source

## Metadata

agf_id: `agf-008`
prompt: `prompts/af-tasks-management-refresh.md`

## Feature Description

Add refresh capabilities to the TaskManager that re-read all worktrees and tasks from source and reconcile them with the current in-memory state. This feature ensures that the TaskManager can synchronize with external changes to task definitions without requiring a full restart, and removes the now-obsolete `add_tasks` method that was used for incremental task additions.

The refresh operation will:
- Re-read all worktrees from the task source
- Reconcile worktrees based on equivalence (same `worktree_name`)
- Reconcile tasks within worktrees based on equivalence (same `task_name` within the same worktree)
- Preserve task state (status, commit_sha) from the in-memory representation when reconciling
- Add new worktrees and tasks discovered in the source
- Remove worktrees and tasks that no longer exist in the source
- Ensure initialization and refresh use the same loading logic

## User Story

As a developer using the Agentic Flow system
I want to refresh task definitions from the source without restarting the application
So that I can update task lists, add new tasks, or modify existing task descriptions while preserving execution state

## Problem Statement

Currently, the TaskManager:
1. Only loads tasks from source during initialization via `_load_from_source()`
2. Has an `add_tasks()` method that incrementally adds tasks but doesn't handle updates or removals
3. Cannot detect changes made to the task source after initialization
4. Has no way to synchronize with external modifications to task definitions
5. Has duplicate logic between initialization (`_load_from_source`) and incremental addition (`add_tasks`)

This creates problems when:
- Task definitions in Markdown files are updated manually
- New tasks are added to existing worktrees outside the system
- Tasks are removed or reordered in the source
- Multiple processes or users modify the same task source

## Solution Statement

Implement a `refresh_from_source()` method that:
1. Re-reads all worktrees and tasks from the TaskSource
2. Reconciles the new data with existing in-memory state using equivalence rules:
   - Worktrees are equivalent if they have the same `worktree_name`
   - Tasks are equivalent if they have the same `description` (used as task_name) within the same worktree
3. For equivalent tasks, preserves in-memory state (status, commit_sha) while updating other attributes
4. Adds new worktrees/tasks discovered in source
5. Removes worktrees/tasks no longer present in source
6. Ensures `_load_from_source()` uses the same reconciliation logic for consistency

Additionally, remove the `add_tasks()` method as it is no longer needed with the refresh capability.

## Relevant Files

Use these files to implement the feature:

- `task_manager/manager.py` - Main implementation file where `refresh_from_source()` will be added and `add_tasks()` will be removed; also where `_load_from_source()` will be updated to use shared reconciliation logic
- `task_manager/models.py` - Review Task and Worktree models to understand equivalence criteria (worktree_name, description)
- `task_manager/source.py` - Review TaskSource protocol to understand `list_worktrees()` interface
- `task_manager/markdown_source.py` - Understand how tasks are loaded from Markdown source
- `tests/task_manager/test_manager.py` - Update existing tests that use `add_tasks()` and add new tests for `refresh_from_source()`

### New Files

- `tests/task_manager/test_refresh.py` - Dedicated test suite for refresh functionality with various reconciliation scenarios

## Implementation Plan

### Phase 1: Foundation

Design the reconciliation algorithm and identify shared logic between initialization and refresh. The core challenge is merging source data with in-memory state while preserving execution progress (task status, commit SHAs) but allowing task definitions to be updated.

### Phase 2: Core Implementation

Implement `refresh_from_source()` method with reconciliation logic, refactor `_load_from_source()` to use the same logic, and remove the obsolete `add_tasks()` method.

### Phase 3: Integration

Update all existing tests that depend on `add_tasks()` to use alternative approaches (either direct initialization or refresh), and create comprehensive tests for refresh scenarios including edge cases.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Design Reconciliation Algorithm

- Review current `_load_from_source()` implementation to understand initialization flow
- Review `add_tasks()` implementation to understand incremental addition logic
- Define equivalence criteria clearly:
  - Worktree equivalence: `worktree_name` match
  - Task equivalence: `description` match within same worktree (description is the stable identifier)
- Design reconciliation strategy:
  - For equivalent worktrees: update metadata, reconcile tasks
  - For new worktrees: add to `_worktrees` dict
  - For removed worktrees: remove from `_worktrees` dict
  - For equivalent tasks: preserve status and commit_sha, update other fields, preserve sequence_number from source
  - For new tasks: add to worktree.tasks
  - For removed tasks: remove from worktree.tasks

### 2. Implement Helper Method for Task Reconciliation

- Create `_reconcile_tasks()` helper method in `task_manager/manager.py`
- Parameters: `existing_tasks: list[Task]`, `source_tasks: list[Task]`
- Logic:
  - Create dict mapping description → existing Task
  - Iterate through source_tasks:
    - If description exists in existing: preserve status, commit_sha; update other fields from source
    - If description is new: add task as-is
  - Return reconciled task list preserving source order and sequence numbers

### 3. Implement Helper Method for Worktree Reconciliation

- Create `_reconcile_worktrees()` helper method in `task_manager/manager.py`
- Parameters: `existing_worktrees: dict[str, Worktree]`, `source_worktrees: list[Worktree]`
- Logic:
  - Create new dict for reconciled worktrees
  - Iterate through source_worktrees:
    - If worktree_name exists in existing: reconcile tasks using `_reconcile_tasks()`
    - If worktree_name is new: add worktree as-is
    - Update worktree metadata (worktree_id, directory_path, head_sha) from source
  - Return reconciled worktrees dict

### 4. Implement `refresh_from_source()` Method

- Add public method `refresh_from_source()` to TaskManager
- Load fresh data from source: `source_worktrees = self._task_source.list_worktrees()`
- Call `_reconcile_worktrees()` to merge with existing state
- Replace `self._worktrees` with reconciled result
- Write task_ids back to source for newly added tasks (same logic as in `_load_from_source`)
- Add docstring explaining the reconciliation process

### 5. Refactor `_load_from_source()` to Use Reconciliation Logic

- Update `_load_from_source()` to use `_reconcile_worktrees()`
- Pass empty dict as existing_worktrees (since it's initial load)
- Ensure behavior remains identical for initialization
- This ensures initialization and refresh use the same logic

### 6. Remove `add_tasks()` Method

- Delete the `add_tasks()` method from TaskManager class
- Remove `WorktreeInput` import from manager.py if no longer used
- Update `task_manager/__init__.py` to remove `WorktreeInput` export if no longer needed

### 7. Update Existing Tests in `test_manager.py`

- Identify all tests that use `add_tasks()`
- Refactor tests to either:
  - Use a mock TaskSource that returns data via `list_worktrees()` during initialization
  - Manually populate `_worktrees` dict in test setup (for unit tests)
  - Use `refresh_from_source()` if testing post-initialization updates
- Ensure all existing test scenarios still pass

### 8. Create Comprehensive Refresh Tests

- Create `tests/task_manager/test_refresh.py` with test cases:
  - `test_refresh_adds_new_worktree` - Source has new worktree
  - `test_refresh_removes_deleted_worktree` - Worktree removed from source
  - `test_refresh_adds_new_task_to_existing_worktree` - New task in existing worktree
  - `test_refresh_removes_deleted_task` - Task removed from source
  - `test_refresh_preserves_task_status` - Completed task status preserved after refresh
  - `test_refresh_preserves_commit_sha` - Commit SHA preserved for completed tasks
  - `test_refresh_updates_task_description_fields` - Non-status fields updated from source
  - `test_refresh_updates_worktree_metadata` - worktree_id, directory_path updated
  - `test_refresh_reorders_tasks` - Task order changed in source
  - `test_refresh_handles_empty_source` - Source becomes empty
  - `test_refresh_from_empty_to_populated` - Starting empty, source adds worktrees
  - `test_refresh_with_in_progress_task` - Task in IN_PROGRESS state preserved
  - `test_refresh_with_failed_task` - Task in FAILED state preserved
  - `test_refresh_writes_task_ids_for_new_tasks` - New tasks get IDs written to source

### 9. Create Integration Tests for Refresh

- Add integration tests in `tests/task_manager/test_integration.py`:
  - Test refresh with MarkdownTaskSource and temporary files
  - Modify Markdown file between initialization and refresh
  - Verify in-memory state reflects changes
  - Verify task IDs are preserved for existing tasks
  - Verify new tasks get new IDs

### 10. Test Edge Cases

- Add edge case tests:
  - Refresh when no changes in source (idempotent)
  - Refresh with only metadata changes (tags, worktree_id)
  - Refresh with all tasks removed from a worktree
  - Refresh with all worktrees removed
  - Multiple consecutive refreshes
  - Refresh after task status updates

### 11. Update Documentation

- Add docstring to `refresh_from_source()` explaining:
  - Purpose and use cases
  - Reconciliation rules (equivalence criteria)
  - What state is preserved vs updated
  - When to call this method
- Update class docstring for TaskManager to mention refresh capability
- Add code comments explaining reconciliation logic in helper methods

### 12. Validate Implementation

- Run all task_manager tests: `uv run pytest tests/task_manager/ -v`
- Run specific refresh tests: `uv run pytest tests/task_manager/test_refresh.py -v`
- Verify no tests depend on removed `add_tasks()` method
- Run syntax check: `uv run python -m py_compile task_manager/*.py`
- Verify imports still work after removing `WorktreeInput` if removed from exports

## Testing Strategy

### Unit Tests

- **Reconciliation Helpers**:
  - Test `_reconcile_tasks()` with various scenarios (new, removed, updated, reordered tasks)
  - Test `_reconcile_worktrees()` with various scenarios (new, removed, updated worktrees)
  - Test preservation of status, commit_sha for existing tasks
  - Test updating of other fields from source

- **Refresh Method**:
  - Test refresh adds new worktrees and tasks
  - Test refresh removes deleted worktrees and tasks
  - Test refresh preserves task execution state
  - Test refresh updates task definitions
  - Test refresh calls `update_task_id` for new tasks

- **Initialization**:
  - Ensure `_load_from_source()` still works correctly
  - Verify initialization and refresh use same reconciliation logic

### Integration Tests

- Test refresh with real MarkdownTaskSource
- Test modifying Markdown file and refreshing
- Test full lifecycle: init → work on tasks → refresh → continue work

### Edge Cases

- Empty source after refresh
- No changes in source (idempotent refresh)
- All tasks removed from worktree
- All worktrees removed
- Reordering tasks in source
- Changing task tags/metadata
- Concurrent status updates and refresh
- Multiple refreshes in sequence
- Refresh with all task statuses (NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, BLOCKED)

## Acceptance Criteria

- `refresh_from_source()` method exists and is public
- Refresh re-reads all worktrees from TaskSource
- Worktrees are reconciled by `worktree_name` equivalence
- Tasks are reconciled by `description` equivalence within same worktree
- Task status and commit_sha are preserved during refresh for equivalent tasks
- New worktrees discovered in source are added
- Removed worktrees are deleted from memory
- New tasks discovered in source are added
- Removed tasks are deleted from memory
- Task definitions (description, tags, sequence) are updated from source
- `_load_from_source()` uses same reconciliation logic as refresh
- `add_tasks()` method is completely removed
- No tests depend on removed `add_tasks()` method
- All existing tests pass
- New refresh tests cover all reconciliation scenarios
- Integration tests demonstrate refresh with MarkdownTaskSource
- Code is well-documented with clear docstrings and comments

## Validation Commands

Execute these commands to validate the feature is complete:

- `uv run python -m py_compile task_manager/*.py` - Verify syntax
- `uv run pytest tests/task_manager/test_manager.py -v` - Verify updated manager tests pass
- `uv run pytest tests/task_manager/test_refresh.py -v` - Verify new refresh tests pass
- `uv run pytest tests/task_manager/ -v` - Verify all task_manager tests pass
- `uv run python -c "from task_manager import TaskManager; import inspect; assert 'refresh_from_source' in dir(TaskManager); print('refresh_from_source method exists')"` - Verify method exists
- `uv run python -c "from task_manager import TaskManager; import inspect; assert 'add_tasks' not in dir(TaskManager); print('add_tasks method removed')"` - Verify add_tasks removed
- `uv run pytest tests/task_manager/test_integration.py -v` - Verify integration tests pass

## Notes

### Equivalence Rules

Two worktrees are equivalent if and only if:
```python
worktree1.worktree_name == worktree2.worktree_name
```

Two tasks are equivalent if and only if:
```python
task1.description == task2.description  # within the same worktree
```

Note: `task_id` is NOT used for equivalence because it's generated and may not exist in source initially. The `description` is the stable, human-defined identifier.

### State Preservation During Reconciliation

When reconciling an equivalent task, preserve from in-memory task:
- `status` - Current execution status (NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, BLOCKED)
- `commit_sha` - Git SHA recorded when task was completed
- `task_id` - Generated identifier (should already match)

Update from source task:
- `description` - Task description (used for equivalence, but may have formatting changes)
- `tags` - Tags may be updated in source
- `sequence_number` - Task order may change in source
- Note: All other Worktree fields (worktree_id, directory_path, head_sha) updated from source

### Why Remove `add_tasks()`?

The `add_tasks()` method has several limitations:
1. Only handles additions, not updates or removals
2. Uses different logic than `_load_from_source()`, creating inconsistency
3. Requires `WorktreeInput` model, adding complexity
4. Doesn't handle reconciliation of existing tasks
5. With `refresh_from_source()` available, it's redundant

The refresh approach is superior because:
- Single source of truth (always the TaskSource)
- Handles additions, updates, and removals
- Consistent logic for initialization and updates
- Simpler API (no separate input model needed)

### Implementation Considerations

- The reconciliation must be atomic (replace `_worktrees` dict in one operation)
- Preserve object references where possible to maintain consistency
- Consider thread safety if TaskManager is used in multi-threaded context
- The `update_task_id` calls should only be made for truly new tasks (not existing tasks being reconciled)
- Ensure sequence_number is taken from source (it defines task order)

### Future Enhancements

After this feature is complete, consider:
- Add a return value from `refresh_from_source()` indicating what changed (added/removed/updated counts)
- Add event callbacks for task/worktree additions/removals
- Add option to refresh only specific worktrees
- Add conflict resolution strategy for concurrent modifications
- Add automatic refresh on file change detection (file watching)
