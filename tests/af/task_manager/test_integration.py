import pytest
import tempfile
from pathlib import Path
from af.task_manager import TaskManager, MarkdownTaskSource, TaskStatus


@pytest.fixture
def temp_task_file():
    """Fixture providing a temporary task file for integration tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Integration Test Tasks

## Git Worktree integration-test {INT001}

- [, taskab] First task {integration}
- [⏰, taskcd] Second task blocked by first {integration}
- [] Third task not started
""")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestEndToEndWorkflow:
    """Integration tests for full workflow"""

    def test_full_task_lifecycle(self):
        """Test complete task lifecycle from creation to completion"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Lifecycle Test

## Git Worktree lifecycle-test

- [] Task to complete
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            # Create source and manager
            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Load initial tasks from manager (not source)
            worktrees = manager.list_worktrees()
            assert len(worktrees) == 1
            assert len(worktrees[0].tasks) == 1

            task = worktrees[0].tasks[0]
            task_id = task.task_id

            # Fetch next available task
            available = manager.fetch_next_available_tasks(count=1)
            assert len(available) == 1
            wt, task = available[0]
            assert task.description == "Task to complete"

            # Update to IN_PROGRESS
            manager.update_task_status("lifecycle-test", task_id, TaskStatus.IN_PROGRESS)

            # Verify it's no longer available
            available = manager.fetch_next_available_tasks(count=1)
            assert len(available) == 0

            # Complete the task
            manager.update_task_status("lifecycle-test", task_id, TaskStatus.COMPLETED, "commit123")

            # Verify in file
            updated_source = MarkdownTaskSource(str(temp_path))
            worktrees = updated_source.list_worktrees()
            task = worktrees[0].tasks[0]
            assert task.status == TaskStatus.COMPLETED
            assert task.commit_sha == "commit123"

        finally:
            temp_path.unlink()

    def test_blocked_task_transitions(self, temp_task_file):
        """Test task becoming available after prerequisite completion"""
        # Reset singleton
        TaskManager._instance = None

        # Create source and manager
        source = MarkdownTaskSource(str(temp_task_file))
        manager = TaskManager(source)

        # Initially, only taskab should be available (first NOT_STARTED task)
        # taskcd is BLOCKED, third task is NOT_STARTED but blocked by taskcd being incomplete
        available = manager.fetch_next_available_tasks(count=5)

        # Should only get taskab (one task per worktree, first eligible NOT_STARTED)
        assert len(available) == 1
        wt, task = available[0]
        assert task.task_id == "taskab"

        # Complete taskab
        manager.update_task_status("integration-test", "taskab", TaskStatus.COMPLETED, "sha001")

        # Now taskcd is BLOCKED (not NOT_STARTED), so it's not eligible
        # Third task is NOT_STARTED but taskcd (seq 1) is not COMPLETED, so third task is also not eligible
        available = manager.fetch_next_available_tasks(count=5)
        assert len(available) == 0

        # Complete taskcd to unblock the third task
        manager.update_task_status("integration-test", "taskcd", TaskStatus.COMPLETED, "sha002")

        # Now the third task should be available
        available = manager.fetch_next_available_tasks(count=5)
        assert len(available) == 1
        wt, task = available[0]
        assert task.sequence_number == 2

    def test_adding_tasks_updates_existing_file(self):
        """Test that task IDs are written to existing tasks in file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Add Tasks Test

## Git Worktree add-test

- [] Task without ID
- [] Another task
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            # Create source and manager
            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Verify tasks were loaded and IDs were assigned
            worktrees = manager.list_worktrees()
            assert len(worktrees) == 1
            assert len(worktrees[0].tasks) == 2

            # All tasks should have task_ids written to file
            content = temp_path.read_text()

            # Verify by re-reading with a fresh source
            new_source = MarkdownTaskSource(str(temp_path))
            worktrees = new_source.list_worktrees()

            assert len(worktrees) == 1
            assert len(worktrees[0].tasks) == 2

            # All tasks should have task_ids
            for task in worktrees[0].tasks:
                assert task.task_id is not None
                assert len(task.task_id) == 6

        finally:
            temp_path.unlink()

    def test_multiple_worktrees_workflow(self):
        """Test workflow with multiple worktrees"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Multi Worktree Test

## Git Worktree wt1

- [] WT1 Task 1
- [⏰] WT1 Task 2

## Git Worktree wt2

- [] WT2 Task 1
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Fetch available tasks from both worktrees
            available = manager.fetch_next_available_tasks(count=5)

            # Should get tasks from both worktrees (one per worktree)
            assert len(available) == 2  # WT1 Task 1 and WT2 Task 1

            descriptions = {task.description for wt, task in available}
            assert "WT1 Task 1" in descriptions
            assert "WT2 Task 1" in descriptions

        finally:
            temp_path.unlink()

    def test_task_error_marking(self):
        """Test marking a task with an error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Error Test

## Git Worktree error-test

- [, errtsk] Task that will fail
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Mark task as error
            manager.mark_task_error("error-test", "errtsk", "Something went wrong")

            # Verify status is FAILED
            worktree = manager.get_worktree("error-test")
            assert worktree.tasks[0].status == TaskStatus.FAILED

            # Verify in file
            new_source = MarkdownTaskSource(str(temp_path))
            worktrees = new_source.list_worktrees()
            assert worktrees[0].tasks[0].status == TaskStatus.FAILED

        finally:
            temp_path.unlink()

    def test_refresh_with_external_file_changes(self):
        """Test refresh after external file modifications"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Refresh Test

## Git Worktree refresh-test

- [] Initial task
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Verify initial state
            worktree = manager.get_worktree("refresh-test")
            assert len(worktree.tasks) == 1
            assert worktree.tasks[0].description == "Initial task"

            # Mark task as in progress (writes to file)
            task_id = worktree.tasks[0].task_id
            manager.update_task_status("refresh-test", task_id, TaskStatus.IN_PROGRESS)

            # Externally modify the file (add a new task, keep IN_PROGRESS status)
            temp_path.write_text("""# Refresh Test

## Git Worktree refresh-test

- [🟡, """ + task_id + """] Initial task
- [] New task added externally
""")

            # Refresh
            manager.refresh_from_source()

            # Verify changes reflected
            worktree = manager.get_worktree("refresh-test")
            assert len(worktree.tasks) == 2
            assert worktree.tasks[0].description == "Initial task"
            assert worktree.tasks[0].status == TaskStatus.IN_PROGRESS  # Updated from source
            assert worktree.tasks[1].description == "New task added externally"

        finally:
            temp_path.unlink()

    def test_refresh_updates_task_state_from_source(self):
        """Test that refresh updates task state from source"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# State Update Test

## Git Worktree state-test

- [] Task 1
- [] Task 2
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Complete first task (writes to file)
            task1_id = manager.get_worktree("state-test").tasks[0].task_id
            manager.update_task_status("state-test", task1_id, TaskStatus.COMPLETED, "commit-abc")

            # Externally modify file (change status to IN_PROGRESS, remove second task)
            temp_path.write_text("""# State Update Test

## Git Worktree state-test

- [🟡, """ + task1_id + """, commit-xyz] Task 1
""")

            # Refresh
            manager.refresh_from_source()

            # Verify state updated from source
            worktree = manager.get_worktree("state-test")
            assert len(worktree.tasks) == 1
            assert worktree.tasks[0].status == TaskStatus.IN_PROGRESS  # Updated from source
            assert worktree.tasks[0].commit_sha == "commit-xyz"  # Updated from source

        finally:
            temp_path.unlink()

    def test_refresh_handles_new_worktree(self):
        """Test refresh when new worktree added to file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# New Worktree Test

## Git Worktree wt1

- [] Task 1
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            assert len(manager.list_worktrees()) == 1

            # Add new worktree to file
            temp_path.write_text("""# New Worktree Test

## Git Worktree wt1

- [] Task 1

## Git Worktree wt2

- [] Task 2
""")

            # Refresh
            manager.refresh_from_source()

            # Verify new worktree added
            worktrees = manager.list_worktrees()
            assert len(worktrees) == 2
            wt_names = {wt.worktree_name for wt in worktrees}
            assert "wt1" in wt_names
            assert "wt2" in wt_names

        finally:
            temp_path.unlink()

    def test_refresh_with_task_reordering(self):
        """Test refresh when tasks are reordered in file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Reorder Test

## Git Worktree reorder-test

- [] Task A
- [] Task B
- [] Task C
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Get initial task IDs
            worktree = manager.get_worktree("reorder-test")
            task_a_id = worktree.tasks[0].task_id
            task_b_id = worktree.tasks[1].task_id
            task_c_id = worktree.tasks[2].task_id

            # Complete Task A
            manager.update_task_status("reorder-test", task_a_id, TaskStatus.COMPLETED)

            # Reorder tasks in file (move Task A to end)
            temp_path.write_text(f"""# Reorder Test

## Git Worktree reorder-test

- [, {task_b_id}] Task B
- [, {task_c_id}] Task C
- [✅, {task_a_id}] Task A
""")

            # Refresh
            manager.refresh_from_source()

            # Verify new order and state from source
            worktree = manager.get_worktree("reorder-test")
            assert worktree.tasks[0].description == "Task B"
            assert worktree.tasks[1].description == "Task C"
            assert worktree.tasks[2].description == "Task A"
            assert worktree.tasks[2].status == TaskStatus.COMPLETED  # Updated from source

        finally:
            temp_path.unlink()
