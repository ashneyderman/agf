"""Configuration models for Agentic Flow system.

This module defines the configuration models for the multi-level configuration system:
- AGFConfig: System-wide configuration loaded from YAML files
- CLIConfig: Runtime configuration from command-line arguments
- AgentModelConfig: Model mappings for a single agent
- EffectiveConfig: Merged configuration with resolved values

Configuration precedence: CLI Arguments > AGF Config File > Hardcoded Defaults
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentModelConfig(BaseModel):
    """Model mappings for a single agent.

    Each agent can define its own mapping from abstract model types
    (thinking, standard, light) to concrete model identifiers.

    Example:
        ```python
        config = AgentModelConfig(
            thinking="opus",
            standard="sonnet",
            light="haiku"
        )
        ```

    YAML example:
        ```yaml
        claude-code:
          thinking: opus
          standard: sonnet
          light: haiku
        ```
    """

    thinking: str
    standard: str
    light: str


class AGFConfig(BaseModel):
    """System-wide configuration for Agentic Flow.

    This configuration is typically loaded from a YAML file (e.g., .agf.yaml)
    and defines system-wide defaults that can be overridden by CLI arguments.

    Fields:
        worktrees: Directory path for storing git worktrees (default: ".worktrees")
        concurrent_tasks: Maximum number of concurrent tasks (default: 5)
        agent: Default agent to use (default: "claude-code")
        model_type: Default model type (default: "standard")
        agents: Dictionary mapping agent names to their model configurations

    Example:
        ```python
        config = AGFConfig.default()
        # or
        config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=10,
            agent="opencode",
            model_type="thinking"
        )
        ```

    YAML example:
        ```yaml
        worktrees: .worktrees
        concurrent-tasks: 5
        agent: claude-code
        model-type: standard
        agents:
          claude-code:
            thinking: opus
            standard: sonnet
            light: haiku
        ```
    """

    model_config = ConfigDict(populate_by_name=True)

    worktrees: str = ".worktrees"
    concurrent_tasks: int = Field(default=5, alias="concurrent-tasks")
    agent: str = "claude-code"
    model_type: str = Field(default="standard", alias="model-type")
    agents: dict[str, AgentModelConfig] = Field(default_factory=dict)

    @field_validator("concurrent_tasks")
    @classmethod
    def validate_concurrent_tasks(cls, v: int) -> int:
        """Validate that concurrent_tasks is positive."""
        if v <= 0:
            raise ValueError("concurrent_tasks must be positive")
        return v

    @classmethod
    def default(cls) -> "AGFConfig":
        """Create an AGFConfig instance with all default values.

        Returns:
            AGFConfig instance with hardcoded defaults including
            default agent configurations for claude-code and opencode.
        """
        return cls(
            worktrees=".worktrees",
            concurrent_tasks=5,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                ),
                "opencode": AgentModelConfig(
                    thinking="github-copilot/claude-opus-4.5",
                    standard="github-copilot/claude-sonnet-4.5",
                    light="github-copilot/claude-haiku-4.5",
                ),
            },
        )


class CLIConfig(BaseModel):
    """Runtime configuration from command-line arguments.

    This model collects all CLI arguments for trigger scripts, including
    optional overrides for agent and model type that take precedence over
    AGF config file settings.

    Fields:
        tasks_file: Path to the tasks markdown file (required)
        project_dir: Root directory of the project (required)
        agf_config: Path to AGF config file (optional)
        sync_interval: Interval in seconds between task discovery runs (default: 30)
        dry_run: Read-only mode flag (default: False)
        single_run: Run once and exit flag (default: False)
        agent: Agent override (None means use AGF config, default: None)
        model_type: Model type override (None means use AGF config, default: None)

    Example:
        ```python
        config = CLIConfig(
            tasks_file=Path("./tasks.md"),
            project_dir=Path("."),
            sync_interval=60,
            agent="opencode"  # Override AGF config
        )
        ```
    """

    tasks_file: Path
    project_dir: Path
    agf_config: Path | None = None
    sync_interval: int = 30
    dry_run: bool = False
    single_run: bool = False
    agent: str | None = None
    model_type: str | None = None

    @field_validator("sync_interval")
    @classmethod
    def validate_sync_interval(cls, v: int) -> int:
        """Validate that sync_interval is positive."""
        if v <= 0:
            raise ValueError("sync_interval must be positive")
        return v


class EffectiveConfig(BaseModel):
    """Effective configuration after merging AGF config and CLI config.

    This model represents the final, resolved configuration with all values
    determined according to the precedence rules: CLI > AGF config > defaults.

    Fields from AGFConfig:
        worktrees: Directory path for storing git worktrees
        concurrent_tasks: Maximum number of concurrent tasks
        agents: Dictionary mapping agent names to their model configurations

    Fields from CLIConfig:
        tasks_file: Path to the tasks markdown file
        project_dir: Root directory of the project
        agf_config: Path to AGF config file (if used)
        sync_interval: Interval in seconds between task discovery runs
        dry_run: Read-only mode flag
        single_run: Run once and exit flag

    Resolved fields (after applying precedence):
        agent: Final agent to use (CLI override or AGF config)
        model_type: Final model type to use (CLI override or AGF config)

    Example:
        ```python
        from agf.config import merge_configs, AGFConfig, CLIConfig

        agf_config = AGFConfig.default()
        cli_config = CLIConfig(
            tasks_file=Path("tasks.md"),
            project_dir=Path("."),
            agent="opencode"  # Override
        )

        effective = merge_configs(agf_config, cli_config)
        print(f"Using agent: {effective.agent}")  # "opencode"
        ```
    """

    # From AGFConfig
    worktrees: str
    concurrent_tasks: int
    agents: dict[str, AgentModelConfig]

    # From CLIConfig
    tasks_file: Path
    project_dir: Path
    agf_config: Path | None
    sync_interval: int
    dry_run: bool
    single_run: bool

    # Resolved values (after precedence)
    agent: str
    model_type: str
