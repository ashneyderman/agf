# Chore: Add Agent and Model Type CLI Overrides to process_tasks.py

## Metadata

agf_id: `agf-017`
prompt: `add agent and model_type overrides via CLIConfig. Order of precendence will be CLI options, AGF config, default AGF config if nothing else specified. Please work this override option into process_tasks.py`

## Chore Description

Add command-line options `--agent` and `--model-type` to `process_tasks.py` to allow runtime overrides of the default agent and model type specified in the AGF configuration. These overrides should follow the established configuration precedence hierarchy: CLI options > AGF config > default AGF config.

Currently, `process_tasks.py` uses the multi-level configuration system (AGFConfig/CLIConfig/EffectiveConfig) but does not expose CLI options for overriding the agent and model type. The CLIConfig model already has `agent` and `model_type` fields (both optional, defaulting to None), and the `merge_configs()` function already implements the correct precedence logic. This chore simply requires:

1. Adding the CLI options to the Click command
2. Passing those values to the CLIConfig constructor
3. Verifying the existing precedence logic works as expected

## Relevant Files

Use these files to complete the chore:

- `agf/triggers/process_tasks.py:282-326` - Click command definition where `--agent` and `--model-type` options need to be added
- `agf/triggers/process_tasks.py:363-374` - CLIConfig instantiation where the new CLI arguments need to be passed
- `agf/config/models.py:128-172` - CLIConfig model definition showing the existing `agent` and `model_type` fields
- `agf/config/loader.py:110-164` - The `merge_configs()` function that already implements the precedence logic
- `tests/config/test_cli_config.py:70-99` - Existing tests for CLIConfig agent and model_type overrides
- `tests/config/test_config_integration.py:186-230` - Existing tests for config merging precedence

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add CLI Options to process_tasks.py

- Add `--agent` option after `--single-run` option (around line 318)
  - Type: `str`
  - Default: `None`
  - Help text: "Override the default agent (from AGF config or defaults)"
- Add `--model-type` option after `--agent` option
  - Type: `str`
  - Default: `None`
  - Help text: "Override the default model type (from AGF config or defaults)"

### 2. Update main() Function Signature

- Add `agent: str | None` parameter to `main()` function signature (line 319)
- Add `model_type: str | None` parameter to `main()` function signature (line 319)

### 3. Pass CLI Arguments to CLIConfig

- Update the `CLIConfig` instantiation (lines 364-371) to include:
  - `agent=agent`
  - `model_type=model_type`

### 4. Update Logging to Show Effective Configuration

- After `log(f"Concurrent tasks: {effective_config.concurrent_tasks}")` (line 382), add:
  - `log(f"Agent: {effective_config.agent}")`
  - `log(f"Model type: {effective_config.model_type}")`

### 5. Validate with Manual Testing

- Run `uv run agf/triggers/process_tasks.py --help` to verify new options appear
- Create a test tasks file and verify the options work:
  - Test with no overrides (uses AGF config or defaults)
  - Test with `--agent opencode` (CLI override)
  - Test with `--model-type thinking` (CLI override)
  - Test with both `--agent` and `--model-type` (both overrides)
- Check log output to confirm effective configuration values are correct

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/triggers/process_tasks.py` - Verify syntax is correct
- `uv run agf/triggers/process_tasks.py --help` - Verify `--agent` and `--model-type` options appear in help
- `uv run pytest tests/config/test_cli_config.py -v` - Verify CLIConfig tests still pass
- `uv run pytest tests/config/test_config_integration.py -v` - Verify config merging tests still pass
- `uv run pytest tests/ -v` - Verify all tests pass

## Notes

### Existing Infrastructure

The configuration system already has all the necessary infrastructure:

1. **CLIConfig Model** (`agf/config/models.py:128-172`):
   - Already has `agent: str | None = None` field
   - Already has `model_type: str | None = None` field
   - These fields are explicitly designed for CLI overrides

2. **merge_configs() Function** (`agf/config/loader.py:110-164`):
   - Already implements precedence: `cli_config.agent if cli_config.agent is not None else agf_config.agent`
   - Already implements precedence: `cli_config.model_type if cli_config.model_type is not None else agf_config.model_type`
   - Returns EffectiveConfig with resolved values

3. **Existing Tests**:
   - `tests/config/test_cli_config.py` has tests for agent and model_type overrides
   - `tests/config/test_config_integration.py` has comprehensive precedence tests
   - All tests should continue to pass without modification

### Configuration Precedence

The precedence chain is:
```
CLI Arguments (--agent, --model-type)
    ↓
AGF Config File (.agf.yaml or agf.yaml)
    ↓
Hardcoded Defaults (AGFConfig.default())
```

Examples:
- If user runs `--agent opencode`, the agent will be "opencode" regardless of AGF config
- If user runs with no `--agent` option, the agent will be from AGF config (or "claude-code" if no config)
- If user runs `--model-type thinking --agent opencode`, both will be overridden

### Integration with Existing Code

The `process_tasks.py` script already:
- Loads AGF configuration (lines 346-361)
- Creates CLIConfig instance (lines 364-371)
- Merges configurations (line 374)
- Uses effective configuration throughout (lines 382, 386, etc.)

This chore simply exposes the existing override capability through CLI options.

### No Breaking Changes

This change is purely additive:
- Existing behavior is preserved (defaults remain the same)
- No changes to configuration models or merging logic
- No changes to tests required
- Full backward compatibility with existing invocations
