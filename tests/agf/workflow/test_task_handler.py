"""Unit tests for WorkflowTaskHandler."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import Repo

from agf.agent.base import AgentResult
from agf.config.models import AGFConfig, AgentModelConfig, CLIConfig, EffectiveConfig
from agf.task_manager import TaskManager
from agf.task_manager.models import Task, TaskStatus, Worktree
from agf.workflow import WorkflowTaskHandler


@pytest.fixture
def mock_config():
    """Create a mock EffectiveConfig for testing."""
    agf_config = AGFConfig(
        worktrees=".worktrees",
        concurrent_tasks=5,
        agent="claude-code",
        model_type="standard",
        agents={
            "claude-code": AgentModelConfig(
                thinking="opus", standard="sonnet", light="haiku"
            )
        },
    )
    cli_config = CLIConfig(
        tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
    )

    return EffectiveConfig(
        worktrees=agf_config.worktrees,
        concurrent_tasks=agf_config.concurrent_tasks,
        agents=agf_config.agents,
        tasks_file=cli_config.tasks_file,
        project_dir=cli_config.project_dir,
        agf_config=None,
        sync_interval=30,
        dry_run=False,
        single_run=False,
        agent=agf_config.agent,
        model_type=agf_config.model_type,
    )


@pytest.fixture
def mock_task_manager():
    """Create a mock TaskManager for testing."""
    manager = MagicMock(spec=TaskManager)
    return manager


@pytest.fixture
def sample_worktree():
    """Create a sample Worktree for testing."""
    return Worktree(worktree_name="test-feature", tasks=[])


@pytest.fixture
def sample_task():
    """Create a sample Task for testing."""
    return Task(task_id="abc123", description="Test task description")


class TestWorkflowTaskHandlerHelpers:
    """Test helper methods of WorkflowTaskHandler."""

    def test_get_username(self, mock_config, mock_task_manager):
        """Test username detection."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with patch.dict(os.environ, {"USER": "testuser"}):
            assert handler._get_username() == "testuser"

    def test_get_username_fallback(self, mock_config, mock_task_manager):
        """Test username fallback when USER not set."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with patch.dict(os.environ, {}, clear=True):
            assert handler._get_username() == "unknown"

    def test_get_worktree_path(
        self, mock_config, mock_task_manager, sample_worktree
    ):
        """Test worktree path construction."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        path = handler._get_worktree_path(sample_worktree)

        expected = os.path.abspath(
            os.path.join("/tmp/project", ".worktrees", "test-feature")
        )
        assert path == expected

    def test_get_branch_name(self, mock_config, mock_task_manager, sample_worktree):
        """Test branch name construction."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with patch.dict(os.environ, {"USER": "alex"}):
            branch = handler._get_branch_name(sample_worktree)
            assert branch == "alex/test-feature"


class TestWorkflowTaskHandlerWorktree:
    """Test worktree validation methods."""

    def test_has_uncommitted_changes_clean(self, mock_config, mock_task_manager):
        """Test clean worktree returns False."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Check clean repo
            assert handler._has_uncommitted_changes(tmpdir) is False

    def test_has_uncommitted_changes_modified(self, mock_config, mock_task_manager):
        """Test modified file returns True."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Modify file
            with open(test_file, "w") as f:
                f.write("modified")

            # Check dirty repo
            assert handler._has_uncommitted_changes(tmpdir) is True

    def test_has_uncommitted_changes_untracked(self, mock_config, mock_task_manager):
        """Test untracked file returns True."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Add untracked file
            untracked_file = os.path.join(tmpdir, "untracked.txt")
            with open(untracked_file, "w") as f:
                f.write("untracked")

            # Check repo with untracked file
            assert handler._has_uncommitted_changes(tmpdir) is True

    def test_validate_branch_checkout_correct(self, mock_config, mock_task_manager):
        """Test validation passes for correct branch."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo on specific branch
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Current branch is master/main
            current_branch = repo.active_branch.name

            # Validate current branch
            assert (
                handler._validate_branch_checkout(tmpdir, current_branch) is True
            )

    def test_validate_branch_checkout_wrong(self, mock_config, mock_task_manager):
        """Test validation fails for wrong branch."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Create and checkout new branch
            repo.create_head("feature-branch")
            repo.heads["feature-branch"].checkout()

            # Validate against wrong branch name
            assert (
                handler._validate_branch_checkout(tmpdir, "wrong-branch") is False
            )


class TestWorkflowTaskHandlerIntegration:
    """Integration tests for WorkflowTaskHandler."""

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful task handling."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution
        mock_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run.return_value = mock_result

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, sample_task)

        # Verify success
        assert result is True

        # Verify worktree created
        mock_mk_worktree.assert_called_once()

        # Verify status updates
        assert mock_task_manager.update_task_status.call_count == 2
        # First call: IN_PROGRESS
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.IN_PROGRESS
        )
        # Second call: COMPLETED
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.COMPLETED, commit_sha=None
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_failure(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test task handling with agent failure."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock failed agent execution
        mock_result = AgentResult(
            success=False,
            output="Task failed",
            exit_code=1,
            duration_seconds=5.0,
            agent_name="claude-code",
            error="Agent encountered an error",
        )
        mock_agent_runner.run.return_value = mock_result

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, sample_task)

        # Verify failure
        assert result is False

        # Verify status updates
        assert mock_task_manager.update_task_status.call_count == 2
        # First call: IN_PROGRESS
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.IN_PROGRESS
        )
        # Second call: FAILED
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.FAILED
        )

        # Verify error recorded
        mock_task_manager.mark_task_error.assert_called_once_with(
            "test-feature", "abc123", "Agent encountered an error"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_handle_task_uncommitted_changes(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test task handling fails with uncommitted changes."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Add uncommitted file
            uncommitted = os.path.join(tmpdir, "uncommitted.txt")
            with open(uncommitted, "w") as f:
                f.write("uncommitted")

            # Mock worktree path to use temp dir
            with patch.object(
                handler, "_get_worktree_path", return_value=tmpdir
            ), patch.object(
                handler, "_get_branch_name", return_value=repo.active_branch.name
            ), patch(
                "os.path.exists", return_value=True
            ):
                result = handler.handle_task(sample_worktree, sample_task)

            # Verify failure
            assert result is False

            # Verify error recorded
            mock_task_manager.mark_task_error.assert_called_once()
            args = mock_task_manager.mark_task_error.call_args[0]
            assert "uncommitted changes" in args[2].lower()

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_handle_task_wrong_branch(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test task handling fails with wrong branch."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # Create initial commit
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Mock worktree path to use temp dir with wrong branch
            with patch.object(
                handler, "_get_worktree_path", return_value=tmpdir
            ), patch.object(
                handler, "_get_branch_name", return_value="expected-branch"
            ), patch(
                "os.path.exists", return_value=True
            ):
                result = handler.handle_task(sample_worktree, sample_task)

            # Verify failure
            assert result is False

            # Verify error recorded
            mock_task_manager.mark_task_error.assert_called_once()
            args = mock_task_manager.mark_task_error.call_args[0]
            assert "expected branch" in args[2].lower()
