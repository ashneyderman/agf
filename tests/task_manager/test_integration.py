import pytest
import tempfile
from pathlib import Path
from task_manager import TaskManager, MarkdownTaskSource, WorktreeInput, TaskStatus


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

    def test_task_deduplication_workflow(self):
        """Test that duplicate tasks are not added"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Dedup Test

## Git Worktree dedup-test

- [] Existing task
""")
            temp_path = Path(f.name)

        try:
            # Reset singleton
            TaskManager._instance = None

            source = MarkdownTaskSource(str(temp_path))
            manager = TaskManager(source)

            # Try to add the same task again
            new_tasks = [
                WorktreeInput(
                    worktree_name="dedup-test",
                    tasks_to_start=[
                        {"description": "Existing task", "tags": []},
                        {"description": "New unique task", "tags": []},
                    ]
                )
            ]

            manager.add_tasks(new_tasks)

            worktree = manager.get_worktree("dedup-test")

            # Should have 2 tasks (1 existing + 1 new), not 3
            assert len(worktree.tasks) == 2

            descriptions = [task.description for task in worktree.tasks]
            assert descriptions.count("Existing task") == 1
            assert "New unique task" in descriptions

        finally:
            temp_path.unlink()
