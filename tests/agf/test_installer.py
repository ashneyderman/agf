import pytest
from pathlib import Path

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


class TestInstallerPathResolution:
    """Tests for path resolution methods"""

    def test_get_agf_config_source_dir_returns_valid_path(self, mock_effective_config, mock_worktree):
        """Test that _get_agf_config_source_dir returns a valid path"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer._get_agf_config_source_dir()

        assert isinstance(result, Path)
        assert result.name == ".agf_config"
        assert result.exists()
        assert result.is_dir()


class TestInstallerDirectoryCopy:
    """Tests for directory copy logic"""

    def test_copy_agf_config_creates_target_directory(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _copy_agf_config creates .agf directory"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        target_dir = tmp_path / ".agf"
        assert not target_dir.exists()

        installer._copy_agf_config()

        assert target_dir.exists()
        assert target_dir.is_dir()

    def test_copy_agf_config_copies_directory_structure(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _copy_agf_config copies the directory structure correctly"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer._copy_agf_config()

        target_dir = tmp_path / ".agf"
        assert (target_dir / "claude" / "commands").exists()
        assert (target_dir / "opencode" / "commands").exists()

        # Check that some command files exist
        claude_commands = list((target_dir / "claude" / "commands").glob("*.md"))
        assert len(claude_commands) > 0

        opencode_commands = list((target_dir / "opencode" / "commands").glob("*.md"))
        assert len(opencode_commands) > 0

    def test_copy_agf_config_replaces_existing_directory(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _copy_agf_config removes and replaces existing .agf directory"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Create existing .agf directory with a marker file
        target_dir = tmp_path / ".agf"
        target_dir.mkdir()
        marker_file = target_dir / "marker.txt"
        marker_file.write_text("old content")

        installer._copy_agf_config()

        # Marker file should be gone
        assert not marker_file.exists()
        # But new structure should be there
        assert (target_dir / "claude" / "commands").exists()

    def test_copy_agf_config_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that _copy_agf_config raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer._copy_agf_config()


class TestInstallerSymlinks:
    """Tests for symlink creation logic"""

    def test_create_command_symlinks_creates_claude_symlink(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _create_command_symlinks creates claude-code symlink"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First copy the config so the target exists
        installer._copy_agf_config()
        installer._create_command_symlinks()

        symlink_path = tmp_path / ".claude" / "commands" / "agf"
        assert symlink_path.is_symlink()
        # Verify it points to the right place
        assert symlink_path.resolve() == (tmp_path / ".agf" / "claude" / "commands").resolve()

    def test_create_command_symlinks_creates_opencode_symlink(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _create_command_symlinks creates opencode symlink"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First copy the config so the target exists
        installer._copy_agf_config()
        installer._create_command_symlinks()

        symlink_path = tmp_path / ".opencode" / "command" / "agf"
        assert symlink_path.is_symlink()
        # Verify it points to the right place
        assert symlink_path.resolve() == (tmp_path / ".agf" / "opencode" / "commands").resolve()

    def test_create_command_symlinks_uses_custom_namespace(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _create_command_symlinks uses custom namespace"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "custom"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer._copy_agf_config()
        installer._create_command_symlinks()

        claude_symlink = tmp_path / ".claude" / "commands" / "custom"
        opencode_symlink = tmp_path / ".opencode" / "command" / "custom"

        assert claude_symlink.is_symlink()
        assert opencode_symlink.is_symlink()

    def test_create_command_symlinks_replaces_existing_symlink(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _create_command_symlinks replaces existing symlink"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Create existing symlink pointing elsewhere
        symlink_parent = tmp_path / ".claude" / "commands"
        symlink_parent.mkdir(parents=True)
        old_target = tmp_path / "old_target"
        old_target.mkdir()
        symlink_path = symlink_parent / "agf"
        symlink_path.symlink_to(old_target)

        # Copy config and create symlinks
        installer._copy_agf_config()
        installer._create_command_symlinks()

        # Symlink should now point to new location
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == (tmp_path / ".agf" / "claude" / "commands").resolve()

    def test_create_command_symlinks_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that _create_command_symlinks raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer._create_command_symlinks()


class TestInstallerInstallCommands:
    """Tests for command installation"""

    def test_install_commands_creates_agf_directory(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands creates .agf directory"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        agf_dir = tmp_path / ".agf"
        assert not agf_dir.exists()

        installer.install_commands()

        assert agf_dir.exists()
        assert agf_dir.is_dir()

    def test_install_commands_creates_symlinks(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands creates symlinks for both agents"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer.install_commands()

        claude_symlink = tmp_path / ".claude" / "commands" / "agf"
        opencode_symlink = tmp_path / ".opencode" / "command" / "agf"

        assert claude_symlink.is_symlink()
        assert opencode_symlink.is_symlink()

    def test_install_commands_updates_gitignore(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands updates .gitignore with all entries"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        assert ".agf/" in content
        assert ".claude/commands/agf/" in content
        assert ".opencode/command/agf/" in content

    def test_install_commands_is_idempotent(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands can be run multiple times safely"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First installation
        installer.install_commands()

        # Get initial state
        agf_dir = tmp_path / ".agf"
        initial_files = list(agf_dir.rglob("*.md"))

        # Second installation
        installer.install_commands()

        # Should still have same structure
        final_files = list(agf_dir.rglob("*.md"))
        assert len(initial_files) == len(final_files)

    def test_install_commands_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that install_commands raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer.install_commands()


class TestInstallerGitignore:
    """Tests for .gitignore update logic"""

    def test_ensure_gitignore_entry_creates_file_if_not_exists(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry creates .gitignore if it doesn't exist"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        gitignore_path = tmp_path / ".gitignore"
        assert not gitignore_path.exists()

        # Run install to trigger gitignore update
        installer.install_commands()

        assert gitignore_path.exists()

    def test_ensure_gitignore_entry_adds_all_entries(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry adds all required entries"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        content = gitignore_path.read_text()
        assert ".agf/" in content
        assert ".claude/commands/agf/" in content
        assert ".opencode/command/agf/" in content

    def test_ensure_gitignore_entry_does_not_duplicate_entries(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry doesn't duplicate existing entries"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First installation
        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        content1 = gitignore_path.read_text()
        count1 = content1.count(".agf/")

        # Second installation
        installer.install_commands()

        content2 = gitignore_path.read_text()
        count2 = content2.count(".agf/")

        # Should still have only one entry
        assert count1 == 1
        assert count2 == 1

    def test_ensure_gitignore_entry_handles_entry_without_trailing_slash(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry handles existing entry without trailing slash"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Pre-create .gitignore with entry without trailing slash
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text(".agf\n")

        installer.install_commands()

        content = gitignore_path.read_text()
        # Should not add duplicate
        assert content.count(".agf") == 1

    def test_ensure_gitignore_entry_adds_newline_before_entry_if_needed(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry adds newline before entry if file doesn't end with one"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Pre-create .gitignore without trailing newline
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("existing_entry")

        installer.install_commands()

        content = gitignore_path.read_text()
        lines = content.split("\n")
        # Should have existing entry and new entries
        assert "existing_entry" in lines
        assert ".agf/" in lines

    def test_ensure_gitignore_entry_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that _ensure_gitignore_entry raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer._ensure_gitignore_entry()

    def test_gitignore_has_entry_returns_true_for_existing_entry(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _gitignore_has_entry returns True for existing entry"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text(".agf/\n")

        assert installer._gitignore_has_entry(gitignore_path, ".agf/")
        assert installer._gitignore_has_entry(gitignore_path, ".agf")

    def test_gitignore_has_entry_returns_false_for_missing_entry(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _gitignore_has_entry returns False for missing entry"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("other_entry/\n")

        assert not installer._gitignore_has_entry(gitignore_path, ".agf/")
