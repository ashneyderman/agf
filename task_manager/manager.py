from .models import Task, Worktree, WorktreeInput, TaskStatus
from .source import TaskSource
from .utils import generate_short_id


class TaskManager:
    """
    Singleton manager for task state and deduplication.

    Manages worktrees and tasks in memory, coordinating with TaskSource
    for persistence.
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
        worktrees = self._task_source.list_worktrees()
        for worktree in worktrees:
            self._worktrees[worktree.worktree_name] = worktree

            # Write task_ids back to source for tasks that were just loaded
            # (in case they were generated during parsing)
            for task in worktree.tasks:
                self._task_source.update_task_id(
                    worktree.worktree_name,
                    task.sequence_number,
                    task.task_id
                )

    def add_tasks(self, raw_worktrees: list[WorktreeInput]) -> None:
        """
        Add tasks from input data with deduplication.

        Args:
            raw_worktrees: List of WorktreeInput with tasks to add
        """
        for wt_input in raw_worktrees:
            worktree_name = wt_input.worktree_name

            # Check if worktree already exists (deduplication by name)
            if worktree_name in self._worktrees:
                worktree = self._worktrees[worktree_name]
            else:
                # Create new worktree
                worktree = Worktree(
                    worktree_name=worktree_name,
                    tasks=[]
                )
                self._worktrees[worktree_name] = worktree

            # Process tasks
            for task_data in wt_input.tasks_to_start:
                description = task_data.get('description', '')
                tags = task_data.get('tags', [])

                # Check if task already exists (deduplication by description)
                existing_task = self._find_task_by_description(worktree, description)
                if existing_task:
                    # Task already exists, skip
                    continue

                # Create new task
                task_id = generate_short_id(6)
                sequence_number = len(worktree.tasks)

                task = Task(
                    task_id=task_id,
                    description=description,
                    status=TaskStatus.NOT_STARTED,
                    sequence_number=sequence_number,
                    tags=tags,
                    commit_sha=None
                )

                worktree.tasks.append(task)

                # Write task_id back to source
                self._task_source.update_task_id(
                    worktree_name,
                    sequence_number,
                    task_id
                )

    def update_task_status(
        self,
        worktree_name: str,
        task_id: str,
        status: TaskStatus,
        commit_sha: str | None = None
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
            raise ValueError(f"Task '{task_id}' not found in worktree '{worktree_name}'")

        # Update internal state
        task.status = status
        if commit_sha:
            task.commit_sha = commit_sha

        # Update source
        self._task_source.update_task_status(worktree_name, task_id, status, commit_sha)

    def mark_task_error(
        self,
        worktree_name: str,
        task_id: str,
        error_msg: str
    ) -> None:
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

    def fetch_next_available_tasks(self, count: int = 1) -> list[Task]:
        """
        Fetch next available tasks for execution.

        A task is available if:
        - status == NOT_STARTED, OR
        - status == BLOCKED and all preceding tasks are COMPLETED

        Args:
            count: Maximum number of tasks to return

        Returns:
            List of available Task objects (up to count)
        """
        available_tasks = []

        for worktree in self._worktrees.values():
            for task in worktree.tasks:
                if len(available_tasks) >= count:
                    return available_tasks

                if self._is_task_available(worktree, task):
                    available_tasks.append(task)

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

    def _find_task_by_description(self, worktree: Worktree, description: str) -> Task | None:
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

    def _is_task_available(self, worktree: Worktree, task: Task) -> bool:
        """
        Check if a task is available for execution.

        Args:
            worktree: Worktree containing the task
            task: Task to check

        Returns:
            True if task is available, False otherwise
        """
        # NOT_STARTED tasks are always available
        if task.status == TaskStatus.NOT_STARTED:
            return True

        # BLOCKED tasks are available if all preceding tasks are COMPLETED
        if task.status == TaskStatus.BLOCKED:
            for other_task in worktree.tasks:
                # Check all tasks with lower sequence number
                if other_task.sequence_number < task.sequence_number:
                    if other_task.status != TaskStatus.COMPLETED:
                        # A preceding task is not completed, so this task is blocked
                        return False
            # All preceding tasks are completed
            return True

        # IN_PROGRESS, COMPLETED, and FAILED tasks are not available
        return False
