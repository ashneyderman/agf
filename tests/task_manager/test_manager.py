import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from task_manager.manager import TaskManager
from task_manager.models import Task, Worktree, TaskStatus
from task_manager.markdown_source import MarkdownTaskSource


@pytest.fixture
def mock_task_source():
    """Fixture providing a mock TaskSource"""
    mock = Mock()
    mock.list_worktrees.return_value = []
    mock.update_task_status = Mock()
    mock.update_task_id = Mock()
    mock.mark_task_error = Mock()
    return mock


@pytest.fixture
def task_manager_with_mock(mock_task_source):
    """Fixture providing a TaskManager with mock source"""
    # Reset singleton for testing
    TaskManager._instance = None
    manager = TaskManager(mock_task_source)
    return manager


@pytest.fixture
def populated_task_source():
    """Fixture providing a TaskSource with existing data"""
    mock = Mock()

    task1 = Task(
        task_id="existq",
        description="Existing task 1",
        status=TaskStatus.COMPLETED,
        sequence_number=0
    )
    task2 = Task(
        task_id="existw",
        description="Existing task 2",
        status=TaskStatus.NOT_STARTED,
        sequence_number=1
    )

    worktree = Worktree(
        worktree_name="existing-wt",
        tasks=[task1, task2]
    )

    mock.list_worktrees.return_value = [worktree]
    mock.update_task_status = Mock()
    mock.update_task_id = Mock()
    mock.mark_task_error = Mock()

    return mock


class TestTaskManagerSingleton:
    """Tests for singleton behavior"""

    def test_singleton_returns_same_instance(self, mock_task_source):
        """Test that TaskManager returns the same instance"""
        TaskManager._instance = None

        manager1 = TaskManager(mock_task_source)
        manager2 = TaskManager(mock_task_source)

        assert manager1 is manager2

    def test_singleton_only_initializes_once(self):
        """Test that TaskManager only initializes once"""
        TaskManager._instance = None

        mock1 = Mock()
        mock1.list_worktrees.return_value = []

        mock2 = Mock()
        mock2.list_worktrees.return_value = []

        manager1 = TaskManager(mock1)
        manager2 = TaskManager(mock2)

        # Should only call list_worktrees on first initialization
        assert mock1.list_worktrees.called
        assert not mock2.list_worktrees.called


class TestTaskManagerUpdateStatus:
    """Tests for update_task_status method"""

    def test_update_task_status_updates_internal_state(self):
        """Test that update_task_status updates internal task state"""
        TaskManager._instance = None

        mock_source = Mock()
        task = Task(task_id="tskabc", description="Test task")
        worktree = Worktree(worktree_name="test-wt", tasks=[task])
        mock_source.list_worktrees.return_value = [worktree]
        mock_source.update_task_status = Mock()

        manager = TaskManager(mock_source)

        manager.update_task_status("test-wt", "tskabc", TaskStatus.COMPLETED, "sha123")

        # Check internal state
        wt = manager.get_worktree("test-wt")
        assert wt.tasks[0].status == TaskStatus.COMPLETED
        assert wt.tasks[0].commit_sha == "sha123"

    def test_update_task_status_calls_source(self):
        """Test that update_task_status calls the task source"""
        TaskManager._instance = None

        mock_source = Mock()
        task = Task(task_id="tskabc", description="Test task")
        worktree = Worktree(worktree_name="test-wt", tasks=[task])
        mock_source.list_worktrees.return_value = [worktree]
        mock_source.update_task_status = Mock()

        manager = TaskManager(mock_source)

        manager.update_task_status("test-wt", "tskabc", TaskStatus.IN_PROGRESS)

        mock_source.update_task_status.assert_called_once_with(
            "test-wt", "tskabc", TaskStatus.IN_PROGRESS, None
        )

    def test_update_task_status_raises_on_missing_worktree(self, task_manager_with_mock):
        """Test that updating nonexistent worktree raises error"""
        with pytest.raises(ValueError, match="not found"):
            task_manager_with_mock.update_task_status(
                "nonexistent", "tskabc", TaskStatus.COMPLETED
            )

    def test_update_task_status_raises_on_missing_task(self):
        """Test that updating nonexistent task raises error"""
        TaskManager._instance = None

        mock_source = Mock()
        task = Task(task_id="tskabc", description="Test task")
        worktree = Worktree(worktree_name="test-wt", tasks=[task])
        mock_source.list_worktrees.return_value = [worktree]
        mock_source.update_task_status = Mock()

        manager = TaskManager(mock_source)

        with pytest.raises(ValueError, match="not found"):
            manager.update_task_status("test-wt", "WRONG", TaskStatus.COMPLETED)


class TestTaskManagerMarkError:
    """Tests for mark_task_error method"""

    def test_mark_task_error_sets_failed_status(self):
        """Test that mark_task_error sets status to FAILED"""
        TaskManager._instance = None

        mock_source = Mock()
        task = Task(task_id="tskabc", description="Test task")
        worktree = Worktree(worktree_name="test-wt", tasks=[task])
        mock_source.list_worktrees.return_value = [worktree]
        mock_source.update_task_status = Mock()
        mock_source.mark_task_error = Mock()

        manager = TaskManager(mock_source)

        manager.mark_task_error("test-wt", "tskabc", "Error occurred")

        wt = manager.get_worktree("test-wt")
        assert wt.tasks[0].status == TaskStatus.FAILED

    def test_mark_task_error_calls_source(self):
        """Test that mark_task_error calls source method"""
        TaskManager._instance = None

        mock_source = Mock()
        task = Task(task_id="tskabc", description="Test task")
        worktree = Worktree(worktree_name="test-wt", tasks=[task])
        mock_source.list_worktrees.return_value = [worktree]
        mock_source.update_task_status = Mock()
        mock_source.mark_task_error = Mock()

        manager = TaskManager(mock_source)

        manager.mark_task_error("test-wt", "tskabc", "Error occurred")

        mock_source.mark_task_error.assert_called_once_with(
            "test-wt", "tskabc", "Error occurred"
        )


class TestTaskManagerFetchNextAvailable:
    """Tests for fetch_next_available_tasks method"""

    def test_fetch_returns_not_started_tasks(self):
        """Test that only the first NOT_STARTED task is returned per worktree"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.NOT_STARTED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=2)

        # Only the first task should be returned (one task per worktree)
        assert len(available) == 1
        wt, task = available[0]
        assert wt.worktree_name == "test-wt"
        assert task.task_id == "taskab"

    def test_fetch_skips_in_progress_tasks(self):
        """Test that tasks are not eligible when a preceding task is IN_PROGRESS"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.IN_PROGRESS, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=2)

        # Task 2 is not eligible because Task 1 is IN_PROGRESS (not COMPLETED)
        assert len(available) == 0

    def test_fetch_not_started_available_when_preceding_completed(self):
        """Test that NOT_STARTED tasks are eligible when all preceding are COMPLETED"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.COMPLETED, sequence_number=1),
            Task(task_id="taskef", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        assert len(available) == 1
        wt, task = available[0]
        assert wt.worktree_name == "test-wt"
        assert task.task_id == "taskef"

    def test_fetch_only_first_not_started_when_preceding_not_completed(self):
        """Test that only the first NOT_STARTED task is available"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
            Task(task_id="taskef", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        # Should get Task 2 only (one task per worktree, first NOT_STARTED)
        assert len(available) == 1
        wt, task = available[0]
        assert wt.worktree_name == "test-wt"
        assert task.task_id == "taskcd"

    def test_fetch_not_available_when_preceding_failed(self):
        """Test that tasks are not available when preceding task failed"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.FAILED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        assert len(available) == 0

    def test_fetch_respects_count_parameter(self):
        """Test that fetch respects the count parameter with multiple worktrees"""
        TaskManager._instance = None

        mock_source = Mock()
        # Create 5 worktrees with one task each
        task_ids = ["task0a", "task1b", "task2c", "task3d", "task4e"]
        worktrees = []
        for i in range(5):
            tasks = [
                Task(task_id=task_ids[i], description=f"WT{i} Task", status=TaskStatus.NOT_STARTED, sequence_number=0)
            ]
            worktrees.append(Worktree(worktree_name=f"wt{i}", tasks=tasks))

        mock_source.list_worktrees.return_value = worktrees

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=3)

        # Should get 3 tasks from 3 different worktrees
        assert len(available) == 3

    def test_fetch_from_multiple_worktrees(self):
        """Test fetching tasks from multiple worktrees"""
        TaskManager._instance = None

        mock_source = Mock()
        wt1_tasks = [
            Task(task_id="wtqtsk", description="WT1 Task 1", status=TaskStatus.NOT_STARTED, sequence_number=0),
        ]
        wt2_tasks = [
            Task(task_id="wtwtsk", description="WT2 Task 1", status=TaskStatus.NOT_STARTED, sequence_number=0),
        ]
        worktrees = [
            Worktree(worktree_name="wt1", tasks=wt1_tasks),
            Worktree(worktree_name="wt2", tasks=wt2_tasks),
        ]
        mock_source.list_worktrees.return_value = worktrees

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        assert len(available) == 2
        # Unpack tuples
        task_ids = {task.task_id for wt, task in available}
        worktree_names = {wt.worktree_name for wt, task in available}
        assert "wtqtsk" in task_ids
        assert "wtwtsk" in task_ids
        assert "wt1" in worktree_names
        assert "wt2" in worktree_names

    def test_prompt_example_feature_0_in_progress(self):
        """Test prompt example: feature 0 with task 2 in progress, task 3 not eligible"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="task1a", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="task2b", description="Task 2", status=TaskStatus.IN_PROGRESS, sequence_number=1),
            Task(task_id="task3c", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="feature-0", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)
        available = manager.fetch_next_available_tasks(count=5)

        # Task 3 is not eligible because Task 2 is IN_PROGRESS
        assert len(available) == 0

    def test_prompt_example_feature_1_eligible(self):
        """Test prompt example: feature 1 with task 1 completed, task 2 eligible"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="task1x", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="task2y", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
            Task(task_id="task3z", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="feature-1", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)
        available = manager.fetch_next_available_tasks(count=5)

        # Only Task 2 should be eligible (first NOT_STARTED task)
        assert len(available) == 1
        wt, task = available[0]
        assert wt.worktree_name == "feature-1"
        assert task.task_id == "task2y"

    def test_prompt_example_feature_2_failed(self):
        """Test prompt example: feature 2 with task 2 failed, task 3 not eligible"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="task1p", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="task2q", description="Task 2", status=TaskStatus.FAILED, sequence_number=1),
            Task(task_id="task3r", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="feature-2", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)
        available = manager.fetch_next_available_tasks(count=5)

        # Task 3 is not eligible because Task 2 FAILED
        assert len(available) == 0

    def test_all_three_prompt_examples_together(self):
        """Test all three prompt examples together to verify only feature-1 task-2 is eligible"""
        TaskManager._instance = None

        mock_source = Mock()

        # Feature 0: Task 1 completed, Task 2 in progress, Task 3 not started
        feature_0_tasks = [
            Task(task_id="f0tsk1", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="f0tsk2", description="Task 2", status=TaskStatus.IN_PROGRESS, sequence_number=1),
            Task(task_id="f0tsk3", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]

        # Feature 1: Task 1 completed, Task 2 and 3 not started
        feature_1_tasks = [
            Task(task_id="f1tsk1", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="f1tsk2", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
            Task(task_id="f1tsk3", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]

        # Feature 2: Task 1 completed, Task 2 failed, Task 3 not started
        feature_2_tasks = [
            Task(task_id="f2tsk1", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0, commit_sha="sha001"),
            Task(task_id="f2tsk2", description="Task 2", status=TaskStatus.FAILED, sequence_number=1),
            Task(task_id="f2tsk3", description="Task 3", status=TaskStatus.NOT_STARTED, sequence_number=2),
        ]

        worktrees = [
            Worktree(worktree_name="feature-0", tasks=feature_0_tasks),
            Worktree(worktree_name="feature-1", tasks=feature_1_tasks),
            Worktree(worktree_name="feature-2", tasks=feature_2_tasks),
        ]
        mock_source.list_worktrees.return_value = worktrees

        manager = TaskManager(mock_source)
        available = manager.fetch_next_available_tasks(count=5)

        # Only feature-1 Task 2 should be eligible
        assert len(available) == 1
        wt, task = available[0]
        assert wt.worktree_name == "feature-1"
        assert task.task_id == "f1tsk2"


class TestTaskManagerGetters:
    """Tests for getter methods"""

    def test_get_worktree_returns_correct_worktree(self):
        """Test get_worktree returns the correct worktree"""
        TaskManager._instance = None

        mock_source = Mock()
        worktree = Worktree(worktree_name="test-wt", tasks=[])
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        result = manager.get_worktree("test-wt")

        assert result is not None
        assert result.worktree_name == "test-wt"

    def test_get_worktree_returns_none_for_missing(self, task_manager_with_mock):
        """Test get_worktree returns None for missing worktree"""
        result = task_manager_with_mock.get_worktree("nonexistent")
        assert result is None

    def test_list_worktrees_returns_all(self):
        """Test list_worktrees returns all worktrees"""
        TaskManager._instance = None

        mock_source = Mock()
        worktrees = [
            Worktree(worktree_name="wt1", tasks=[]),
            Worktree(worktree_name="wt2", tasks=[]),
        ]
        mock_source.list_worktrees.return_value = worktrees

        manager = TaskManager(mock_source)

        result = manager.list_worktrees()

        assert len(result) == 2
        names = {wt.worktree_name for wt in result}
        assert "wt1" in names
        assert "wt2" in names
