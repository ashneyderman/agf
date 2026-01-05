"""Multi-level configuration system for Agentic Flow.

This package provides a hierarchical configuration system with three layers:

1. Hardcoded Defaults (lowest priority)
   - Defined in code as fallbacks
   - Ensures system always has valid configuration

2. AGF Config File (medium priority)
   - Loaded from .agf.yaml or agf.yaml
   - Defines project-specific defaults
   - Can be version-controlled with project

3. CLI Arguments (highest priority)
   - Specified at runtime via command-line options
   - Allows per-invocation overrides

Configuration precedence: CLI Arguments > AGF Config File > Hardcoded Defaults

Usage:
    ```python
    from agf.config import (
        AGFConfig,
        CLIConfig,
        load_agf_config_from_file,
        find_agf_config,
        merge_configs
    )

    # Load AGF config from file
    agf_config = load_agf_config_from_file(Path(".agf.yaml"))

    # Or discover config file automatically
    config_path = find_agf_config(Path.cwd())
    if config_path:
        agf_config = load_agf_config_from_file(config_path)
    else:
        agf_config = AGFConfig.default()

    # Create CLI config from arguments
    cli_config = CLIConfig(
        tasks_file=Path("tasks.md"),
        project_dir=Path("."),
        agent="opencode"  # Override AGF config
    )

    # Merge configurations
    config = merge_configs(agf_config, cli_config)
    print(f"Using agent: {config['agent']}")
    ```
"""

from .loader import find_agf_config, load_agf_config_from_file, merge_configs
from .models import AGFConfig, AgentModelConfig, CLIConfig, EffectiveConfig

__all__ = [
    "AGFConfig",
    "CLIConfig",
    "AgentModelConfig",
    "EffectiveConfig",
    "load_agf_config_from_file",
    "find_agf_config",
    "merge_configs",
]
