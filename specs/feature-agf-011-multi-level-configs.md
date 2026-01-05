# Feature: Multi-Level Configuration System

## Metadata

agf_id: `agf-multi-level-configs`
prompt: `prompts/agf-multi-level-configs.md`

## Feature Description

Implement a flexible multi-level configuration system for Agentic Flow that allows system-wide defaults to be defined in a YAML configuration file, with the ability to override those defaults via command-line arguments. This system will centralize configuration management, support multiple agents with agent-specific model mappings, and provide a consistent configuration interface across all workflows and triggers.

The configuration system will consist of two primary models:
- `AGFConfig`: Represents system-wide configuration loaded from YAML files
- `CLIConfig`: Represents runtime configuration from command-line arguments

These models will work together with a precedence hierarchy: CLI arguments override AGF config file settings, which override hardcoded defaults.

## User Story

As a developer using Agentic Flow
I want to configure system-wide defaults in a YAML file and override them via command-line arguments
So that I can maintain consistent settings across workflows while retaining flexibility for specific invocations

## Problem Statement

Currently, the Agentic Flow system has configuration scattered across multiple locations:
1. Hardcoded defaults in enums (`AgentType`, `ModelType`) in `agf/agent/base.py`
2. Static model mappings in `ModelMapping` class in `agf/agent/base.py`
3. CLI arguments defined in trigger scripts like `agf/triggers/find_and_start_tasks.py`
4. No centralized way to configure system-wide defaults
5. No mechanism to override defaults without modifying code or always specifying CLI arguments

This creates problems when:
- Users want to change the default agent or model type system-wide
- Different projects need different default configurations
- Multiple agents need to be configured with specific model mappings
- Configuration needs to be version-controlled alongside project code
- Teams want to share consistent settings across environments

## Solution Statement

Implement a hierarchical configuration system with three layers:
1. **Hardcoded Defaults**: Lowest priority, defined in code as fallbacks
2. **AGF Config File**: Medium priority, defined in YAML file (e.g., `.agf.yaml`)
3. **CLI Arguments**: Highest priority, specified at runtime

The `AGFConfig` model will:
- Be loaded from a YAML file specified by `--agf-config` CLI option or a default location
- Define system-wide settings: worktrees directory, concurrent tasks limit, default agent, default model type
- Support per-agent model mappings (agent → model-type → concrete-model-name)
- Use Pydantic for validation and type safety
- Provide sensible defaults matching current system behavior

The `CLIConfig` model will:
- Collect all command-line arguments for trigger scripts
- Include optional overrides for agent and model-type
- Support both required arguments (tasks-file, project-dir) and optional settings
- Integrate with existing Click-based CLI in `find_and_start_tasks.py`

Configuration resolution will follow the precedence hierarchy:
```
CLI args > AGF config file > Hardcoded defaults
```

## Relevant Files

Use these files to implement the feature:

- `agf/agent/base.py` - Contains current `AgentType`, `ModelType`, and `ModelMapping` classes that will be integrated with the new config system
- `agf/triggers/find_and_start_tasks.py` - Current trigger script with CLI arguments that will be updated to use `CLIConfig` and load `AGFConfig`
- `sample.agf.yaml` - Sample configuration file that already defines the expected YAML structure

### New Files

- `agf/config/__init__.py` - Package initialization, exports `AGFConfig` and `CLIConfig`
- `agf/config/models.py` - Configuration models (`AGFConfig`, `CLIConfig`, `AgentModelConfig`)
- `agf/config/loader.py` - Configuration loading utilities (YAML parsing, file discovery, merging)
- `tests/config/__init__.py` - Test package initialization
- `tests/config/test_agf_config.py` - Tests for `AGFConfig` model and YAML loading
- `tests/config/test_cli_config.py` - Tests for `CLIConfig` model
- `tests/config/test_config_integration.py` - Integration tests for configuration precedence and merging
- `tests/config/fixtures/` - Directory for test YAML configuration files

## Implementation Plan

### Phase 1: Foundation

Create the `agf/config` package and define the configuration models using Pydantic. These models will mirror the structure shown in `sample.agf.yaml` and the CLI arguments currently in `find_and_start_tasks.py`. This phase establishes the data structures and validation rules.

### Phase 2: Core Implementation

Implement configuration loading from YAML files, configuration merging logic respecting precedence rules, and integration with the existing `ModelMapping` class to support dynamic agent registration from config files.

### Phase 3: Integration

Update `find_and_start_tasks.py` to use the new configuration system, ensuring backward compatibility while enabling the new hierarchical configuration approach. Refactor how agent and model are selected to use the config resolution system.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Configuration Package Structure

- Create directory `agf/config/`
- Create `agf/config/__init__.py` with module docstring
- Create `agf/config/models.py` for configuration models
- Create `agf/config/loader.py` for YAML loading and merging logic
- Create `tests/config/` directory
- Create `tests/config/__init__.py`
- Create `tests/config/fixtures/` for test YAML files

### 2. Implement `AgentModelConfig` Model

- Create `AgentModelConfig` Pydantic model in `agf/config/models.py`
- Define fields: `thinking: str`, `standard: str`, `light: str`
- All fields required (no defaults)
- Add docstring explaining this represents model mappings for a single agent
- Add example in docstring showing the structure

### 3. Implement `AGFConfig` Model

- Create `AGFConfig` Pydantic model in `agf/config/models.py`
- Define fields matching `sample.agf.yaml`:
  - `worktrees: str` - default `".worktrees"`
  - `concurrent_tasks: int` - default `5` (note: use underscore in Python, hyphen in YAML)
  - `agent: str` - default `"claude-code"`
  - `model_type: str` - default `"standard"` (note: use underscore in Python, hyphen in YAML)
  - `agents: dict[str, AgentModelConfig]` - default with claude-code and opencode mappings
- Use Pydantic `Field(alias=...)` to support YAML hyphen names (concurrent-tasks, model-type)
- Add field validators to ensure agent and model_type are valid
- Implement `model_config = ConfigDict(populate_by_name=True)` to support both hyphen and underscore names
- Add class method `default()` that returns an instance with all defaults
- Add comprehensive docstring explaining each field

### 4. Implement `CLIConfig` Model

- Create `CLIConfig` Pydantic model in `agf/config/models.py`
- Define fields matching CLI arguments in `find_and_start_tasks.py`:
  - `tasks_file: Path` - required, location of tasks file
  - `project_dir: Path` - required, root directory of project
  - `agf_config: Path | None` - optional, location of AGF config file
  - `sync_interval: int` - default `30`, interval in seconds for trigger runs
  - `dry_run: bool` - default `False`, read-only mode flag
  - `single_run: bool` - default `False`, run once and exit flag
  - `agent: str | None` - default `None`, override for agent selection
  - `model_type: str | None` - default `None`, override for model type selection
- Add field validators for paths (ensure they exist when required)
- Add docstring explaining this collects CLI arguments and optional overrides

### 5. Implement YAML Configuration Loader

- Create `load_agf_config_from_file(path: Path) -> AGFConfig` function in `agf/config/loader.py`
- Use PyYAML to parse YAML file (add `pyyaml` dependency to pyproject.toml)
- Parse YAML and construct `AGFConfig` using Pydantic's model validation
- Handle file not found errors gracefully
- Handle YAML parsing errors with clear error messages
- Add docstring with example usage

### 6. Implement Configuration Discovery

- Create `find_agf_config(start_dir: Path) -> Path | None` function in `agf/config/loader.py`
- Search for `.agf.yaml` or `agf.yaml` in current directory and parent directories
- Stop at git repository root or filesystem root
- Return first config file found or None
- Add docstring explaining discovery strategy

### 7. Implement Configuration Merging

- Create `merge_configs(agf_config: AGFConfig, cli_config: CLIConfig) -> dict[str, Any]` function in `agf/config/loader.py`
- Return resolved configuration dict with precedence: CLI > AGF config > defaults
- Handle agent override: use `cli_config.agent` if set, else `agf_config.agent`
- Handle model_type override: use `cli_config.model_type` if set, else `agf_config.model_type`
- Include all AGF config fields in result
- Include all CLI config fields in result
- Add docstring explaining precedence rules with examples

### 8. Export Configuration Models

- Update `agf/config/__init__.py` to export:
  - `AGFConfig`
  - `CLIConfig`
  - `AgentModelConfig`
  - `load_agf_config_from_file`
  - `find_agf_config`
  - `merge_configs`
- Add module-level docstring explaining the configuration system

### 9. Create Unit Tests for `AGFConfig`

- Create `tests/config/test_agf_config.py`
- Test `AGFConfig.default()` returns expected defaults
- Test creating `AGFConfig` from dict with all fields specified
- Test creating `AGFConfig` with partial fields (uses defaults)
- Test field validation (invalid agent names, negative concurrent_tasks, etc.)
- Test alias support (YAML hyphen names vs Python underscore names)
- Test agents dict with custom agent configurations
- Test that default agents (claude-code, opencode) have correct model mappings

### 10. Create Unit Tests for `CLIConfig`

- Create `tests/config/test_cli_config.py`
- Test creating `CLIConfig` with required fields only
- Test creating `CLIConfig` with all fields specified
- Test defaults for optional fields
- Test path validation for tasks_file and project_dir
- Test agent and model_type overrides (None vs specified)

### 11. Create Unit Tests for Configuration Loading

- Create `tests/config/test_config_integration.py`
- Create test fixtures in `tests/config/fixtures/`:
  - `default.agf.yaml` - uses all default values
  - `custom.agf.yaml` - customized values for all fields
  - `minimal.agf.yaml` - only required fields
  - `invalid.agf.yaml` - invalid YAML to test error handling
- Test `load_agf_config_from_file()` with valid YAML files
- Test error handling for missing files
- Test error handling for invalid YAML
- Test error handling for schema validation failures

### 12. Create Integration Tests for Config Merging

- Add tests to `tests/config/test_config_integration.py`
- Test merging with no CLI overrides (uses AGF config)
- Test merging with CLI agent override (CLI wins)
- Test merging with CLI model_type override (CLI wins)
- Test merging with both overrides (CLI wins on both)
- Test merging when AGF config doesn't exist (uses defaults)
- Test that all fields from both configs appear in merged result

### 13. Update ModelMapping Integration

- Update `agf/agent/base.py` to add class method: `ModelMapping.from_agf_config(config: AGFConfig) -> None`
- Method should iterate through `config.agents` dict and call `ModelMapping.register_agent()` for each
- This allows dynamic agent registration from config files
- Add docstring explaining this updates the global ModelMapping state
- Add unit tests in `tests/agent/test_base.py` (create if doesn't exist)

### 14. Update find_and_start_tasks.py to Use Configuration System

- Import `AGFConfig`, `CLIConfig`, `load_agf_config_from_file`, `find_agf_config`, `merge_configs` from `agf.config`
- Add `--agf-config` CLI option to specify config file path (optional)
- In `main()` function, before using agent/model:
  - Load AGF config: if `--agf-config` provided, use it; else use `find_agf_config(project_dir)`
  - If config file found, load it with `load_agf_config_from_file()`; else use `AGFConfig.default()`
  - Create `CLIConfig` instance from CLI arguments
  - Call `merge_configs()` to get resolved configuration
  - Use resolved config for agent and model selection
- Update `ModelMapping.from_agf_config(agf_config)` to register agents from config
- Ensure backward compatibility: if no config file and no CLI overrides, behavior unchanged

### 15. Update CLI Help Text

- Update `--agent` option help text to mention it overrides AGF config
- Update `--model` option help text to mention it overrides AGF config
- Add `--agf-config` option help text explaining config file location and discovery
- Add note in main docstring about configuration precedence

### 16. Add PyYAML Dependency

- Run `uv add pyyaml` to add dependency to pyproject.toml
- Verify dependency appears in `[project.dependencies]`

### 17. Create Sample Configuration Documentation

- Update `sample.agf.yaml` comments to explain each field
- Add comment at top explaining precedence rules
- Add examples of common customizations

### 18. Test End-to-End Configuration Flow

- Create integration test in `tests/config/test_config_integration.py`:
  - Create temporary directory with `.agf.yaml` file
  - Simulate CLI invocation with various argument combinations
  - Verify correct agent and model are selected
  - Test discovery of config file from project directory
  - Test explicit config file path
  - Test CLI overrides take precedence

### 19. Validate All Tests Pass

- Run `uv run pytest tests/config/ -v` - verify all config tests pass
- Run `uv run pytest tests/agent/test_base.py -v` - verify ModelMapping integration tests pass (if created)
- Run `uv run pytest tests/ -v` - verify all tests pass
- Run `uv run python -m py_compile agf/config/*.py` - verify syntax

### 20. Create Usage Examples

- Add examples to `agf/config/models.py` docstrings showing:
  - Loading config from file
  - Creating CLIConfig from arguments
  - Merging configs
  - Using resolved config with agent runner
- Add inline code examples demonstrating the precedence hierarchy

## Testing Strategy

### Unit Tests

- **AGFConfig Model**:
  - Test default values match specification
  - Test field validation (types, constraints)
  - Test YAML alias support (hyphens to underscores)
  - Test custom agent configurations
  - Test invalid configurations raise validation errors

- **CLIConfig Model**:
  - Test required vs optional fields
  - Test default values
  - Test path validation
  - Test override fields (None vs specified values)

- **Configuration Loading**:
  - Test loading valid YAML files
  - Test error handling for missing files
  - Test error handling for invalid YAML
  - Test error handling for schema violations
  - Test config file discovery in directory tree

- **Configuration Merging**:
  - Test precedence rules (CLI > AGF > defaults)
  - Test partial overrides
  - Test all fields present in merged result
  - Test with missing AGF config (uses defaults)

### Integration Tests

- **End-to-End Configuration**:
  - Test loading config from file system
  - Test automatic config discovery
  - Test CLI overrides working correctly
  - Test ModelMapping registration from config
  - Test actual agent invocation uses correct config

- **Backward Compatibility**:
  - Test system works without config file (uses defaults)
  - Test system works with config file but no CLI overrides
  - Test existing workflows continue to function

### Edge Cases

- Empty config file (all defaults)
- Config file with only some fields (partial defaults)
- Invalid agent names in config
- Invalid model types in config
- Config file not readable (permissions)
- Circular directory search (filesystem root)
- Multiple config files in hierarchy (uses first found)
- CLI overrides with invalid values
- Missing required CLI arguments
- Agent config without all model types

## Acceptance Criteria

- `AGFConfig` model exists with all specified fields and defaults
- `CLIConfig` model exists with all specified fields
- `AgentModelConfig` model exists for per-agent model mappings
- Configuration can be loaded from YAML files
- YAML field names with hyphens map to Python field names with underscores
- Config file discovery searches parent directories for `.agf.yaml` or `agf.yaml`
- `merge_configs()` correctly implements precedence: CLI > AGF > defaults
- `ModelMapping.from_agf_config()` registers agents from configuration
- `find_and_start_tasks.py` uses the configuration system
- `--agf-config` CLI option allows specifying config file location
- CLI `--agent` and `--model` options override config file settings
- System works with no config file (uses hardcoded defaults)
- All existing functionality remains backward compatible
- PyYAML dependency added to project
- All configuration tests pass
- All existing tests continue to pass
- Documentation in docstrings and comments is comprehensive

## Validation Commands

Execute these commands to validate the feature is complete:

- `uv add pyyaml` - Add PyYAML dependency
- `uv run python -m py_compile agf/config/*.py` - Verify config module syntax
- `uv run pytest tests/config/test_agf_config.py -v` - Test AGFConfig model
- `uv run pytest tests/config/test_cli_config.py -v` - Test CLIConfig model
- `uv run pytest tests/config/test_config_integration.py -v` - Test config loading and merging
- `uv run pytest tests/config/ -v` - Test all config tests pass
- `uv run pytest tests/ -v` - Ensure all tests pass
- `uv run python -c "from agf.config import AGFConfig, CLIConfig; print('Config models imported successfully')"` - Verify imports work
- `uv run python -c "from agf.config import load_agf_config_from_file; config = load_agf_config_from_file('sample.agf.yaml'); print(f'Loaded config: agent={config.agent}, model_type={config.model_type}')"` - Test loading sample config
- `uv run agf/triggers/find_and_start_tasks.py --help` - Verify CLI help shows new --agf-config option
- `uv run python -c "from agf.agent.base import ModelMapping; from agf.config import AGFConfig; config = AGFConfig.default(); ModelMapping.from_agf_config(config); print(f'Registered agents: {ModelMapping.list_agents()}')"` - Test ModelMapping integration

## Notes

### Configuration Precedence

The configuration resolution follows a clear hierarchy:

```
CLI Arguments (highest priority)
    ↓
AGF Config File (.agf.yaml)
    ↓
Hardcoded Defaults (lowest priority)
```

This means:
- If `--agent claude-code` is passed on CLI, it overrides the AGF config file's `agent:` setting
- If AGF config file specifies `agent: opencode`, it overrides the default `claude-code`
- If neither CLI nor config file specify a setting, the hardcoded default is used

### YAML to Python Field Mapping

YAML uses hyphens in field names (convention), but Python uses underscores (PEP 8):
- YAML: `concurrent-tasks`, `model-type`
- Python: `concurrent_tasks`, `model_type`

Pydantic's `Field(alias=...)` and `ConfigDict(populate_by_name=True)` handle this mapping automatically.

### Agent Configuration Structure

The `agents` dictionary in AGF config uses this structure:
```yaml
agents:
  agent-name:
    thinking: concrete-model-for-thinking
    standard: concrete-model-for-standard
    light: concrete-model-for-light
```

This allows each agent to define its own mapping from abstract model types to concrete model identifiers.

### Configuration File Discovery

The discovery mechanism searches for config files in this order:
1. Explicit path via `--agf-config` CLI argument
2. `.agf.yaml` in current directory, then parent directories
3. `agf.yaml` in current directory, then parent directories
4. Stop at git repository root or filesystem root
5. If not found, use `AGFConfig.default()`

This allows project-specific config files to be committed to version control while supporting user-specific overrides in parent directories.

### Integration with ModelMapping

The existing `ModelMapping` class provides a global registry of agent model mappings. The new configuration system extends this by:
- Allowing model mappings to be defined in config files
- Registering those mappings at runtime via `ModelMapping.from_agf_config()`
- Maintaining backward compatibility with existing hardcoded mappings

If a config file defines new agents or updates existing ones, those changes are applied to the global `ModelMapping` when the configuration is loaded.

### Backward Compatibility

The implementation must maintain full backward compatibility:
- Existing scripts that don't use config files continue to work
- Default values match current hardcoded defaults
- CLI arguments work exactly as before
- No breaking changes to `AgentType`, `ModelType`, or `ModelMapping` APIs

### Future Enhancements

After this feature is complete, consider:
- Environment variable overrides (e.g., `AGF_AGENT`, `AGF_MODEL_TYPE`)
- User-level config file in home directory (`~/.agf.yaml`)
- Config validation command (`agf config validate`)
- Config show command to display resolved configuration
- Support for config file includes/inheritance
- Schema validation for custom agent configurations
- Config migration tools for version updates
