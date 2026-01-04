Create refersh from source capabilities for tasks manager.

## Implementation

in `ask_manager/manager.py` let's create `refresh_from_source` that will re-read all the worktrees from source and reconcile them with the current state of the worktrees and the tasks within them.

When reconciling we should keep in mind rules of equivalence between the worktrees and tasks. Two worktrees are equivalent if they have the same worktree_name. Two tasks are equivalent if they have the same task_name within the same worktree.

When task manager is instantiated it uses `_load_from_source` call. Make sure that the referesh and initialization logic are the same.

in `task_manager/manager.py` there is a method `def add_tasks` it is no longer needed. So let's remove it.

## Ntoes

Update all the existing tests and add new tests as needed.
