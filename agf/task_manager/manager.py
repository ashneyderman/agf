from .models import Task, TaskStatus, Worktree
from .source import TaskSource


class TaskManager:
    """
    Singleton manager for task state and deduplication.

    Manages worktrees and tasks in memory, coordinating with TaskSource
    for persistence. Supports refreshing from source to reconcile external
    changes while preserving task execution state.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern - ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, task_source: TaskSource):
        """
        Initialize TaskManager with a task source.

        Args:
            task_source: TaskSource implementation for persistence

        Note: Only initializes once (singleton pattern)
        """
        if self._initialized:
            return

        self._task_source = task_source
        self._worktrees: dict[str, Worktree] = {}
        self._initialized = True

        # Load existing worktrees from source
        self._load_from_source()

    def _load_from_source(self) -> None:
        """Load existing worktrees and tasks from the task source"""
        source_worktrees = self._task_source.list_worktrees()

        # Use reconciliation logic with empty existing worktrees (initial load)
        self._worktrees = self._reconcile_worktrees({}, source_worktrees)

        # Write task_ids back to source for all tasks
        # (in case they were generated during parsing)
        for worktree in self._worktrees.values():
            for task in worktree.tasks:
                self._task_source.update_task_id(
                    worktree.worktree_name, task.sequence_number, task.task_id
                )

    def refresh_from_source(self) -> None:
        """
        Refresh worktrees and tasks from source, reconciling with in-memory state.

        This method re-reads all worktrees and tasks from the TaskSource and
        reconciles them with the current in-memory state using equivalence rules:

        Equivalence Rules:
        - Worktrees are equivalent if they have the same worktree_name
        - Tasks are equivalent if they have the same description within the same worktree

        State Reconciliation:
        - For equivalent tasks: preserves task_id from in-memory
        - For equivalent tasks: updates description, tags, sequence_number, status,
          and commit_sha from source (source is primary)
        - For equivalent worktrees: updates worktree_id, agent, directory_path, and head_sha from source

        Additions and Removals:
        - New worktrees/tasks from source are added
        - Worktrees/tasks no longer in source are removed

        This allows external modifications to task definitions and status to be
        synchronized with in-memory state, with the source as the authoritative source.
        """
        source_worktrees = self._task_source.list_worktrees()

        # Reconcile with existing state
        self._worktrees = self._reconcile_worktrees(self._worktrees, source_worktrees)

        # Write task_ids back to source for newly added tasks
        for worktree in self._worktrees.values():
            for task in worktree.tasks:
                # Only update if task_id was just generated (not reconciled)
                # We write all IDs to be safe, the source should be idempotent
                self._task_source.update_task_id(
                    worktree.worktree_name, task.sequence_number, task.task_id
                )

    def update_task_status(
        self,
        worktree_name: str,
        task_id: str,
        status: TaskStatus,
        commit_sha: str | None = None,
    ) -> None:
        """
        Update task status in memory and at source.

        Args:
            worktree_name: Name of the worktree
            task_id: ID of the task to update
            status: New status
            commit_sha: Optional commit SHA to record
        """
        # Find and update task in internal state
        worktree = self._worktrees.get(worktree_name)
        if not worktree:
            raise ValueError(f"Worktree '{worktree_name}' not found")

        task = self._find_task_by_id(worktree, task_id)
        if not task:
            raise ValueError(
                f"Task '{task_id}' not found in worktree '{worktree_name}'"
            )

        # Update internal state
        task.status = status
        if commit_sha:
            task.commit_sha = commit_sha

        # Update source
        self._task_source.update_task_status(worktree_name, task_id, status, commit_sha)

    def mark_task_error(self, worktree_name: str, task_id: str, error_msg: str) -> None:
        """
        Mark a task as failed with an error message.

        Args:
            worktree_name: Name of the worktree
            task_id: ID of the task
            error_msg: Error message to record
        """
        # Update status to FAILED
        self.update_task_status(worktree_name, task_id, TaskStatus.FAILED)

        # Call source-specific error marking
        self._task_source.mark_task_error(worktree_name, task_id, error_msg)

    def fetch_next_available_tasks(self, count: int = 1) -> list[tuple[Worktree, Task]]:
        """
        Fetch next available tasks for execution.

        Returns at most one task per worktree. A task is eligible if and only if:
        - All tasks above it (lower sequence numbers) have status COMPLETED
        - Its own status is NOT_STARTED

        Args:
            count: Maximum number of tasks to return

        Returns:
            List of tuples (Worktree, Task) for available tasks (up to count)
        """
        available_tasks = []

        for worktree in self._worktrees.values():
            if len(available_tasks) >= count:
                break

            # Find the first eligible task in this worktree
            eligible_task = self._find_next_eligible_task(worktree)
            if eligible_task:
                available_tasks.append((worktree, eligible_task))

        return available_tasks

    def get_worktree(self, name: str) -> Worktree | None:
        """
        Retrieve a worktree by name.

        Args:
            name: Name of the worktree

        Returns:
            Worktree object or None if not found
        """
        return self._worktrees.get(name)

    def list_worktrees(self) -> list[Worktree]:
        """
        Get all worktrees.

        Returns:
            List of all Worktree objects
        """
        return list(self._worktrees.values())

    def _reconcile_tasks(
        self, existing_tasks: list[Task], source_tasks: list[Task]
    ) -> list[Task]:
        """
        Reconcile tasks from source with existing in-memory tasks.

        Args:
            existing_tasks: Current in-memory task list
            source_tasks: Fresh tasks from source

        Returns:
            Reconciled task list preserving source order and taking fields from source

        Reconciliation rules:
        - Tasks are matched by description (equivalence)
        - For matched tasks: preserve task_id from existing
        - For matched tasks: update description, tags, sequence_number, status, commit_sha from source
        - For new tasks: add as-is from source
        - Removed tasks: not included in result
        """
        # Create mapping of description -> existing Task for fast lookup
        existing_by_desc = {task.description: task for task in existing_tasks}

        reconciled = []
        for source_task in source_tasks:
            if source_task.description in existing_by_desc:
                # Task exists - preserve task_id, update everything else from source
                existing = existing_by_desc[source_task.description]

                # Create reconciled task with task_id from existing, everything else from source
                reconciled_task = Task(
                    task_id=existing.task_id,  # Preserve ID
                    description=source_task.description,  # Update from source
                    status=source_task.status,  # Update from source
                    sequence_number=source_task.sequence_number,  # Update from source
                    tags=source_task.tags,  # Update from source
                    commit_sha=source_task.commit_sha,  # Update from source
                )
                reconciled.append(reconciled_task)
            else:
                # New task - add as-is
                reconciled.append(source_task)

        return reconciled

    def _reconcile_worktrees(
        self, existing_worktrees: dict[str, Worktree], source_worktrees: list[Worktree]
    ) -> dict[str, Worktree]:
        """
        Reconcile worktrees from source with existing in-memory worktrees.

        Args:
            existing_worktrees: Current in-memory worktrees dict
            source_worktrees: Fresh worktrees from source

        Returns:
            Reconciled worktrees dict

        Reconciliation rules:
        - Worktrees are matched by worktree_name (equivalence)
        - For matched worktrees: reconcile tasks, update metadata from source
        - For new worktrees: add as-is
        - Removed worktrees: not included in result
        """
        reconciled = {}

        for source_wt in source_worktrees:
            if source_wt.worktree_name in existing_worktrees:
                # Worktree exists - reconcile tasks and update metadata
                existing_wt = existing_worktrees[source_wt.worktree_name]

                # Reconcile tasks
                reconciled_tasks = self._reconcile_tasks(
                    existing_wt.tasks, source_wt.tasks
                )

                # Create reconciled worktree with updated metadata from source
                reconciled_wt = Worktree(
                    worktree_name=source_wt.worktree_name,
                    worktree_id=source_wt.worktree_id,  # Update from source
                    agent=source_wt.agent,  # Update from source
                    tasks=reconciled_tasks,
                    directory_path=source_wt.directory_path,  # Update from source
                    head_sha=source_wt.head_sha,  # Update from source
                )
                reconciled[source_wt.worktree_name] = reconciled_wt
            else:
                # New worktree - add as-is
                reconciled[source_wt.worktree_name] = source_wt

        return reconciled

    def _find_task_by_description(
        self, worktree: Worktree, description: str
    ) -> Task | None:
        """Find a task in a worktree by exact description match"""
        for task in worktree.tasks:
            if task.description == description:
                return task
        return None

    def _find_task_by_id(self, worktree: Worktree, task_id: str) -> Task | None:
        """Find a task in a worktree by task_id"""
        for task in worktree.tasks:
            if task.task_id == task_id:
                return task
        return None

    def _find_next_eligible_task(self, worktree: Worktree) -> Task | None:
        """
        Find the next eligible task in a worktree.

        A task is eligible if and only if:
        - All tasks above it (lower sequence numbers) have status COMPLETED
        - Its own status is NOT_STARTED

        Args:
            worktree: Worktree to search

        Returns:
            The first eligible task, or None if no task is eligible
        """
        for task in worktree.tasks:
            # Only NOT_STARTED tasks can be eligible
            if task.status != TaskStatus.NOT_STARTED:
                continue

            # Check if all preceding tasks are COMPLETED
            all_preceding_completed = True
            for other_task in worktree.tasks:
                if other_task.sequence_number < task.sequence_number:
                    if other_task.status != TaskStatus.COMPLETED:
                        all_preceding_completed = False
                        break

            # If all preceding tasks are completed, this task is eligible
            if all_preceding_completed:
                return task

        # No eligible task found
        return None
