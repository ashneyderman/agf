import pytest
import os
import time
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


class TestInstallerPathResolution:
    """Tests for path resolution methods"""

    def test_get_agf_commands_source_dir_returns_valid_path(self, mock_effective_config, mock_worktree):
        """Test that _get_agf_commands_source_dir returns a valid path"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer._get_agf_commands_source_dir()

        assert isinstance(result, Path)
        assert result.name == "agf_commands"
        assert result.exists()
        assert result.is_dir()

    def test_get_target_commands_dir_for_claude_code(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _get_target_commands_dir returns correct path for claude-code"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.agent = "claude-code"
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer._get_target_commands_dir()

        assert isinstance(result, Path)
        assert str(result) == str(tmp_path / ".claude" / "commands" / "agf")

    def test_get_target_commands_dir_for_opencode(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _get_target_commands_dir returns correct path for opencode"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.agent = "opencode"
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer._get_target_commands_dir()

        assert isinstance(result, Path)
        assert str(result) == str(tmp_path / ".opencode" / "command" / "agf")

    def test_get_target_commands_dir_with_custom_namespace(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _get_target_commands_dir uses custom namespace"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.agent = "claude-code"
        mock_effective_config.commands_namespace = "custom"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer._get_target_commands_dir()

        assert isinstance(result, Path)
        assert str(result) == str(tmp_path / ".claude" / "commands" / "custom")

    def test_get_target_commands_dir_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that _get_target_commands_dir raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer._get_target_commands_dir()


class TestInstallerFileComparison:
    """Tests for file comparison logic"""

    def test_is_file_outdated_when_target_does_not_exist(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _is_file_outdated returns True when target doesn't exist"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)
        source = tmp_path / "source.md"
        source.write_text("content")
        target = tmp_path / "target.md"

        result = installer._is_file_outdated(source, target)

        assert result is True

    def test_is_file_outdated_when_source_is_newer(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _is_file_outdated returns True when source is newer than target"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Create target first (older)
        target = tmp_path / "target.md"
        target.write_text("old content")
        time.sleep(0.01)  # Ensure time difference

        # Create source later (newer)
        source = tmp_path / "source.md"
        source.write_text("new content")

        result = installer._is_file_outdated(source, target)

        assert result is True

    def test_is_file_outdated_when_target_is_newer(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _is_file_outdated returns False when target is newer than source"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Create source first (older)
        source = tmp_path / "source.md"
        source.write_text("content")
        time.sleep(0.01)  # Ensure time difference

        # Create target later (newer)
        target = tmp_path / "target.md"
        target.write_text("content")

        result = installer._is_file_outdated(source, target)

        assert result is False

    def test_is_file_outdated_when_files_have_same_mtime(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _is_file_outdated returns False when files have same modification time"""
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        source = tmp_path / "source.md"
        source.write_text("content")

        target = tmp_path / "target.md"
        target.write_text("content")

        # Set same modification time
        mtime = os.path.getmtime(source)
        os.utime(target, (mtime, mtime))

        result = installer._is_file_outdated(source, target)

        assert result is False


class TestInstallerInstallCommands:
    """Tests for command installation"""

    def test_install_commands_creates_target_directory(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands creates target directory if it doesn't exist"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        target_dir = tmp_path / ".claude" / "commands" / "agf"
        assert not target_dir.exists()

        installer.install_commands()

        assert target_dir.exists()
        assert target_dir.is_dir()

    def test_install_commands_copies_md_files(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands copies .md files from source to target"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        target_dir = tmp_path / ".claude" / "commands" / "agf"

        result = installer.install_commands()

        # Should have copied multiple .md files
        assert len(result) > 0
        assert all(f.endswith(".md") for f in result)

        # Verify files exist in target
        for filename in result:
            assert (target_dir / filename).exists()

    def test_install_commands_returns_copied_files(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands returns list of copied files"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        result = installer.install_commands()

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(f, str) for f in result)

    def test_install_commands_skips_up_to_date_files(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands skips files that are already up-to-date"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First installation
        result1 = installer.install_commands()
        assert len(result1) > 0

        # Second installation - should skip all files
        result2 = installer.install_commands()
        assert len(result2) == 0

    def test_install_commands_updates_outdated_files(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands updates files when source is newer"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First installation
        result1 = installer.install_commands()
        first_install_count = len(result1)

        # Make source files appear newer by modifying one file
        source_dir = installer._get_agf_commands_source_dir()
        source_files = list(source_dir.glob("*.md"))
        if source_files:
            test_file = source_files[0]
            # Touch the file to make it newer
            test_file.touch()

            # Second installation - should copy the touched file
            result2 = installer.install_commands()
            assert len(result2) >= 1
            assert test_file.name in result2

    def test_install_commands_preserves_timestamps(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that install_commands preserves file timestamps"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        source_dir = installer._get_agf_commands_source_dir()
        source_files = list(source_dir.glob("*.md"))

        installer.install_commands()

        target_dir = installer._get_target_commands_dir()

        # Check that at least one file has matching timestamp
        for source_file in source_files[:1]:  # Check first file
            target_file = target_dir / source_file.name
            if target_file.exists():
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                # Allow small difference due to filesystem precision
                assert abs(source_mtime - target_mtime) < 0.01

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

    def test_ensure_gitignore_entry_adds_entry_for_claude_code(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry adds correct entry for claude-code"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.agent = "claude-code"
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        content = gitignore_path.read_text()
        assert ".claude/commands/agf/" in content

    def test_ensure_gitignore_entry_adds_entry_for_opencode(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry adds correct entry for opencode"""
        mock_worktree.directory_path = str(tmp_path)
        mock_effective_config.agent = "opencode"
        mock_effective_config.commands_namespace = "agf"
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        content = gitignore_path.read_text()
        assert ".opencode/command/agf/" in content

    def test_ensure_gitignore_entry_does_not_duplicate_entry(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry doesn't duplicate existing entry"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # First installation
        installer.install_commands()

        gitignore_path = tmp_path / ".gitignore"
        content1 = gitignore_path.read_text()
        count1 = content1.count(".claude/commands/agf/")

        # Second installation
        installer.install_commands()

        content2 = gitignore_path.read_text()
        count2 = content2.count(".claude/commands/agf/")

        # Should still have only one entry
        assert count1 == 1
        assert count2 == 1

    def test_ensure_gitignore_entry_handles_entry_without_trailing_slash(self, mock_effective_config, mock_worktree, tmp_path):
        """Test that _ensure_gitignore_entry handles existing entry without trailing slash"""
        mock_worktree.directory_path = str(tmp_path)
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        # Pre-create .gitignore with entry without trailing slash
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text(".claude/commands/agf\n")

        installer.install_commands()

        content = gitignore_path.read_text()
        # Should not add duplicate
        assert content.count(".claude/commands/agf") == 1

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
        # Should have existing entry, new entry, and possibly empty string at end
        assert "existing_entry" in lines
        assert ".claude/commands/agf/" in lines

    def test_ensure_gitignore_entry_raises_when_directory_path_is_none(self, mock_effective_config, mock_worktree):
        """Test that _ensure_gitignore_entry raises ValueError when directory_path is None"""
        mock_worktree.directory_path = None
        installer = Installer(config=mock_effective_config, worktree=mock_worktree)

        with pytest.raises(ValueError, match="Worktree directory_path cannot be None"):
            installer._ensure_gitignore_entry()
