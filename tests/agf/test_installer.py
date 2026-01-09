import pytest
from pathlib import Path
from unittest.mock import Mock

from agf.installer import Installer
from agf.config.models import EffectiveConfig, AgentModelConfig
from agf.task_manager.models import Worktree, Task, TaskStatus


@pytest.fixture
def mock_effective_config():
    """Fixture providing a mock EffectiveConfig"""
    return EffectiveConfig(
        # From AGFConfig
        worktrees=".worktrees",
        concurrent_tasks=5,
        agents={
            "claude-code": AgentModelConfig(
                thinking="opus",
                standard="sonnet",
                light="haiku"
            )
        },
        # From CLIConfig
        tasks_file=Path("./tasks.md"),
        project_dir=Path("."),
        agf_config=None,
        sync_interval=30,
        dry_run=False,
        single_run=False,
        testing=False,
        # Resolved values
        agent="claude-code",
        model_type="standard",
        branch_prefix=None,
        commands_namespace="agf"
    )


@pytest.fixture
def mock_worktree():
    """Fixture providing a mock Worktree"""
    task1 = Task(
        task_id="task1a",
        description="Test task 1",
        status=TaskStatus.NOT_STARTED,
        sequence_number=0
    )
    task2 = Task(
        task_id="task2b",
        description="Test task 2",
        status=TaskStatus.NOT_STARTED,
        sequence_number=1
    )
    return Worktree(
        worktree_name="test-worktree",
        worktree_id="wt123",
        tasks=[task1, task2],
        directory_path="/path/to/worktree",
        head_sha="abc123"
    )


class TestInstallerInstantiation:
    """Tests for Installer instantiation"""

    def test_installer_can_be_instantiated(self, mock_effective_config, mock_worktree):
        """Test that Installer can be instantiated with config and worktree"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        assert installer is not None
        assert isinstance(installer, Installer)

    def test_installer_stores_config_reference(self, mock_effective_config, mock_worktree):
        """Test that Installer stores the config reference correctly"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        assert installer._config is mock_effective_config

    def test_installer_stores_worktree_reference(self, mock_effective_config, mock_worktree):
        """Test that Installer stores the worktree reference correctly"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        assert installer._worktree is mock_worktree


class TestInstallerProperties:
    """Tests for Installer property methods"""

    def test_config_property_returns_effective_config(self, mock_effective_config, mock_worktree):
        """Test that config property returns the correct EffectiveConfig instance"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer.config

        assert result is mock_effective_config
        assert isinstance(result, EffectiveConfig)
        assert result.agent == "claude-code"
        assert result.worktrees == ".worktrees"

    def test_worktree_property_returns_worktree(self, mock_effective_config, mock_worktree):
        """Test that worktree property returns the correct Worktree instance"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer.worktree

        assert result is mock_worktree
        assert isinstance(result, Worktree)
        assert result.worktree_name == "test-worktree"
        assert result.worktree_id == "wt123"
        assert len(result.tasks) == 2
