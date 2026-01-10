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

    def _get_agf_commands_source_dir(self) -> Path:
        """
        Get the path to the AGF commands source directory.

        Returns:
            Path to the agf_commands directory in the AGF project
        """
        # __file__ points to agf/installer.py, so go up one level to agf package,
        # then up one more level to the project root, then into agf_commands
        return Path(__file__).parent.parent / "agf_commands"

    def _get_target_commands_dir(self) -> Path:
        """
        Get the target directory path for commands based on agent type and configuration.

        Returns:
            Path to the target commands directory in the worktree

        Raises:
            ValueError: If worktree directory_path is None
        """
        if self._worktree.directory_path is None:
            raise ValueError("Worktree directory_path cannot be None")

        worktree_path = Path(self._worktree.directory_path)
        agent = self._config.agent
        namespace = self._config.commands_namespace

        # Determine agent-specific directory structure
        if agent == "claude-code":
            agent_dir = ".claude/commands"
        elif agent == "opencode":
            agent_dir = ".opencode/command"
        else:
            # Default to claude-code structure for unknown agents
            agent_dir = ".claude/commands"

        return worktree_path / agent_dir / namespace

    def _is_file_outdated(self, source_path: Path, target_path: Path) -> bool:
        """
        Check if a target file is missing or outdated compared to the source.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file

        Returns:
            True if target doesn't exist or is older than source, False otherwise
        """
        # If target doesn't exist, it's outdated
        if not target_path.exists():
            return True

        # Compare modification times - if source is newer, target is outdated
        source_mtime = os.path.getmtime(source_path)
        target_mtime = os.path.getmtime(target_path)

        return source_mtime > target_mtime

    def install_commands(self) -> list[str]:
        """
        Install AGF command prompts to the worktree's agent-specific commands directory.

        This method synchronizes command files from the AGF source directory to the
        worktree's commands directory, copying only files that are missing or outdated.

        Returns:
            List of filenames that were copied to the target directory

        Raises:
            ValueError: If worktree directory_path is None
        """
        source_dir = self._get_agf_commands_source_dir()
        target_dir = self._get_target_commands_dir()

        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        copied_files: list[str] = []

        # Iterate over all .md files in source directory
        for source_file in source_dir.glob("*.md"):
            target_file = target_dir / source_file.name

            # Check if file needs to be copied
            if self._is_file_outdated(source_file, target_file):
                # Copy file, preserving timestamps
                shutil.copy2(source_file, target_file)
                copied_files.append(source_file.name)

        # Update .gitignore after successful installation
        if copied_files:
            self._ensure_gitignore_entry()

        return copied_files

    def _ensure_gitignore_entry(self) -> None:
        """
        Ensure the agent-specific commands directory is listed in .gitignore.

        This method checks if the commands directory entry exists in the worktree's
        .gitignore file and adds it if missing.

        Raises:
            ValueError: If worktree directory_path is None
        """
        if self._worktree.directory_path is None:
            raise ValueError("Worktree directory_path cannot be None")

        worktree_path = Path(self._worktree.directory_path)
        gitignore_path = worktree_path / ".gitignore"

        # Determine the entry to add based on agent type
        agent = self._config.agent
        namespace = self._config.commands_namespace

        if agent == "claude-code":
            entry = f".claude/commands/{namespace}/"
        elif agent == "opencode":
            entry = f".opencode/command/{namespace}/"
        else:
            # Default to claude-code structure
            entry = f".claude/commands/{namespace}/"

        # Check if .gitignore exists and read its contents
        existing_entries = set()
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                existing_entries = {line.strip() for line in f}

        # Normalize entry for comparison (with and without trailing slash)
        entry_normalized = entry.rstrip("/")
        entry_with_slash = entry if entry.endswith("/") else entry + "/"

        # Check if entry already exists (in any form)
        entry_exists = any(
            existing.rstrip("/") == entry_normalized
            for existing in existing_entries
        )

        # Add entry if it doesn't exist
        if not entry_exists:
            with open(gitignore_path, "a") as f:
                # Add newline before entry if file exists and doesn't end with newline
                if gitignore_path.stat().st_size > 0:
                    with open(gitignore_path, "rb") as rf:
                        rf.seek(-1, 2)  # Seek to last byte
                        last_char = rf.read(1)
                        if last_char != b"\n":
                            f.write("\n")
                f.write(f"{entry_with_slash}\n")
