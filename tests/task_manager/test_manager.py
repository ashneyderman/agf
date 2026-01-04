import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from task_manager.manager import TaskManager
from task_manager.models import Task, Worktree, WorktreeInput, TaskStatus
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


class TestTaskManagerAddTasks:
    """Tests for add_tasks method"""

    def test_add_tasks_creates_new_worktree(self, task_manager_with_mock):
        """Test adding tasks creates a new worktree"""
        input_data = [
            WorktreeInput(
                worktree_name="new-wt",
                tasks_to_start=[
                    {"description": "Task 1", "tags": ["tag1"]},
                    {"description": "Task 2", "tags": []},
                ]
            )
        ]

        task_manager_with_mock.add_tasks(input_data)

        worktree = task_manager_with_mock.get_worktree("new-wt")
        assert worktree is not None
        assert worktree.worktree_name == "new-wt"
        assert len(worktree.tasks) == 2

    def test_add_tasks_deduplicates_by_worktree_name(self, task_manager_with_mock):
        """Test that duplicate worktree names are detected"""
        input_data1 = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[{"description": "Task 1"}]
            )
        ]
        input_data2 = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[{"description": "Task 2"}]
            )
        ]

        task_manager_with_mock.add_tasks(input_data1)
        task_manager_with_mock.add_tasks(input_data2)

        worktrees = task_manager_with_mock.list_worktrees()
        assert len(worktrees) == 1
        assert len(worktrees[0].tasks) == 2

    def test_add_tasks_deduplicates_by_description(self, task_manager_with_mock):
        """Test that duplicate task descriptions are skipped"""
        input_data = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[
                    {"description": "Same task"},
                    {"description": "Same task"},
                    {"description": "Different task"},
                ]
            )
        ]

        task_manager_with_mock.add_tasks(input_data)

        worktree = task_manager_with_mock.get_worktree("test-wt")
        assert len(worktree.tasks) == 2
        assert worktree.tasks[0].description == "Same task"
        assert worktree.tasks[1].description == "Different task"

    def test_add_tasks_generates_task_ids(self, task_manager_with_mock, mock_task_source):
        """Test that task IDs are generated for new tasks"""
        input_data = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[{"description": "Task 1"}]
            )
        ]

        task_manager_with_mock.add_tasks(input_data)

        worktree = task_manager_with_mock.get_worktree("test-wt")
        task = worktree.tasks[0]

        assert len(task.task_id) == 6
        assert task.task_id.islower()

    def test_add_tasks_assigns_sequence_numbers(self, task_manager_with_mock):
        """Test that sequence numbers are assigned correctly"""
        input_data = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[
                    {"description": "Task 1"},
                    {"description": "Task 2"},
                    {"description": "Task 3"},
                ]
            )
        ]

        task_manager_with_mock.add_tasks(input_data)

        worktree = task_manager_with_mock.get_worktree("test-wt")
        for i, task in enumerate(worktree.tasks):
            assert task.sequence_number == i

    def test_add_tasks_calls_update_task_id(self, task_manager_with_mock, mock_task_source):
        """Test that update_task_id is called for new tasks"""
        input_data = [
            WorktreeInput(
                worktree_name="test-wt",
                tasks_to_start=[{"description": "Task 1"}]
            )
        ]

        task_manager_with_mock.add_tasks(input_data)

        assert mock_task_source.update_task_id.called


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
        """Test that NOT_STARTED tasks are returned"""
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

        assert len(available) == 2
        assert available[0].task_id == "taskab"
        assert available[1].task_id == "taskcd"

    def test_fetch_skips_in_progress_tasks(self):
        """Test that IN_PROGRESS tasks are not returned"""
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

        assert len(available) == 1
        assert available[0].task_id == "taskcd"

    def test_fetch_blocked_available_when_preceding_completed(self):
        """Test that BLOCKED tasks are available when all preceding are COMPLETED"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.COMPLETED, sequence_number=1),
            Task(task_id="taskef", description="Task 3", status=TaskStatus.BLOCKED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        assert len(available) == 1
        assert available[0].task_id == "taskef"

    def test_fetch_blocked_not_available_when_preceding_not_completed(self):
        """Test that BLOCKED tasks are not available when preceding tasks incomplete"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.COMPLETED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.NOT_STARTED, sequence_number=1),
            Task(task_id="taskef", description="Task 3", status=TaskStatus.BLOCKED, sequence_number=2),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        # Should get TASK02 but not TASK03 (blocked by TASK02)
        assert len(available) == 1
        assert available[0].task_id == "taskcd"

    def test_fetch_blocked_not_available_when_preceding_failed(self):
        """Test that BLOCKED tasks are not available when preceding task failed"""
        TaskManager._instance = None

        mock_source = Mock()
        tasks = [
            Task(task_id="taskab", description="Task 1", status=TaskStatus.FAILED, sequence_number=0),
            Task(task_id="taskcd", description="Task 2", status=TaskStatus.BLOCKED, sequence_number=1),
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=5)

        assert len(available) == 0

    def test_fetch_respects_count_parameter(self):
        """Test that fetch respects the count parameter"""
        TaskManager._instance = None

        mock_source = Mock()
        # Generate 10 unique task IDs using letters only
        task_ids = ["tskabc", "tskdef", "tskghi", "tskjkl", "tskmno", "tskpqr", "tskstu", "tskwxy", "tskzab", "tskzcd"]
        tasks = [
            Task(task_id=task_ids[i], description=f"Task {i}", status=TaskStatus.NOT_STARTED, sequence_number=i)
            for i in range(10)
        ]
        worktree = Worktree(worktree_name="test-wt", tasks=tasks)
        mock_source.list_worktrees.return_value = [worktree]

        manager = TaskManager(mock_source)

        available = manager.fetch_next_available_tasks(count=3)

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
        task_ids = {task.task_id for task in available}
        assert "wtqtsk" in task_ids
        assert "wtwtsk" in task_ids


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
