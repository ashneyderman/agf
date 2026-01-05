import pytest
from unittest.mock import Mock
from agf.task_manager.manager import TaskManager
from agf.task_manager.models import Task, Worktree, TaskStatus


@pytest.fixture
def mock_task_source():
    """Fixture providing a mock TaskSource"""
    mock = Mock()
    mock.list_worktrees.return_value = []
    mock.update_task_status = Mock()
    mock.update_task_id = Mock()
    mock.mark_task_error = Mock()
    return mock


class TestRefreshFromSource:
    """Tests for refresh_from_source method"""

    def test_refresh_adds_new_worktree(self, mock_task_source):
        """Test that refresh adds new worktrees from source"""
        TaskManager._instance = None

        # Initial state: empty
        manager = TaskManager(mock_task_source)
        assert len(manager.list_worktrees()) == 0

        # Source now has a worktree
        new_worktree = Worktree(
            worktree_name="new-wt",
            tasks=[
                Task(task_id="task1a", description="Task 1", sequence_number=0)
            ]
        )
        mock_task_source.list_worktrees.return_value = [new_worktree]

        # Refresh
        manager.refresh_from_source()

        # Verify worktree was added
        worktrees = manager.list_worktrees()
        assert len(worktrees) == 1
        assert worktrees[0].worktree_name == "new-wt"
        assert len(worktrees[0].tasks) == 1

    def test_refresh_removes_deleted_worktree(self, mock_task_source):
        """Test that refresh removes worktrees no longer in source"""
        TaskManager._instance = None

        # Initial state: one worktree
        existing_wt = Worktree(
            worktree_name="old-wt",
            tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [existing_wt]
        manager = TaskManager(mock_task_source)

        assert len(manager.list_worktrees()) == 1

        # Source now empty
        mock_task_source.list_worktrees.return_value = []

        # Refresh
        manager.refresh_from_source()

        # Verify worktree was removed
        assert len(manager.list_worktrees()) == 0

    def test_refresh_adds_new_task_to_existing_worktree(self, mock_task_source):
        """Test that refresh adds new tasks to existing worktrees"""
        TaskManager._instance = None

        # Initial state: worktree with one task
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        assert len(manager.get_worktree("test-wt").tasks) == 1

        # Source now has two tasks
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(task_id="task1a", description="Task 1", sequence_number=0),
                Task(task_id="task2b", description="Task 2", sequence_number=1)
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify new task was added
        worktree = manager.get_worktree("test-wt")
        assert len(worktree.tasks) == 2
        assert worktree.tasks[1].description == "Task 2"

    def test_refresh_removes_deleted_task(self, mock_task_source):
        """Test that refresh removes tasks no longer in source"""
        TaskManager._instance = None

        # Initial state: worktree with two tasks
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(task_id="task1a", description="Task 1", sequence_number=0),
                Task(task_id="task2b", description="Task 2", sequence_number=1)
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        assert len(manager.get_worktree("test-wt").tasks) == 2

        # Source now has only one task
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify task was removed
        worktree = manager.get_worktree("test-wt")
        assert len(worktree.tasks) == 1
        assert worktree.tasks[0].description == "Task 1"

    def test_refresh_updates_task_status_from_source(self, mock_task_source):
        """Test that refresh updates task status from source"""
        TaskManager._instance = None

        # Initial state: task with COMPLETED status
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.COMPLETED,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has same task but with IN_PROGRESS status
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.IN_PROGRESS,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify status was updated from source
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_refresh_updates_commit_sha_from_source(self, mock_task_source):
        """Test that refresh updates commit SHA from source"""
        TaskManager._instance = None

        # Initial state: task with commit SHA
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.COMPLETED,
                    commit_sha="abc123",
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has same task with different commit SHA
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.COMPLETED,
                    commit_sha="xyz789",
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify commit SHA was updated from source
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].commit_sha == "xyz789"

    def test_refresh_updates_task_tags(self, mock_task_source):
        """Test that refresh updates tags from source"""
        TaskManager._instance = None

        # Initial state: task with old tags
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    tags=["old-tag"],
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has same task with new tags
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    tags=["new-tag", "another-tag"],
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify tags were updated
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].tags == ["new-tag", "another-tag"]

    def test_refresh_updates_worktree_metadata(self, mock_task_source):
        """Test that refresh updates worktree metadata from source"""
        TaskManager._instance = None

        # Initial state: worktree with old metadata
        initial_wt = Worktree(
            worktree_name="test-wt",
            worktree_id="old-id",
            directory_path="/old/path",
            head_sha="old-sha",
            tasks=[]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has updated metadata
        updated_wt = Worktree(
            worktree_name="test-wt",
            worktree_id="new-id",
            directory_path="/new/path",
            head_sha="new-sha",
            tasks=[]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify metadata was updated
        worktree = manager.get_worktree("test-wt")
        assert worktree.worktree_id == "new-id"
        assert worktree.directory_path == "/new/path"
        assert worktree.head_sha == "new-sha"

    def test_refresh_reorders_tasks(self, mock_task_source):
        """Test that refresh handles task reordering"""
        TaskManager._instance = None

        # Initial state: tasks in one order
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(task_id="task1a", description="Task 1", sequence_number=0),
                Task(task_id="task2b", description="Task 2", sequence_number=1)
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has tasks in different order
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(task_id="task2b", description="Task 2", sequence_number=0),
                Task(task_id="task1a", description="Task 1", sequence_number=1)
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify order was updated
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].description == "Task 2"
        assert worktree.tasks[0].sequence_number == 0
        assert worktree.tasks[1].description == "Task 1"
        assert worktree.tasks[1].sequence_number == 1

    def test_refresh_handles_empty_source(self, mock_task_source):
        """Test that refresh handles source becoming empty"""
        TaskManager._instance = None

        # Initial state: multiple worktrees
        initial_wts = [
            Worktree(worktree_name="wt1", tasks=[]),
            Worktree(worktree_name="wt2", tasks=[])
        ]
        mock_task_source.list_worktrees.return_value = initial_wts
        manager = TaskManager(mock_task_source)

        assert len(manager.list_worktrees()) == 2

        # Source becomes empty
        mock_task_source.list_worktrees.return_value = []

        # Refresh
        manager.refresh_from_source()

        # Verify all worktrees removed
        assert len(manager.list_worktrees()) == 0

    def test_refresh_from_empty_to_populated(self, mock_task_source):
        """Test that refresh handles going from empty to populated"""
        TaskManager._instance = None

        # Initial state: empty
        manager = TaskManager(mock_task_source)
        assert len(manager.list_worktrees()) == 0

        # Source becomes populated
        new_wts = [
            Worktree(
                worktree_name="wt1",
                tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
            ),
            Worktree(
                worktree_name="wt2",
                tasks=[Task(task_id="task2b", description="Task 2", sequence_number=0)]
            )
        ]
        mock_task_source.list_worktrees.return_value = new_wts

        # Refresh
        manager.refresh_from_source()

        # Verify worktrees added
        assert len(manager.list_worktrees()) == 2

    def test_refresh_with_in_progress_task(self, mock_task_source):
        """Test that refresh updates IN_PROGRESS status from source"""
        TaskManager._instance = None

        # Initial state: task in progress
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.IN_PROGRESS,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has same task with COMPLETED status
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.COMPLETED,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify status updated from source
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].status == TaskStatus.COMPLETED

    def test_refresh_with_failed_task(self, mock_task_source):
        """Test that refresh updates FAILED status from source"""
        TaskManager._instance = None

        # Initial state: failed task
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.FAILED,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Source has same task with NOT_STARTED status
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.NOT_STARTED,
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify status updated from source
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].status == TaskStatus.NOT_STARTED

    def test_refresh_writes_task_ids_for_new_tasks(self, mock_task_source):
        """Test that refresh writes task IDs to source for new tasks"""
        TaskManager._instance = None

        # Initial state: empty
        manager = TaskManager(mock_task_source)
        mock_task_source.update_task_id.reset_mock()

        # Source has new worktree with task
        new_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [new_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify update_task_id was called
        assert mock_task_source.update_task_id.called
        mock_task_source.update_task_id.assert_called_with("test-wt", 0, "task1a")

    def test_refresh_idempotent_when_no_changes(self, mock_task_source):
        """Test that refresh is idempotent when source hasn't changed"""
        TaskManager._instance = None

        # Initial state
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.COMPLETED,
                    commit_sha="sha123",
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Get initial state
        worktree_before = manager.get_worktree("test-wt")
        task_before = worktree_before.tasks[0]

        # Refresh with same data
        manager.refresh_from_source()

        # Verify nothing changed
        worktree_after = manager.get_worktree("test-wt")
        task_after = worktree_after.tasks[0]

        assert task_after.task_id == task_before.task_id
        assert task_after.description == task_before.description
        assert task_after.status == task_before.status
        assert task_after.commit_sha == task_before.commit_sha

    def test_refresh_multiple_consecutive_times(self, mock_task_source):
        """Test multiple consecutive refreshes"""
        TaskManager._instance = None

        manager = TaskManager(mock_task_source)

        # First refresh: add worktree
        wt1 = Worktree(worktree_name="wt1", tasks=[])
        mock_task_source.list_worktrees.return_value = [wt1]
        manager.refresh_from_source()
        assert len(manager.list_worktrees()) == 1

        # Second refresh: add another worktree
        wt2 = Worktree(worktree_name="wt2", tasks=[])
        mock_task_source.list_worktrees.return_value = [wt1, wt2]
        manager.refresh_from_source()
        assert len(manager.list_worktrees()) == 2

        # Third refresh: remove first worktree
        mock_task_source.list_worktrees.return_value = [wt2]
        manager.refresh_from_source()
        assert len(manager.list_worktrees()) == 1
        assert manager.get_worktree("wt2") is not None
        assert manager.get_worktree("wt1") is None

    def test_refresh_after_task_status_update(self, mock_task_source):
        """Test refresh after manually updating task status - source takes precedence"""
        TaskManager._instance = None

        # Initial state
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="task1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        # Update task status in memory
        manager.update_task_status("test-wt", "task1a", TaskStatus.COMPLETED, "sha123")

        # Refresh with source showing different status (source is authoritative)
        refreshed_wt = Worktree(
            worktree_name="test-wt",
            tasks=[
                Task(
                    task_id="task1a",
                    description="Task 1",
                    status=TaskStatus.IN_PROGRESS,
                    commit_sha="sha456",
                    sequence_number=0
                )
            ]
        )
        mock_task_source.list_worktrees.return_value = [refreshed_wt]
        manager.refresh_from_source()

        # Verify source status takes precedence
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].status == TaskStatus.IN_PROGRESS
        assert worktree.tasks[0].commit_sha == "sha456"

    def test_refresh_preserves_task_id(self, mock_task_source):
        """Test that refresh preserves task_id for equivalent tasks"""
        TaskManager._instance = None

        # Initial state
        initial_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="orig1a", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [initial_wt]
        manager = TaskManager(mock_task_source)

        original_id = manager.get_worktree("test-wt").tasks[0].task_id

        # Source has same task with different ID
        updated_wt = Worktree(
            worktree_name="test-wt",
            tasks=[Task(task_id="newid1", description="Task 1", sequence_number=0)]
        )
        mock_task_source.list_worktrees.return_value = [updated_wt]

        # Refresh
        manager.refresh_from_source()

        # Verify original task_id was preserved
        worktree = manager.get_worktree("test-wt")
        assert worktree.tasks[0].task_id == original_id
