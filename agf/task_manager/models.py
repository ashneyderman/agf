from enum import Enum

from pydantic import BaseModel, Field, field_validator

from .utils import generate_short_id


class TaskStatus(str, Enum):
    """Enum for task status values"""

    NOT_STARTED = "not_started"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """
    Represents a single task within a worktree.
    """

    task_id: str = Field(default_factory=lambda: generate_short_id(6))
    description: str
    status: TaskStatus = TaskStatus.NOT_STARTED
    sequence_number: int = 0
    tags: list[str] = Field(default_factory=list)
    commit_sha: str | None = None

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate that task_id is 6 lowercase characters"""
        if not v:
            return v
        if len(v) != 6:
            raise ValueError(f"task_id must be 6 characters long, got {len(v)}")
        if not v.islower():
            raise ValueError("task_id must be lowercase")
        return v


class Worktree(BaseModel):
    """
    Represents a git worktree containing tasks.
    """

    worktree_name: str
    worktree_id: str | None = None
    tasks: list[Task] = Field(default_factory=list)
    directory_path: str | None = None
    head_sha: str | None = None

    @field_validator("worktree_name")
    @classmethod
    def validate_worktree_name(cls, v: str) -> str:
        """Validate that worktree_name is not empty"""
        if not v or not v.strip():
            raise ValueError("worktree_name cannot be empty")
        return v
