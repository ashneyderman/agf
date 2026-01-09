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
        assert command_template.model == "standard"
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
        assert command_template.model == "standard"
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
