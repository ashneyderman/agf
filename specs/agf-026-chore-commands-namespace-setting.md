# Chore: Add commands_namespace Setting

## Metadata

agf_id: `agf-026`
prompt: `add commands_namespace setting to AGFConfig; make it overridable through CLI parameters and pass it onto EffectiveConfig. Default value is "agf". Used this config constructing CommandTemplate, copy the setting to namespace attribute on the template.`

## Chore Description

Add a new configuration setting `commands_namespace` that controls the namespace used when constructing `CommandTemplate` objects. This setting should:

1. Be defined in `AGFConfig` with a default value of `"agf"`
2. Support a YAML alias `commands-namespace` for config file compatibility
3. Be overridable via CLI `--commands-namespace` parameter
4. Be passed through to `EffectiveConfig` after merge resolution
5. Be used in `WorkflowTaskHandler` when constructing `CommandTemplate` instances to set the `namespace` attribute

The `CommandTemplate` model already has a `namespace` field with a default value of `"agf"`. This chore adds the ability to configure this namespace globally via the configuration system rather than relying on the hardcoded default.

## Relevant Files

Use these files to complete the chore:

- `agf/config/models.py` - Contains `AGFConfig`, `CLIConfig`, and `EffectiveConfig` models where the new setting needs to be added
- `agf/config/loader.py` - Contains `merge_configs()` function that needs to be updated to handle the new setting
- `agf/triggers/process_tasks.py` - Contains CLI argument parsing where `--commands-namespace` option needs to be added
- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler` where `CommandTemplate` objects are constructed and need to use the config namespace
- `agf/agent/models.py` - Contains `CommandTemplate` model (for reference, already has `namespace` field)
- `tests/config/test_agf_config.py` - Unit tests for AGFConfig model
- `tests/config/test_cli_config.py` - Unit tests for CLIConfig model
- `tests/config/test_config_integration.py` - Integration tests for config loading and merging

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add commands_namespace to AGFConfig

- Add `commands_namespace: str = Field(default="agf", alias="commands-namespace")` field to `AGFConfig` class in `agf/config/models.py`
- Update the `AGFConfig.default()` class method to include `commands_namespace="agf"`
- Update the class docstring to document the new field

### 2. Add commands_namespace to CLIConfig

- Add `commands_namespace: str | None = None` field to `CLIConfig` class in `agf/config/models.py`
- Update the class docstring to document the new field

### 3. Add commands_namespace to EffectiveConfig

- Add `commands_namespace: str` field to `EffectiveConfig` class in `agf/config/models.py`
- Update the class docstring to document the new field

### 4. Update merge_configs Function

- In `agf/config/loader.py`, update `merge_configs()` to resolve `commands_namespace` with precedence: CLI > AGF config
- Add resolved value to `EffectiveConfig` constructor

### 5. Add CLI Parameter

- In `agf/triggers/process_tasks.py`, add `--commands-namespace` click option
- Pass the value to `CLIConfig` constructor
- Add logging for the commands_namespace value

### 6. Update WorkflowTaskHandler to Use Config Namespace

- In `agf/workflow/task_handler.py`, update all `CommandTemplate` instantiations to use `self.config.commands_namespace` for the `namespace` parameter
- This affects `_run_plan()`, `_run_chore()`, `_run_feature()`, `_run_implement()`, `_create_commit()`, and `_create_empty_commit()` methods

### 7. Add Unit Tests for AGFConfig

- Add test `test_agf_config_commands_namespace_default` to verify default value is "agf"
- Add test `test_agf_config_commands_namespace_hyphen_alias` to verify YAML alias works
- Add test `test_agf_config_commands_namespace_custom_value` to verify custom values work

### 8. Add Unit Tests for CLIConfig

- Add test `test_cli_config_commands_namespace_default` to verify default is None
- Add test `test_cli_config_commands_namespace_custom_value` to verify custom values work

### 9. Add Integration Tests for Config Merging

- Add test `test_merge_cli_commands_namespace_override` to verify CLI wins over AGF config
- Add test `test_merge_agf_commands_namespace_when_cli_none` to verify AGF config is used when CLI is None

### 10. Validate the Implementation

- Run all tests to ensure nothing is broken
- Verify the configuration flow works end-to-end

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/config/models.py agf/config/loader.py agf/triggers/process_tasks.py agf/workflow/task_handler.py` - Verify all modified Python files compile
- `uv run pytest tests/config/test_agf_config.py -v` - Run AGFConfig unit tests
- `uv run pytest tests/config/test_cli_config.py -v` - Run CLIConfig unit tests
- `uv run pytest tests/config/test_config_integration.py -v` - Run config integration tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The `CommandTemplate.namespace` field already exists with a default of `"agf"`, so the model itself doesn't need to be modified
- Follow the same pattern used for `branch_prefix` setting which was recently added (similar field with hyphen alias, CLI override, merge logic)
- The namespace is used for categorizing prompts by source or purpose, enabling different prompt sources to use different namespaces
