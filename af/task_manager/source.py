from typing import Protocol

from .models import Worktree, TaskStatus


class TaskSource(Protocol):
    """
    Protocol defining the interface for task sources.

    Task sources can read tasks from various backends (Markdown files, databases, APIs)
    and update task status at the source.
    """

    def list_worktrees(self) -> list[Worktree]:
        """
        Retrieve all worktrees with their tasks from the source.

        Returns:
            List of Worktree objects with populated tasks
        """
        ...

    def update_task_status(
        self,
        worktree_name: str,
        task_id: str,
        status: TaskStatus,
        commit_sha: str | None = None
    ) -> None:
        """
        Update the status of a task at the source.

        Args:
            worktree_name: Name of the worktree containing the task
            task_id: ID of the task to update
            status: New status for the task
            commit_sha: Optional git SHA to record with the status update
        """
        ...

    def update_task_id(
        self,
        worktree_name: str,
        sequence_number: int,
        task_id: str
    ) -> None:
        """
        Write a generated task_id back to the source.

        Args:
            worktree_name: Name of the worktree containing the task
            sequence_number: Sequence number of the task within the worktree
            task_id: The generated task ID to write
        """
        ...

    def mark_task_error(
        self,
        worktree_name: str,
        task_id: str,
        error_msg: str
    ) -> None:
        """
        Mark a task as failed with an error message.

        Args:
            worktree_name: Name of the worktree containing the task
            task_id: ID of the task that failed
            error_msg: Error message to record
        """
        ...
