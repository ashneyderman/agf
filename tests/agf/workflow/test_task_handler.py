"""Unit tests for WorkflowTaskHandler."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import Repo

from agf.agent.base import AgentResult
from agf.config.models import AgentModelConfig, AGFConfig, CLIConfig, EffectiveConfig
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
        testing=False,
        install_only=False,
        agent=agf_config.agent,
        model_type=agf_config.model_type,
        branch_prefix=None,
        commands_namespace="agf",
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

    def test_get_worktree_path(self, mock_config, mock_task_manager, sample_worktree):
        """Test worktree path construction."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        path = handler._get_worktree_path(sample_worktree)

        expected = os.path.abspath(
            os.path.join("/tmp/project", ".worktrees", "test-feature")
        )
        assert path == expected

    def test_get_branch_name_without_worktree_id(
        self, mock_config, mock_task_manager, sample_worktree
    ):
        """Test branch name construction without worktree_id."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        with patch.dict(os.environ, {"USER": "alex"}):
            branch = handler._get_branch_name(sample_worktree)
            assert branch == "alex/test-feature"

    def test_get_branch_name_with_worktree_id(self, mock_config, mock_task_manager):
        """Test branch name construction with worktree_id."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(
            worktree_name="test-feature", worktree_id="SCHIP-7899"
        )

        with patch.dict(os.environ, {"USER": "alex"}):
            branch = handler._get_branch_name(worktree_with_id)
            assert branch == "alex/SCHIP-7899-test-feature"

    def test_get_branch_name_with_custom_prefix(self, mock_task_manager, sample_worktree):
        """Test branch name construction with custom branch_prefix."""
        # Create config with custom branch_prefix
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            branch_prefix="my-team",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                )
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
        )
        config_with_prefix = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=False,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix="my-team",
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config_with_prefix, mock_task_manager)

        branch = handler._get_branch_name(sample_worktree)
        assert branch == "my-team/test-feature"

    def test_get_branch_name_fallback_to_user(self, mock_config, mock_task_manager, sample_worktree):
        """Test branch name falls back to USER when branch_prefix is None."""
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
            assert handler._validate_branch_checkout(tmpdir, current_branch) is True

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
            assert handler._validate_branch_checkout(tmpdir, "wrong-branch") is False


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

        # Add feature tag to task
        sample_task.tags = ["feature"]

        # Mock successful agent execution for all three phases
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-feature-test.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={"commit_sha": "abc123def456"},
        )
        mock_agent_runner.run_command.side_effect = [feature_result, implement_result, commit_result]

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
            "test-feature", "abc123", TaskStatus.COMPLETED, commit_sha="abc123def456"
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

        # Add feature tag to task
        sample_task.tags = ["feature"]

        # Mock failed agent execution during planning phase
        mock_agent_runner.run_command.side_effect = Exception("Agent encountered an error")

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
            "test-feature", "abc123", "Planning phase failed: Agent encountered an error"
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
            with (
                patch.object(handler, "_get_worktree_path", return_value=tmpdir),
                patch.object(
                    handler, "_get_branch_name", return_value=repo.active_branch.name
                ),
                patch("os.path.exists", return_value=True),
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
            with (
                patch.object(handler, "_get_worktree_path", return_value=tmpdir),
                patch.object(
                    handler, "_get_branch_name", return_value="expected-branch"
                ),
                patch("os.path.exists", return_value=True),
            ):
                result = handler.handle_task(sample_worktree, sample_task)

            # Verify failure
            assert result is False

            # Verify error recorded
            mock_task_manager.mark_task_error.assert_called_once()
            args = mock_task_manager.mark_task_error.call_args[0]
            assert "expected branch" in args[2].lower()


class TestWorkflowTaskHandlerPromptWrappers:
    """Test SDLC prompt wrapper methods."""

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_plan_success(
        self, mock_agent_runner, mock_config, mock_task_manager, sample_task
    ):
        """Test successful plan execution with worktree_id."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(worktree_name="test-feature", worktree_id="agf-020")

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/agf-020-plan-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_plan(worktree_with_id, sample_task)

        # Verify result
        assert result == "specs/agf-020-plan-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template uses worktree_id instead of task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "plan"
        assert command_template.params == ["agf-020", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_chore_success(
        self, mock_agent_runner, mock_config, mock_task_manager, sample_task
    ):
        """Test successful chore execution with worktree_id."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(worktree_name="test-feature", worktree_id="agf-020")

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/agf-020-chore-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_chore(worktree_with_id, sample_task)

        # Verify result
        assert result == "specs/agf-020-chore-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template uses worktree_id instead of task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "chore"
        assert command_template.params == ["agf-020", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_feature_success(
        self, mock_agent_runner, mock_config, mock_task_manager, sample_task
    ):
        """Test successful feature execution with worktree_id."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(worktree_name="test-feature", worktree_id="agf-020")

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/agf-020-feature-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_feature(worktree_with_id, sample_task)

        # Verify result
        assert result == "specs/agf-020-feature-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template uses worktree_id instead of task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "feature"
        assert command_template.params == ["agf-020", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_implement_success(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful implement execution."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with string output
        mock_result = AgentResult(
            success=True,
            output="- Implemented feature X\n- Added tests\n- Updated docs\n",
            exit_code=0,
            duration_seconds=20.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_implement(
            sample_worktree, sample_task, "specs/abc123-feature-test.md"
        )

        # Verify result (should be stripped)
        assert result == "- Implemented feature X\n- Added tests\n- Updated docs"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "implement"
        assert command_template.params == ["@specs/abc123-feature-test.md"]
        assert command_template.model == "standard"
        assert command_template.json_output is False

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_build_success(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful build execution."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with string output
        mock_result = AgentResult(
            success=True,
            output="- Implemented task\n- Ran tests successfully\n- All checks passed\n",
            exit_code=0,
            duration_seconds=15.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_build(sample_worktree, sample_task)

        # Verify result (should be stripped)
        assert result == "- Implemented task\n- Ran tests successfully\n- All checks passed"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "build"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "standard"
        assert command_template.json_output is False

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_build_uses_worktree_id(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_task,
    ):
        """Test that build uses worktree_id when available."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(worktree_name="test-feature", worktree_id="agf-028")

        # Mock successful agent execution with string output
        mock_result = AgentResult(
            success=True,
            output="- Completed build task\n- Tests passed\n",
            exit_code=0,
            duration_seconds=12.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._run_build(worktree_with_id, sample_task)

        # Verify result
        assert result == "- Completed build task\n- Tests passed"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template uses worktree_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "build"
        assert command_template.params == ["agf-028", "Test task description"]
        assert command_template.model == "standard"
        assert command_template.json_output is False

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_create_commit_success(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful commit creation."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "abc123def456789",
                "commit_message": "feat: implement test feature",
            },
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._create_commit(sample_worktree, sample_task)

        # Verify result
        assert result["commit_sha"] == "abc123def456789"
        assert result["commit_message"] == "feat: implement test feature"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "create-commit"
        assert command_template.params == []
        assert command_template.model == "standard"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_create_empty_commit_success(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful empty commit creation."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "xyz789abc123",
                "commit_message": "add prompt wrapper function that calls... (task: agf-025)",
            },
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._create_empty_commit(sample_worktree, sample_task)

        # Verify result
        assert result["commit_sha"] == "xyz789abc123"
        assert result["commit_message"] == "add prompt wrapper function that calls... (task: agf-025)"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "empty-commit"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "standard"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_create_github_pr_success(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful GitHub PR creation."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with string output
        mock_result = AgentResult(
            success=True,
            output="https://github.com/owner/repo/pull/123\n\nPR #123: agf-027 - Add create-github-pr wrapper\n",
            exit_code=0,
            duration_seconds=8.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._create_github_pr(sample_worktree, sample_task)

        # Verify result (should be stripped)
        assert result == "https://github.com/owner/repo/pull/123\n\nPR #123: agf-027 - Add create-github-pr wrapper"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "create-github-pr"
        assert command_template.params == ["abc123"]
        assert command_template.model == "standard"
        assert command_template.json_output is False

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_create_github_pr_uses_worktree_id(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_task,
    ):
        """Test that create_github_pr uses worktree_id when available."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(worktree_name="test-feature", worktree_id="agf-027")

        # Mock successful agent execution with string output
        mock_result = AgentResult(
            success=True,
            output="https://github.com/owner/repo/pull/456\n\nPR #456: agf-027 - Feature implementation\n",
            exit_code=0,
            duration_seconds=8.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper
        result = handler._create_github_pr(worktree_with_id, sample_task)

        # Verify result
        assert result == "https://github.com/owner/repo/pull/456\n\nPR #456: agf-027 - Feature implementation"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template uses worktree_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "create-github-pr"
        assert command_template.params == ["agf-027"]
        assert command_template.model == "standard"
        assert command_template.json_output is False

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_plan_fallback_to_task_id(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test plan execution falls back to task_id when worktree_id is None."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-plan-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper with worktree that has no worktree_id
        result = handler._run_plan(sample_worktree, sample_task)

        # Verify result
        assert result == "specs/abc123-plan-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template falls back to task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "plan"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_chore_fallback_to_task_id(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test chore execution falls back to task_id when worktree_id is None."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-chore-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper with worktree that has no worktree_id
        result = handler._run_chore(sample_worktree, sample_task)

        # Verify result
        assert result == "specs/abc123-chore-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template falls back to task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "chore"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_run_feature_fallback_to_task_id(
        self,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test feature execution falls back to task_id when worktree_id is None."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock successful agent execution with JSON output
        mock_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-feature-test-task.md"},
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Call the wrapper with worktree that has no worktree_id
        result = handler._run_feature(sample_worktree, sample_task)

        # Verify result
        assert result == "specs/abc123-feature-test-task.md"

        # Verify AgentRunner was called with correct parameters
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args

        # Verify the command template falls back to task_id
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "feature"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "thinking"
        assert command_template.json_output is True


class TestWorkflowTaskHandlerTaskType:
    """Test task type detection methods."""

    def test_get_task_type_chore(self, mock_config, mock_task_manager):
        """Test task type detection for chore tag."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test01",
            description="Test task",
            tags=["chore", "backend"],
        )
        assert handler._get_task_type(task) == "chore"

    def test_get_task_type_feature(self, mock_config, mock_task_manager):
        """Test task type detection for feature tag."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test02",
            description="Test task",
            tags=["urgent", "feature"],
        )
        assert handler._get_task_type(task) == "feature"

    def test_get_task_type_plan(self, mock_config, mock_task_manager):
        """Test task type detection for plan tag."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test03",
            description="Test task",
            tags=["plan"],
        )
        assert handler._get_task_type(task) == "plan"

    def test_get_task_type_defaults_to_plan(self, mock_config, mock_task_manager):
        """Test task type detection defaults to 'plan' when no valid tag found."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test04",
            description="Test task",
            tags=["urgent", "backend"],
        )
        assert handler._get_task_type(task) == "plan"

    def test_get_task_type_empty_tags(self, mock_config, mock_task_manager):
        """Test task type detection defaults to 'plan' with empty tags."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test05",
            description="Test task",
            tags=[],
        )
        assert handler._get_task_type(task) == "plan"

    def test_get_task_type_first_match(self, mock_config, mock_task_manager):
        """Test task type detection returns first matching tag."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test06",
            description="Test task",
            tags=["chore", "feature"],  # Multiple valid types
        )
        # Should return the first match found
        assert handler._get_task_type(task) == "chore"

    def test_get_task_type_build(self, mock_config, mock_task_manager):
        """Test task type detection for build tag."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test07",
            description="Test task",
            tags=["build"],
        )
        assert handler._get_task_type(task) == "build"

    def test_get_task_type_build_with_other_tags(self, mock_config, mock_task_manager):
        """Test task type detection for build tag mixed with other non-type tags."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)
        task = Task(
            task_id="test08",
            description="Test task",
            tags=["urgent", "build", "backend"],
        )
        assert handler._get_task_type(task) == "build"


class TestWorkflowTaskHandlerSDLCFlow:
    """Test SDLC flow integration in handle_task."""

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_sdlc_flow_feature_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test successful SDLC flow for feature task."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a feature task
        feature_task = Task(
            task_id="feat01",
            description="Add user authentication",
            tags=["feature"],
        )

        # Mock agent execution results for each phase
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/feat01-feature-auth.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="- Implemented auth feature\n- Added tests",
            exit_code=0,
            duration_seconds=20.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "abc123",
                "commit_message": "feat: add user authentication",
            },
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            feature_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="feat01",
                    description="Add user authentication",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="feat02",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, feature_task)

        # Verify success
        assert result is True

        # Verify agent was called 3 times (feature, implement, commit)
        assert mock_agent_runner.run_command.call_count == 3

        # Verify task status updates
        assert mock_task_manager.update_task_status.call_count == 2
        # First call: IN_PROGRESS
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "feat01", TaskStatus.IN_PROGRESS
        )
        # Second call: COMPLETED with commit SHA
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "feat01", TaskStatus.COMPLETED, commit_sha="abc123"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_sdlc_flow_chore_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test successful SDLC flow for chore task."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a chore task
        chore_task = Task(
            task_id="chore1",
            description="Update dependencies",
            tags=["chore"],
        )

        # Mock agent execution results for each phase
        chore_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={"path": "specs/chore1-update-deps.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="- Updated dependencies\n- Ran tests",
            exit_code=0,
            duration_seconds=15.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "def456",
                "commit_message": "chore: update dependencies",
            },
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            chore_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="chore1",
                    description="Update dependencies",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="chore2",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, chore_task)

        # Verify success
        assert result is True

        # Verify agent was called 3 times (chore, implement, commit)
        assert mock_agent_runner.run_command.call_count == 3

        # Verify task completed
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "chore1", TaskStatus.COMPLETED, commit_sha="def456"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_sdlc_flow_plan_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test successful SDLC flow for plan task."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a plan task
        plan_task = Task(
            task_id="plan01",
            description="Design authentication system",
            tags=["plan"],
        )

        # Mock agent execution results for each phase
        plan_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=15.0,
            agent_name="claude-code",
            json_output={"path": "specs/plan01-auth-design.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="- Implemented design plan\n- Created architecture docs",
            exit_code=0,
            duration_seconds=25.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=4.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "ghi789",
                "commit_message": "docs: add authentication system design",
            },
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            plan_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="plan01",
                    description="Design authentication system",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="plan02",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, plan_task)

        # Verify success
        assert result is True

        # Verify agent was called 3 times (plan, implement, commit)
        assert mock_agent_runner.run_command.call_count == 3

        # Verify task completed
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "plan01", TaskStatus.COMPLETED, commit_sha="ghi789"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_missing_task_type(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test task handling defaults to 'plan' workflow when task type tag is missing."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a task without valid type tag (should default to plan)
        task_without_type = Task(
            task_id="inval1",
            description="Task without type tag",
            tags=["urgent", "backend"],  # No chore/feature/plan tag
        )

        # Mock agent execution results for each phase (plan workflow)
        plan_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/inval1-default-plan.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="- Implemented task\n- Added documentation",
            exit_code=0,
            duration_seconds=15.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "xyz123",
                "commit_message": "docs: task without type tag",
            },
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            plan_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="inval1",
                    description="Task without type tag",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="inval2",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, task_without_type)

        # Verify success
        assert result is True

        # Verify agent was called 3 times (plan, implement, commit)
        assert mock_agent_runner.run_command.call_count == 3

        # Verify task completed successfully
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "inval1", TaskStatus.COMPLETED, commit_sha="xyz123"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_planning_phase_failure(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test task handling fails when planning phase fails."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a feature task
        feature_task = Task(
            task_id="feat02",
            description="Add payment processing",
            tags=["feature"],
        )

        # Mock planning phase to raise an exception
        mock_agent_runner.run_command.side_effect = Exception("Planning failed")

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, feature_task)

        # Verify failure
        assert result is False

        # Verify error recorded
        mock_task_manager.mark_task_error.assert_called_once()
        args = mock_task_manager.mark_task_error.call_args[0]
        assert "planning phase failed" in args[2].lower()

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_implementation_phase_failure(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test task handling fails when implementation phase fails."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a feature task
        feature_task = Task(
            task_id="feat03",
            description="Add search functionality",
            tags=["feature"],
        )

        # Mock planning succeeds, but implementation fails
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/feat03-search.md"},
        )

        mock_agent_runner.run_command.side_effect = [
            feature_result,
            Exception("Implementation failed"),
        ]

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, feature_task)

        # Verify failure
        assert result is False

        # Verify error recorded
        mock_task_manager.mark_task_error.assert_called_once()
        args = mock_task_manager.mark_task_error.call_args[0]
        assert "implementation phase failed" in args[2].lower()

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_commit_phase_failure(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test task handling fails when commit phase fails."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a feature task
        feature_task = Task(
            task_id="feat04",
            description="Add notifications",
            tags=["feature"],
        )

        # Mock planning and implementation succeed, but commit fails
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/feat04-notifications.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="- Added notifications",
            exit_code=0,
            duration_seconds=20.0,
            agent_name="claude-code",
        )

        mock_agent_runner.run_command.side_effect = [
            feature_result,
            implement_result,
            Exception("Commit failed"),
        ]

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, feature_task)

        # Verify failure
        assert result is False

        # Verify error recorded
        mock_task_manager.mark_task_error.assert_called_once()
        args = mock_task_manager.mark_task_error.call_args[0]
        assert "commit phase failed" in args[2].lower()

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_sdlc_flow_build_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test successful SDLC flow for build task."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a build task
        build_task = Task(
            task_id="bld001",
            description="Run build and fix any type errors",
            tags=["build"],
        )

        # Mock agent execution results for build and commit phases only
        build_result = AgentResult(
            success=True,
            output="- Fixed 3 type errors\n- Build passed successfully",
            exit_code=0,
            duration_seconds=30.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "build123",
                "commit_message": "chore: fix type errors from build",
            },
        )

        # Set up mock to return different results for each call
        # Build workflow should only call agent 2 times (build, commit)
        mock_agent_runner.run_command.side_effect = [
            build_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="bld001",
                    description="Run build and fix any type errors",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="bld002",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, build_task)

        # Verify success
        assert result is True

        # Verify agent was called exactly 2 times (build, commit) NOT 3 times
        assert mock_agent_runner.run_command.call_count == 2

        # Verify task status updates
        assert mock_task_manager.update_task_status.call_count == 2
        # First call: IN_PROGRESS
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "bld001", TaskStatus.IN_PROGRESS
        )
        # Second call: COMPLETED with commit SHA
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "bld001", TaskStatus.COMPLETED, commit_sha="build123"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_build_phase_failure(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_worktree,
    ):
        """Test task handling fails when build phase fails."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create a build task
        build_task = Task(
            task_id="bld002",
            description="Run build",
            tags=["build"],
        )

        # Mock build phase to raise an exception
        mock_agent_runner.run_command.side_effect = Exception("Build failed")

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, build_task)

        # Verify failure
        assert result is False

        # Verify error recorded
        mock_task_manager.mark_task_error.assert_called_once()
        args = mock_task_manager.mark_task_error.call_args[0]
        assert "build phase failed" in args[2].lower()


class TestWorkflowTaskHandlerTestingMode:
    """Test testing mode functionality in WorkflowTaskHandler."""

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_testing_mode_success(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test successful task handling in testing mode."""
        # Create config with testing=True
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
            tasks_file=Path("/tmp/tasks.md"),
            project_dir=Path("/tmp/project"),
            testing=True,
        )
        config_with_testing = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=True,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config_with_testing, mock_task_manager)

        # Mock successful empty commit execution
        empty_commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "test123abc",
                "commit_message": "test commit (task: abc123)",
            },
        )
        mock_agent_runner.run_command.return_value = empty_commit_result

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, sample_task)

        # Verify success
        assert result is True

        # Verify AgentRunner was called exactly once with empty-commit prompt
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "empty-commit"
        assert command_template.params == ["abc123", "Test task description"]
        assert command_template.model == "standard"
        assert command_template.json_output is True

        # Verify status updates
        assert mock_task_manager.update_task_status.call_count == 2
        # First call: IN_PROGRESS
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.IN_PROGRESS
        )
        # Second call: COMPLETED with commit SHA
        mock_task_manager.update_task_status.assert_any_call(
            "test-feature", "abc123", TaskStatus.COMPLETED, commit_sha="test123abc"
        )

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_testing_mode_uses_worktree_id(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_task_manager,
        sample_task,
    ):
        """Test testing mode uses worktree_id when available."""
        # Create config with testing=True
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
            tasks_file=Path("/tmp/tasks.md"),
            project_dir=Path("/tmp/project"),
            testing=True,
        )
        config_with_testing = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=True,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config_with_testing, mock_task_manager)

        # Create worktree with worktree_id
        worktree_with_id = Worktree(
            worktree_name="test-feature", worktree_id="agf-025"
        )

        # Mock successful empty commit execution
        empty_commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "test456def",
                "commit_message": "test commit (task: agf-025)",
            },
        )
        mock_agent_runner.run_command.return_value = empty_commit_result

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(worktree_with_id, sample_task)

        # Verify success
        assert result is True

        # Verify the agf_id passed to empty-commit is task_id
        call_args = mock_agent_runner.run_command.call_args
        command_template = call_args[1]["command_template"]
        assert command_template.params == ["abc123", "Test task description"]

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_testing_mode_fallback_to_task_id(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test testing mode falls back to task_id when worktree_id is None."""
        # Create config with testing=True
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
            tasks_file=Path("/tmp/tasks.md"),
            project_dir=Path("/tmp/project"),
            testing=True,
        )
        config_with_testing = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=True,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config_with_testing, mock_task_manager)

        # Mock successful empty commit execution
        empty_commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "test789ghi",
                "commit_message": "test commit (task: abc123)",
            },
        )
        mock_agent_runner.run_command.return_value = empty_commit_result

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, sample_task)

        # Verify success
        assert result is True

        # Verify the agf_id falls back to task_id
        call_args = mock_agent_runner.run_command.call_args
        command_template = call_args[1]["command_template"]
        assert command_template.params == ["abc123", "Test task description"]


class TestWorkflowTaskHandlerPRCreation:
    """Test PR creation helper and auto-PR creation functionality."""

    def test_all_worktree_tasks_completed_true(self, mock_config, mock_task_manager):
        """Test all tasks have COMPLETED status."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with all completed tasks
        all_completed_worktree = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(task_id="task01", description="Task 1", status=TaskStatus.COMPLETED),
                Task(task_id="task02", description="Task 2", status=TaskStatus.COMPLETED),
                Task(task_id="task03", description="Task 3", status=TaskStatus.COMPLETED),
            ],
        )

        # Mock task_manager to return the worktree
        mock_task_manager.get_worktree.return_value = all_completed_worktree

        # Verify returns True
        assert handler._all_worktree_tasks_completed("test-feature") is True

    def test_all_worktree_tasks_completed_false_mixed_status(
        self, mock_config, mock_task_manager
    ):
        """Test some tasks not completed."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with mixed status tasks
        mixed_status_worktree = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(task_id="task01", description="Task 1", status=TaskStatus.COMPLETED),
                Task(
                    task_id="task02",
                    description="Task 2",
                    status=TaskStatus.NOT_STARTED,
                ),
                Task(task_id="task03", description="Task 3", status=TaskStatus.COMPLETED),
            ],
        )

        # Mock task_manager to return the worktree
        mock_task_manager.get_worktree.return_value = mixed_status_worktree

        # Verify returns False
        assert handler._all_worktree_tasks_completed("test-feature") is False

    def test_all_worktree_tasks_completed_empty_worktree(
        self, mock_config, mock_task_manager
    ):
        """Test worktree with no tasks returns False."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with no tasks
        empty_worktree = Worktree(worktree_name="test-feature", tasks=[])

        # Mock task_manager to return the empty worktree
        mock_task_manager.get_worktree.return_value = empty_worktree

        # Verify returns False
        assert handler._all_worktree_tasks_completed("test-feature") is False

    def test_all_worktree_tasks_completed_worktree_not_found(
        self, mock_config, mock_task_manager
    ):
        """Test worktree doesn't exist returns False."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Mock task_manager to return None
        mock_task_manager.get_worktree.return_value = None

        # Verify returns False
        assert handler._all_worktree_tasks_completed("nonexistent") is False

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_creates_pr_when_all_tasks_completed(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_task,
    ):
        """Test PR creation is triggered when all tasks are completed."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with feature tag task
        sample_task.tags = ["feature"]
        worktree = Worktree(worktree_name="test-feature", tasks=[sample_task])

        # Mock successful agent execution results for all phases
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-feature-test.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={"commit_sha": "abc123def456"},
        )
        pr_result = AgentResult(
            success=True,
            output="PR created: https://github.com/owner/repo/pull/123",
            exit_code=0,
            duration_seconds=8.0,
            agent_name="claude-code",
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            feature_result,
            implement_result,
            commit_result,
            pr_result,
        ]

        # Mock task_manager.get_worktree to return worktree with all tasks completed
        worktree_with_completed_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="abc123",
                    description="Test task description",
                    status=TaskStatus.COMPLETED,
                )
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_completed_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(worktree, sample_task)

        # Verify success
        assert result is True

        # Verify agent was called 4 times (feature, implement, commit, pr)
        assert mock_agent_runner.run_command.call_count == 4

        # Verify last call was create-github-pr
        last_call = mock_agent_runner.run_command.call_args_list[-1]
        command_template = last_call[1]["command_template"]
        assert command_template.prompt == "create-github-pr"

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_skips_pr_in_testing_mode(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_task_manager,
        sample_worktree,
        sample_task,
    ):
        """Test PR creation is skipped when testing mode is enabled."""
        # Create config with testing=True
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
            tasks_file=Path("/tmp/tasks.md"),
            project_dir=Path("/tmp/project"),
            testing=True,
        )
        config_with_testing = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=True,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config_with_testing, mock_task_manager)

        # Mock successful empty commit execution
        empty_commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=3.0,
            agent_name="claude-code",
            json_output={
                "commit_sha": "test123abc",
                "commit_message": "test commit (task: abc123)",
            },
        )
        mock_agent_runner.run_command.return_value = empty_commit_result

        # Mock task_manager.get_worktree to return worktree with all tasks completed
        worktree_with_completed_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="abc123",
                    description="Test task description",
                    status=TaskStatus.COMPLETED,
                )
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_completed_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(sample_worktree, sample_task)

        # Verify success
        assert result is True

        # Verify agent was called exactly once (only empty-commit, no PR creation)
        assert mock_agent_runner.run_command.call_count == 1
        call_args = mock_agent_runner.run_command.call_args
        command_template = call_args[1]["command_template"]
        assert command_template.prompt == "empty-commit"

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_skips_pr_when_tasks_remaining(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_config,
        mock_task_manager,
        sample_task,
    ):
        """Test PR creation is skipped when some tasks are not completed."""
        handler = WorkflowTaskHandler(mock_config, mock_task_manager)

        # Create worktree with feature tag task
        sample_task.tags = ["feature"]
        worktree = Worktree(worktree_name="test-feature", tasks=[sample_task])

        # Mock successful agent execution results for all phases
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
            json_output={"path": "specs/abc123-feature-test.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="claude-code",
            json_output={"commit_sha": "abc123def456"},
        )

        # Set up mock to return different results for each call
        mock_agent_runner.run_command.side_effect = [
            feature_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with some NOT_STARTED tasks
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="abc123",
                    description="Test task description",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="def456",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(worktree, sample_task)

        # Verify success
        assert result is True

        # Verify agent was called 3 times (feature, implement, commit - no PR)
        assert mock_agent_runner.run_command.call_count == 3

        # Verify last call was create-commit, not create-github-pr
        last_call = mock_agent_runner.run_command.call_args_list[-1]
        command_template = last_call[1]["command_template"]
        assert command_template.prompt == "create-commit"


class TestWorkflowTaskHandlerWorktreeAgentOverride:
    """Test worktree agent override functionality."""

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_execute_command_uses_worktree_agent(
        self, mock_agent_runner, mock_task_manager, sample_task
    ):
        """Test that _execute_command uses worktree.agent when set."""
        # Create config with multiple agents
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
                "opencode": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
        )
        config = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=False,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config, mock_task_manager)

        # Create worktree with agent override
        worktree_with_agent = Worktree(
            worktree_name="test-feature", agent="opencode"
        )

        # Mock successful agent execution
        mock_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="opencode",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Create a command template
        from agf.agent.models import CommandTemplate

        command_template = CommandTemplate(
            namespace="agf",
            prompt="test",
            params=["param1"],
            model="standard",
            json_output=False,
        )

        # Call _execute_command
        result = handler._execute_command(worktree_with_agent, command_template)

        # Verify result
        assert result.success is True
        assert result.agent_name == "opencode"

        # Verify AgentRunner was called with opencode agent
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args
        assert call_args[1]["agent_name"] == "opencode"

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_execute_command_uses_config_agent_when_worktree_agent_none(
        self, mock_agent_runner, mock_task_manager, sample_worktree
    ):
        """Test that _execute_command uses config.agent when worktree.agent is None."""
        # Create config
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
        )
        config = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=False,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config, mock_task_manager)

        # Mock successful agent execution
        mock_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Create a command template
        from agf.agent.models import CommandTemplate

        command_template = CommandTemplate(
            namespace="agf",
            prompt="test",
            params=["param1"],
            model="standard",
            json_output=False,
        )

        # Call _execute_command with worktree that has no agent override
        result = handler._execute_command(sample_worktree, command_template)

        # Verify result
        assert result.success is True
        assert result.agent_name == "claude-code"

        # Verify AgentRunner was called with claude-code agent
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args
        assert call_args[1]["agent_name"] == "claude-code"

    @patch("agf.workflow.task_handler.AgentRunner")
    def test_execute_command_fallback_to_config_agent_on_invalid_worktree_agent(
        self, mock_agent_runner, mock_task_manager
    ):
        """Test that _execute_command falls back to config.agent when worktree.agent is invalid."""
        # Create config
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
        )
        config = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=False,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config, mock_task_manager)

        # Create worktree with invalid agent name
        worktree_with_invalid_agent = Worktree(
            worktree_name="test-feature", agent="nonexistent-agent"
        )

        # Mock successful agent execution
        mock_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="claude-code",
        )
        mock_agent_runner.run_command.return_value = mock_result

        # Create a command template
        from agf.agent.models import CommandTemplate

        command_template = CommandTemplate(
            namespace="agf",
            prompt="test",
            params=["param1"],
            model="standard",
            json_output=False,
        )

        # Call _execute_command
        result = handler._execute_command(worktree_with_invalid_agent, command_template)

        # Verify result - should use fallback agent
        assert result.success is True
        assert result.agent_name == "claude-code"

        # Verify AgentRunner was called with claude-code agent (fallback)
        mock_agent_runner.run_command.assert_called_once()
        call_args = mock_agent_runner.run_command.call_args
        assert call_args[1]["agent_name"] == "claude-code"

    @patch("agf.workflow.task_handler.AgentRunner")
    @patch("agf.workflow.task_handler.mk_worktree")
    def test_handle_task_with_worktree_agent_override(
        self,
        mock_mk_worktree,
        mock_agent_runner,
        mock_task_manager,
        sample_task,
    ):
        """Test that handle_task uses worktree.agent override throughout execution."""
        # Create config with multiple agents
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
                "opencode": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path("/tmp/tasks.md"), project_dir=Path("/tmp/project")
        )
        config = EffectiveConfig(
            worktrees=agf_config.worktrees,
            concurrent_tasks=agf_config.concurrent_tasks,
            agents=agf_config.agents,
            tasks_file=cli_config.tasks_file,
            project_dir=cli_config.project_dir,
            agf_config=None,
            sync_interval=30,
            dry_run=False,
            single_run=False,
            testing=False,
            install_only=False,
            agent=agf_config.agent,
            model_type=agf_config.model_type,
            branch_prefix=None,
            commands_namespace="agf",
        )

        handler = WorkflowTaskHandler(config, mock_task_manager)

        # Create worktree with agent override
        worktree_with_agent = Worktree(
            worktree_name="test-feature", agent="opencode"
        )

        # Add feature tag to task
        sample_task.tags = ["feature"]

        # Mock successful agent execution for all three phases
        feature_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="opencode",
            json_output={"path": "specs/abc123-feature-test.md"},
        )
        implement_result = AgentResult(
            success=True,
            output="Task completed",
            exit_code=0,
            duration_seconds=10.0,
            agent_name="opencode",
        )
        commit_result = AgentResult(
            success=True,
            output="",
            exit_code=0,
            duration_seconds=5.0,
            agent_name="opencode",
            json_output={"commit_sha": "abc123def456"},
        )
        mock_agent_runner.run_command.side_effect = [
            feature_result,
            implement_result,
            commit_result,
        ]

        # Mock task_manager.get_worktree to return worktree with incomplete tasks
        # so PR creation is not triggered
        worktree_with_incomplete_tasks = Worktree(
            worktree_name="test-feature",
            tasks=[
                Task(
                    task_id="abc123",
                    description="Test task description",
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    task_id="def456",
                    description="Another task",
                    status=TaskStatus.NOT_STARTED,
                ),
            ],
        )
        mock_task_manager.get_worktree.return_value = worktree_with_incomplete_tasks

        # Mock worktree doesn't exist yet
        with patch("os.path.exists", return_value=False):
            result = handler.handle_task(worktree_with_agent, sample_task)

        # Verify success
        assert result is True

        # Verify all agent calls used opencode agent
        assert mock_agent_runner.run_command.call_count == 3
        for call in mock_agent_runner.run_command.call_args_list:
            assert call[1]["agent_name"] == "opencode"
