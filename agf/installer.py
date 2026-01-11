"""Installer for managing package installation operations in Agentic Flow system."""

import os
import shutil
from pathlib import Path

from agf.config.models import EffectiveConfig
from agf.task_manager.models import Worktree


class Installer:
    """
    Manages installation operations for the Agentic Flow system.

    This class serves as the foundation for installation capabilities,
    maintaining references to the effective configuration and worktree
    context needed for installation operations.

    Attributes:
        _config: The effective configuration for the system
        _worktree: The worktree context for installation operations
    """

    def __init__(self, config: EffectiveConfig, worktree: Worktree):
        """
        Initialize Installer with configuration and worktree references.

        Args:
            config: EffectiveConfig instance containing merged configuration
            worktree: Worktree instance representing the git worktree context
        """
        self._config = config
        self._worktree = worktree

    @property
    def config(self) -> EffectiveConfig:
        """
        Get the effective configuration.

        Returns:
            EffectiveConfig instance
        """
        return self._config

    @property
    def worktree(self) -> Worktree:
        """
        Get the worktree context.

        Returns:
            Worktree instance
        """
        return self._worktree

    def _get_agf_config_source_dir(self) -> Path:
        """
        Get the path to the AGF config source directory.

        Returns:
            Path to the .agf_config directory in the AGF project
        """
        # __file__ points to agf/installer.py, so go up one level to agf package,
        # then up one more level to the project root, then into .agf_config
        return Path(__file__).parent.parent / ".agf_config"

    def _copy_agf_config(self) -> None:
        """
        Copy the entire .agf_config directory to the worktree's .agf directory.

        Raises:
            ValueError: If worktree directory_path is None
        """
        if self._worktree.directory_path is None:
            raise ValueError("Worktree directory_path cannot be None")

        source_dir = self._get_agf_config_source_dir()
        worktree_path = Path(self._worktree.directory_path)
        target_dir = worktree_path / ".agf"

        # Remove existing .agf directory if it exists
        if target_dir.exists():
            shutil.rmtree(target_dir)

        # Copy the entire directory structure
        shutil.copytree(source_dir, target_dir)

    def _create_command_symlinks(self) -> None:
        """
        Create symbolic links from agent command directories to .agf structure.

        Creates symlinks for both claude-code and opencode agents, pointing their
        command directories to the corresponding paths in .agf.

        Raises:
            ValueError: If worktree directory_path is None
        """
        if self._worktree.directory_path is None:
            raise ValueError("Worktree directory_path cannot be None")

        worktree_path = Path(self._worktree.directory_path)
        namespace = self._config.commands_namespace

        # Define symlink mappings: (parent_dir, link_name, target_relative_path)
        symlinks = [
            (
                worktree_path / ".claude" / "commands",
                namespace,
                "../../.agf/claude/commands"
            ),
            (
                worktree_path / ".opencode" / "command",
                namespace,
                "../../.agf/opencode/commands"
            ),
        ]

        for parent_dir, link_name, target_path in symlinks:
            # Create parent directory if it doesn't exist
            parent_dir.mkdir(parents=True, exist_ok=True)

            link_path = parent_dir / link_name

            # Remove existing symlink if it exists
            if link_path.is_symlink() or link_path.exists():
                if link_path.is_symlink():
                    link_path.unlink()
                elif link_path.is_dir():
                    shutil.rmtree(link_path)
                else:
                    link_path.unlink()

            # Create the symlink using relative path
            os.symlink(target_path, link_path)

    def install_commands(self) -> None:
        """
        Install AGF command prompts to the worktree using symlink-based approach.

        This method:
        1. Copies the entire .agf_config directory to {worktree}/.agf
        2. Creates symlinks from agent command directories to .agf structure
        3. Updates .gitignore with all required entries

        Raises:
            ValueError: If worktree directory_path is None
        """
        # Copy the config directory
        self._copy_agf_config()

        # Create symlinks for both agents
        self._create_command_symlinks()

        # Update gitignore with all entries
        self._ensure_gitignore_entry()

    def _gitignore_has_entry(self, gitignore_path: Path, entry: str) -> bool:
        """
        Check if .gitignore contains the specified entry.

        Args:
            gitignore_path: Path to the .gitignore file
            entry: The gitignore entry to check for

        Returns:
            True if entry exists (with or without trailing slash), False otherwise
        """
        if not gitignore_path.exists():
            return False

        with open(gitignore_path, "r") as f:
            existing_entries = {line.strip() for line in f}

        # Normalize entry for comparison (with and without trailing slash)
        entry_normalized = entry.rstrip("/")

        # Check if entry already exists (in any form)
        return any(
            existing.rstrip("/") == entry_normalized
            for existing in existing_entries
        )

    def _add_gitignore_entries(self, gitignore_path: Path, entries: list[str]) -> None:
        """
        Add multiple entries to .gitignore file.

        Args:
            gitignore_path: Path to the .gitignore file
            entries: List of entries to add (duplicates will be skipped)
        """
        # Filter out entries that already exist
        entries_to_add = [
            entry for entry in entries
            if not self._gitignore_has_entry(gitignore_path, entry)
        ]

        if not entries_to_add:
            return

        with open(gitignore_path, "a") as f:
            # Add newline before entries if file exists and doesn't end with newline
            if gitignore_path.exists() and gitignore_path.stat().st_size > 0:
                with open(gitignore_path, "rb") as rf:
                    rf.seek(-1, 2)  # Seek to last byte
                    last_char = rf.read(1)
                    if last_char != b"\n":
                        f.write("\n")

            # Add all entries
            for entry in entries_to_add:
                entry_with_slash = entry if entry.endswith("/") else entry + "/"
                f.write(f"{entry_with_slash}\n")

    def _ensure_gitignore_entry(self) -> None:
        """
        Ensure all required directories are listed in .gitignore.

        Adds entries for .agf/, .claude/commands/{namespace}/, and
        .opencode/command/{namespace}/ to the worktree's .gitignore file.

        Raises:
            ValueError: If worktree directory_path is None
        """
        if self._worktree.directory_path is None:
            raise ValueError("Worktree directory_path cannot be None")

        worktree_path = Path(self._worktree.directory_path)
        gitignore_path = worktree_path / ".gitignore"
        namespace = self._config.commands_namespace

        # Define all entries to add
        entries = [
            ".agf/",
            f".claude/commands/{namespace}/",
            f".opencode/command/{namespace}/",
        ]

        self._add_gitignore_entries(gitignore_path, entries)
