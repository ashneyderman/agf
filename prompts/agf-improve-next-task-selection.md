Improve next task selection. When task/s select return a list of tuples (Worktree, Task). Follow the following rules of selection.

1. Only a single task per worktree can be eligible for selection.
2. Task within a worktree is eligible if and only if all the tasks above it are successfully completed.

## Implementation

Current code resides in `agentic_flow/task_manager/manager.py` starting on line 164. Replace the existing code with the changes required.

## Examples

Given the following tasks description file:

```
## Git Worktree feature 0

[✅, ntjnwftq, 17d16d17] Task 1
[🟡, qbrlerfg] Task 2
[] Task 3

## Git Worktree feature 1

[✅, ntjnwftq, 17d16d17] Task 1
[] Task 2
[] Task 3

## Git Worktree feature 2

[✅, ntjnwftq, 17d16d17] Task 1
[❌, qbrlerfg] Task 2
[] Task 3
```

If task manager is asked to select next available tasks only ("Git Worktree feature 1", "Task 2") is eligible since all the tasks withing the worktree above it are successfully completed. In "Git Worktree feature 2", "Task 3" is not eligible since one task above it had failed. In "Git Worktree feature 0", "Task 3" is not eligible since at least one task above it is still in progress.

Make sure you review all the existing tests for modification.
