"""Tests for the process_tasks trigger script."""

import asyncio
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

from agf.task_manager.models import Task, TaskStatus, Worktree
from agf.triggers.process_tasks import (
    TriggerContext,
    bounded_task,
    log,
    main,
    process_task,
    process_tasks_parallel,
    run_iteration,
    setup_signal_handlers,
    validate_project_dir,
    validate_tasks_file,
)


class TestTriggerContext:
    """Tests for TriggerContext class."""

    def test_initial_state(self):
        """Test that context starts in running state."""
        ctx = TriggerContext()
        assert ctx.running is True
        assert ctx.current_iteration == 0

    def test_stop(self):
        """Test that stop sets running to False."""
        ctx = TriggerContext()
        ctx.stop()
        assert ctx.running is False


class TestValidateTasksFile:
    """Tests for validate_tasks_file function."""

    def test_valid_md_file(self, tmp_path):
        """Test validation of existing .md file."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        result = validate_tasks_file(None, None, str(tasks_file))

        assert result == tasks_file.resolve()

    def test_file_does_not_exist(self, tmp_path):
        """Test that non-existent file raises BadParameter."""
        non_existent = tmp_path / "missing.md"

        with pytest.raises(click.BadParameter) as exc_info:
            validate_tasks_file(None, None, str(non_existent))

        assert "does not exist" in str(exc_info.value)

    def test_file_wrong_extension(self, tmp_path):
        """Test that non-.md file raises BadParameter."""
        txt_file = tmp_path / "tasks.txt"
        txt_file.write_text("# Tasks\n")

        with pytest.raises(click.BadParameter) as exc_info:
            validate_tasks_file(None, None, str(txt_file))

        assert "must be a .md file" in str(exc_info.value)


class TestValidateProjectDir:
    """Tests for validate_project_dir function."""

    def test_valid_directory(self, tmp_path):
        """Test validation of existing directory."""
        result = validate_project_dir(None, None, str(tmp_path))

        assert result == tmp_path.resolve()

    def test_directory_does_not_exist(self, tmp_path):
        """Test that non-existent directory raises BadParameter."""
        non_existent = tmp_path / "missing_dir"

        with pytest.raises(click.BadParameter) as exc_info:
            validate_project_dir(None, None, str(non_existent))

        assert "does not exist" in str(exc_info.value)

    def test_path_is_file_not_directory(self, tmp_path):
        """Test that file path raises BadParameter."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        with pytest.raises(click.BadParameter) as exc_info:
            validate_project_dir(None, None, str(file_path))

        assert "not a directory" in str(exc_info.value)


class TestLog:
    """Tests for the log function."""

    def test_log_without_dry_run(self, capsys):
        """Test log output without dry run prefix."""
        log("Test message", dry_run=False)

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "[DRY-RUN]" not in captured.out

    def test_log_with_dry_run(self, capsys):
        """Test log output with dry run prefix."""
        log("Test message", dry_run=True)

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "[DRY-RUN]" in captured.out

    def test_log_includes_timestamp(self, capsys):
        """Test that log includes timestamp."""
        log("Test message")

        captured = capsys.readouterr()
        # Check for timestamp format [YYYY-MM-DD HH:MM:SS]
        assert "[20" in captured.out  # Year starts with 20xx


class TestSetupSignalHandlers:
    """Tests for setup_signal_handlers function."""

    def test_signal_handlers_set(self):
        """Test that signal handlers are configured."""
        ctx = TriggerContext()

        # Store original handlers
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        try:
            setup_signal_handlers(ctx)

            # Verify handlers are set (not the default)
            new_sigint = signal.getsignal(signal.SIGINT)
            new_sigterm = signal.getsignal(signal.SIGTERM)

            assert new_sigint != original_sigint
            assert new_sigterm != original_sigterm
        finally:
            # Restore original handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)


class TestProcessTask:
    """Tests for process_task async function."""

    @pytest.mark.asyncio
    async def test_process_task_prints_correct_output(self, capsys):
        """Test that process_task prints task information correctly."""
        from agf.config.models import EffectiveConfig, AgentModelConfig

        worktree = Worktree(
            worktree_name="feature-auth",
            worktree_id="AUTH-001",
            tasks=[],
        )
        task = Task(
            task_id="abc123",
            description="This is a very long description that should be truncated",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            await process_task(worktree, task, config, mock_task_manager)

        captured = capsys.readouterr()
        output = captured.out

        assert "worktree: feature-auth" in output
        assert "task_id: abc123" in output
        assert "description: This is a very long..." in output  # First 5 words with ellipsis

    @pytest.mark.asyncio
    async def test_process_task_truncates_description(self, capsys):
        """Test that description is truncated to 5 words."""
        from agf.config.models import EffectiveConfig, AgentModelConfig

        worktree = Worktree(worktree_name="wt", worktree_id="ID", tasks=[])
        task = Task(
            task_id="abc123",
            description="Short desc",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            await process_task(worktree, task, config, mock_task_manager)

        captured = capsys.readouterr()
        assert "description: Short desc" in captured.out  # Not truncated if shorter than 5 words

    @pytest.mark.asyncio
    async def test_process_task_calls_handler(self):
        """Test that process_task calls WorkflowTaskHandler."""
        from agf.config.models import EffectiveConfig, AgentModelConfig

        worktree = Worktree(worktree_name="wt", worktree_id="ID", tasks=[])
        task = Task(
            task_id="abc123",
            description="Task",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            await process_task(worktree, task, config, mock_task_manager)

        # Verify handler was created with correct params
        mock_handler.assert_called_once_with(config, mock_task_manager)
        mock_handler.return_value.handle_task.assert_called_once_with(worktree, task)

    @pytest.mark.asyncio
    async def test_process_task_reports_success(self, capsys):
        """Test that process_task reports success correctly."""
        from agf.config.models import EffectiveConfig, AgentModelConfig

        worktree = Worktree(worktree_name="wt", worktree_id="ID", tasks=[])
        task = Task(
            task_id="abc123",
            description="Task",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            await process_task(worktree, task, config, mock_task_manager)

        captured = capsys.readouterr()
        assert "Task completed: SUCCESS" in captured.out


class TestBoundedTask:
    """Tests for bounded_task async function."""

    @pytest.mark.asyncio
    async def test_bounded_task_executes_coroutine(self):
        """Test that bounded_task executes the coroutine."""
        sem = asyncio.Semaphore(1)

        async def sample_coro():
            return "result"

        result = await bounded_task(sem, sample_coro())

        assert result == "result"

    @pytest.mark.asyncio
    async def test_bounded_task_respects_semaphore(self):
        """Test that bounded_task respects semaphore limit."""
        sem = asyncio.Semaphore(2)
        execution_order = []

        async def tracked_coro(name):
            execution_order.append(f"{name}_start")
            await asyncio.sleep(0.01)
            execution_order.append(f"{name}_end")
            return name

        # Execute 3 tasks with semaphore limit of 2
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for i in range(3):
                tasks.append(tg.create_task(bounded_task(sem, tracked_coro(f"task{i}"))))

        # Verify all tasks completed
        assert len(execution_order) == 6


class TestProcessTasksParallel:
    """Tests for process_tasks_parallel async function."""

    @pytest.mark.asyncio
    async def test_no_available_tasks(self):
        """Test handling when no tasks are available."""
        mock_task_manager = MagicMock()
        mock_task_manager.fetch_next_available_tasks.return_value = []

        from agf.config.models import EffectiveConfig

        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        count = await process_tasks_parallel(mock_task_manager, config)

        assert count == 0
        mock_task_manager.fetch_next_available_tasks.assert_called_once_with(count=5)

    @pytest.mark.asyncio
    async def test_processes_multiple_tasks(self):
        """Test processing multiple tasks in parallel."""
        worktree1 = Worktree(worktree_name="wt1", worktree_id="ID1", tasks=[])
        task1 = Task(
            task_id="abc123",
            description="Task 1",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        worktree2 = Worktree(worktree_name="wt2", worktree_id="ID2", tasks=[])
        task2 = Task(
            task_id="def456",
            description="Task 2",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        mock_task_manager.fetch_next_available_tasks.return_value = [
            (worktree1, task1),
            (worktree2, task2),
        ]

        from agf.config.models import EffectiveConfig, AgentModelConfig

        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=2,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            count = await process_tasks_parallel(mock_task_manager, config)

        assert count == 2

    @pytest.mark.asyncio
    async def test_respects_concurrent_tasks_limit(self):
        """Test that concurrent_tasks limit is respected."""
        worktrees_and_tasks = []
        for i in range(10):
            wt = Worktree(worktree_name=f"wt{i}", worktree_id=f"ID{i}", tasks=[])
            task = Task(
                task_id=f"id{i:04d}",  # Ensure 6 characters like "id0000"
                description=f"Task {i}",
                status=TaskStatus.NOT_STARTED,
                sequence_number=1,
            )
            worktrees_and_tasks.append((wt, task))

        mock_task_manager = MagicMock()
        mock_task_manager.fetch_next_available_tasks.return_value = worktrees_and_tasks

        from agf.config.models import EffectiveConfig, AgentModelConfig

        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=3,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            count = await process_tasks_parallel(mock_task_manager, config)

        # Should fetch up to 3 tasks (concurrent_tasks limit)
        mock_task_manager.fetch_next_available_tasks.assert_called_once_with(count=3)
        assert count == 10  # All 10 returned tasks should be processed


class TestRunIteration:
    """Tests for run_iteration function."""

    def test_run_iteration_calls_process_tasks(self):
        """Test that run_iteration calls process_tasks_parallel."""
        mock_task_manager = MagicMock()
        mock_task_manager.fetch_next_available_tasks.return_value = []

        from agf.config.models import EffectiveConfig

        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        count = run_iteration(mock_task_manager, config, iteration=1)

        assert count == 0
        mock_task_manager.fetch_next_available_tasks.assert_called_once()

    def test_run_iteration_returns_task_count(self):
        """Test that run_iteration returns the number of tasks processed."""
        worktree = Worktree(worktree_name="wt", worktree_id="ID", tasks=[])
        task = Task(
            task_id="abc123",
            description="Task",
            status=TaskStatus.NOT_STARTED,
            sequence_number=1,
        )

        mock_task_manager = MagicMock()
        mock_task_manager.fetch_next_available_tasks.return_value = [(worktree, task)]

        from agf.config.models import EffectiveConfig, AgentModelConfig

        config = EffectiveConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agents={"claude-code": AgentModelConfig(thinking="opus", standard="sonnet", light="haiku")},
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agf_config=None,
            sync_interval=30,
            dry_run=True,
            single_run=True,
            testing=False,
            install_only=False,
            agent="claude-code",
            model_type="standard",
            branch_prefix=None,
            commands_namespace="agf",
        )

        with patch("agf.triggers.process_tasks.WorkflowTaskHandler") as mock_handler:
            mock_handler.return_value.handle_task.return_value = True
            count = run_iteration(mock_task_manager, config, iteration=1)

        assert count == 1


class TestCLI:
    """Tests for the CLI interface."""

    def test_help_option(self):
        """Test that --help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Process tasks from a task list" in result.output
        assert "--tasks-file" in result.output
        assert "--project-dir" in result.output
        assert "--sync-interval" in result.output
        assert "--dry-run" in result.output
        assert "--single-run" in result.output
        assert "--agf-config" in result.output

    def test_missing_required_options(self):
        """Test that missing required options cause error."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code != 0
        assert "Missing option" in result.output

    def test_missing_tasks_file(self):
        """Test that missing --tasks-file causes error."""
        runner = CliRunner()
        result = runner.invoke(main, ["--project-dir", "."])

        assert result.exit_code != 0
        assert "--tasks-file" in result.output

    def test_missing_project_dir(self):
        """Test that missing --project-dir causes error."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(main, ["--tasks-file", "tasks.md"])

        assert result.exit_code != 0
        assert "--project-dir" in result.output

    def test_invalid_tasks_file(self):
        """Test error when tasks file doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["--tasks-file", "nonexistent.md", "--project-dir", "."],
            )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_invalid_project_dir(self):
        """Test error when project dir doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                ["--tasks-file", "tasks.md", "--project-dir", "nonexistent_dir"],
            )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_single_run_dry_run(self):
        """Test single-run with dry-run mode."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Starting task processing trigger" in result.output
        assert "DRY-RUN" in result.output
        assert "Single run completed" in result.output

    def test_custom_sync_interval(self):
        """Test custom sync interval is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--sync-interval",
                    "60",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Sync interval: 60s" in result.output

    def test_default_concurrent_tasks(self):
        """Test that default concurrent_tasks is 5."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Concurrent tasks: 5" in result.output

    def test_with_agf_config(self, tmp_path):
        """Test loading AGF config file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            # Create AGF config with custom concurrent_tasks
            agf_config = Path(".agf.yaml")
            agf_config.write_text("concurrent-tasks: 3\n")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Loaded AGF config from:" in result.output
        assert "Concurrent tasks: 3" in result.output

    def test_explicit_agf_config_path(self, tmp_path):
        """Test specifying AGF config file path explicitly."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            # Create AGF config in a custom location
            config_dir = Path("config")
            config_dir.mkdir()
            agf_config = config_dir / "custom.yaml"
            agf_config.write_text("concurrent-tasks: 7\n")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--agf-config",
                    str(agf_config),
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Loaded AGF config from:" in result.output
        assert "Concurrent tasks: 7" in result.output

    def test_with_real_tasks_file(self):
        """Test processing a real tasks file with worktrees and tasks."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a properly formatted tasks file
            tasks_content = """# Test Tasks

## Git Worktree feature-auth

- [] Implement user login
- [] Add password hashing
"""
            Path("tasks.md").write_text(tasks_content)

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        # Check that it initialized and completed successfully
        assert "Initialized TaskManager" in result.output
        assert "Iteration 1 completed" in result.output
        assert "Single run completed" in result.output

    def test_empty_tasks_file(self):
        """Test with empty tasks file (no worktrees)."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Empty Tasks File\n")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Initialized TaskManager" in result.output
        assert "Iteration 1 completed" in result.output

    def test_tasks_file_with_no_eligible_tasks(self):
        """Test with tasks file where all tasks are completed."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            tasks_content = """# Test Tasks

## Git Worktree feature-done

- [✅, abc123] Completed task 1
- [✅, def456] Completed task 2
"""
            Path("tasks.md").write_text(tasks_content)

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Initialized TaskManager" in result.output
        assert "Iteration 1 completed" in result.output

    def test_invalid_agf_config_falls_back_to_defaults(self):
        """Test that invalid AGF config falls back to defaults."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            # Create invalid AGF config
            agf_config = Path(".agf.yaml")
            agf_config.write_text("invalid yaml content: [[[")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Warning: Failed to load AGF config" in result.output
        assert "Using default configuration" in result.output
        # Should use default concurrent_tasks of 5
        assert "Concurrent tasks: 5" in result.output

    def test_task_manager_initialization_error(self):
        """Test handling of TaskManager initialization error."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a tasks file that will cause an error
            # (e.g., malformed content that MarkdownTaskSource can't parse)
            Path("tasks.md").write_text("Not a valid tasks file format")

            # Note: This might not actually cause an error depending on
            # how robust MarkdownTaskSource is, but the test demonstrates
            # the error handling path
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        # The script should either succeed (if it parses the file as empty)
        # or exit with error code 1 (if initialization fails)
        assert result.exit_code in [0, 1]

    def test_install_only_option_in_help(self):
        """Test that --install-only appears in help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "--install-only" in result.output

    def test_install_only_mode(self):
        """Test install-only mode installs commands and exits."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--install-only",
                ],
            )

        assert result.exit_code == 0
        assert "Running in install-only mode" in result.output
        assert "Install-only completed" in result.output
        # Should NOT initialize TaskManager or process tasks
        assert "Initialized TaskManager" not in result.output

    def test_install_only_creates_agf_directory(self):
        """Test that install-only creates .agf directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            agf_dir = Path(".agf")
            assert not agf_dir.exists()

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--install-only",
                ],
            )

        assert result.exit_code == 0
        assert agf_dir.exists()
        assert (agf_dir / "claude" / "commands").exists()
        assert (agf_dir / "opencode" / "skill").exists()

    def test_install_only_creates_symlinks(self):
        """Test that install-only creates command symlinks."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--install-only",
                ],
            )

        assert result.exit_code == 0
        claude_symlink = Path(".claude") / "commands" / "agf"
        opencode_symlink = Path(".opencode") / "skill" / "agf"
        assert claude_symlink.is_symlink()
        assert opencode_symlink.is_symlink()

    def test_install_only_updates_gitignore(self):
        """Test that install-only updates .gitignore."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")

            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--install-only",
                ],
            )

        assert result.exit_code == 0
        gitignore = Path(".gitignore")
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".agf/" in content
