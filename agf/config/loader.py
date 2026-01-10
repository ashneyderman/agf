"""Configuration loading and merging utilities.

This module provides functions for:
- Loading AGF configuration from YAML files
- Discovering configuration files in the directory hierarchy
- Merging AGF config with CLI config according to precedence rules
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import AGFConfig, CLIConfig, EffectiveConfig


def load_agf_config_from_file(path: Path) -> AGFConfig:
    """Load AGFConfig from a YAML file.

    Args:
        path: Path to the YAML configuration file

    Returns:
        AGFConfig instance parsed from the YAML file

    Raises:
        FileNotFoundError: If the config file does not exist
        yaml.YAMLError: If the YAML is malformed
        ValidationError: If the YAML doesn't match the AGFConfig schema

    Example:
        ```python
        config = load_agf_config_from_file(Path(".agf.yaml"))
        print(f"Default agent: {config.agent}")
        ```
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML from {path}: {e}") from e

    if data is None:
        # Empty YAML file, use defaults
        data = {}

    try:
        return AGFConfig(**data)
    except ValidationError as e:
        raise ValidationError(
            f"Configuration file {path} has validation errors: {e}"
        ) from e


def find_agf_config(start_dir: Path) -> Path | None:
    """Find AGF configuration file by searching parent directories.

    Searches for .agf.yaml or agf.yaml starting from start_dir and moving
    up the directory tree. Stops at git repository root or filesystem root.

    Args:
        start_dir: Directory to start searching from

    Returns:
        Path to the first config file found, or None if not found

    Search order:
        1. .agf.yaml in current directory
        2. agf.yaml in current directory
        3. Repeat in parent directories up to git root or filesystem root

    Example:
        ```python
        config_path = find_agf_config(Path.cwd())
        if config_path:
            config = load_agf_config_from_file(config_path)
        ```
    """
    current = start_dir.resolve()

    # Search up to filesystem root
    while True:
        # Check for .agf.yaml first (hidden file convention)
        dotfile = current / ".agf.yaml"
        if dotfile.exists() and dotfile.is_file():
            return dotfile

        # Check for agf.yaml (visible file)
        visible = current / "agf.yaml"
        if visible.exists() and visible.is_file():
            return visible

        # Check if we've hit a git repository root
        if (current / ".git").exists():
            break

        # Check if we've hit filesystem root
        parent = current.parent
        if parent == current:
            break

        current = parent

    return None


def merge_configs(agf_config: AGFConfig, cli_config: CLIConfig) -> EffectiveConfig:
    """Merge AGF config and CLI config with proper precedence.

    Configuration precedence (highest to lowest):
    1. CLI arguments (from CLIConfig)
    2. AGF config file (from AGFConfig)
    3. Hardcoded defaults (already in AGFConfig)

    The merged result includes all fields from both configs. For agent and
    model_type, CLI values override AGF config values when specified.

    Args:
        agf_config: System-wide configuration from YAML file
        cli_config: Runtime configuration from CLI arguments

    Returns:
        EffectiveConfig with merged configuration values

    Example:
        ```python
        agf_config = AGFConfig.default()
        cli_config = CLIConfig(
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agent="opencode"  # Override
        )
        effective = merge_configs(agf_config, cli_config)
        # effective.agent == "opencode" (CLI wins)
        # effective.model_type == "standard" (from AGF config)
        ```
    """
    # Apply precedence for agent: CLI > AGF config
    resolved_agent = cli_config.agent if cli_config.agent is not None else agf_config.agent

    # Apply precedence for model_type: CLI > AGF config
    resolved_model_type = (
        cli_config.model_type if cli_config.model_type is not None else agf_config.model_type
    )

    # Apply precedence for branch_prefix: CLI > AGF config
    resolved_branch_prefix = (
        cli_config.branch_prefix if cli_config.branch_prefix is not None else agf_config.branch_prefix
    )

    # Apply precedence for commands_namespace: CLI > AGF config
    resolved_commands_namespace = (
        cli_config.commands_namespace if cli_config.commands_namespace is not None else agf_config.commands_namespace
    )

    return EffectiveConfig(
        # From AGFConfig
        worktrees=agf_config.worktrees,
        concurrent_tasks=agf_config.concurrent_tasks,
        agents=agf_config.agents,
        # From CLIConfig
        tasks_file=cli_config.tasks_file,
        project_dir=cli_config.project_dir,
        agf_config=cli_config.agf_config,
        sync_interval=cli_config.sync_interval,
        dry_run=cli_config.dry_run,
        single_run=cli_config.single_run,
        testing=cli_config.testing,
        # Resolved values
        agent=resolved_agent,
        model_type=resolved_model_type,
        branch_prefix=resolved_branch_prefix,
        commands_namespace=resolved_commands_namespace,
    )
