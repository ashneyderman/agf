"""Installer for managing package installation operations in Agentic Flow system."""

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
