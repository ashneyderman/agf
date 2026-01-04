import pytest
from pydantic import ValidationError
from task_manager.models import Task, Worktree, TaskStatus


def test_task_creation_with_all_fields():
    """Test creating a Task with all fields specified"""
    task = Task(
        task_id="abcdef",
        description="Test task",
        status=TaskStatus.IN_PROGRESS,
        sequence_number=1,
        tags=["test", "unit"],
        commit_sha="abc123"
    )

    assert task.task_id == "abcdef"
    assert task.description == "Test task"
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.sequence_number == 1
    assert task.tags == ["test", "unit"]
    assert task.commit_sha == "abc123"


def test_task_creation_with_defaults():
    """Test creating a Task with default values"""
    task = Task(description="Simple task")

    assert len(task.task_id) == 6
    assert task.task_id.islower()
    assert task.description == "Simple task"
    assert task.status == TaskStatus.NOT_STARTED
    assert task.sequence_number == 0
    assert task.tags == []
    assert task.commit_sha is None


def test_task_id_validation_length():
    """Test that task_id must be 6 characters"""
    with pytest.raises(ValidationError) as exc_info:
        Task(task_id="abc", description="Test")

    assert "6 characters long" in str(exc_info.value)


def test_task_id_validation_lowercase():
    """Test that task_id must be lowercase"""
    with pytest.raises(ValidationError) as exc_info:
        Task(task_id="ABCDEF", description="Test")

    assert "lowercase" in str(exc_info.value)


def test_task_status_enum_values():
    """Test TaskStatus enum has all expected values"""
    assert TaskStatus.NOT_STARTED.value == "not_started"
    assert TaskStatus.BLOCKED.value == "blocked"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


def test_worktree_creation():
    """Test creating a Worktree"""
    worktree = Worktree(
        worktree_name="feature-auth",
        worktree_id="SCHIP-7899"
    )

    assert worktree.worktree_name == "feature-auth"
    assert worktree.worktree_id == "SCHIP-7899"
    assert worktree.tasks == []
    assert worktree.directory_path is None
    assert worktree.head_sha is None


def test_worktree_with_tasks():
    """Test creating a Worktree with tasks"""
    task1 = Task(task_id="taskab", description="First task")
    task2 = Task(task_id="taskcd", description="Second task")

    worktree = Worktree(
        worktree_name="feature-test",
        tasks=[task1, task2]
    )

    assert len(worktree.tasks) == 2
    assert worktree.tasks[0].description == "First task"
    assert worktree.tasks[1].description == "Second task"


def test_worktree_name_validation():
    """Test that worktree_name cannot be empty"""
    with pytest.raises(ValidationError) as exc_info:
        Worktree(worktree_name="")

    assert "cannot be empty" in str(exc_info.value)


def test_worktree_defaults():
    """Test that Worktree sets default values correctly"""
    worktree = Worktree(worktree_name="test")

    assert worktree.worktree_id is None
    assert worktree.tasks == []
    assert worktree.directory_path is None
    assert worktree.head_sha is None


def test_worktree_id_can_be_set():
    """Test that worktree_id can be set and retrieved correctly"""
    worktree = Worktree(
        worktree_name="feature-xyz",
        worktree_id="PROJ-1234"
    )

    assert worktree.worktree_id == "PROJ-1234"
    assert worktree.worktree_name == "feature-xyz"
