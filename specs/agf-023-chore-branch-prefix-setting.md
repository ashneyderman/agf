# Chore: Add Branch Prefix Setting to AGFConfig

## Metadata

agf_id: `agf-023`
prompt: `add branch_prefix setting to AGFConfig; make it overridable through CLI parameters and pass it onto EffectiveConfig.`

## Chore Description

Add a `branch_prefix` configuration option to enable customization of the git branch naming prefix. Currently, branch names are hardcoded to use the `USER` environment variable (e.g., `alex/agf-023-feature-name`). This chore introduces a `branch_prefix` setting that:

1. Defaults to the current behavior (using the `USER` environment variable)
2. Can be configured via the AGF config file (`.agf.yaml`)
3. Can be overridden via CLI parameter (`--branch-prefix`)
4. Follows the established configuration precedence: CLI > AGF Config > Default

This enables teams to use custom branch prefixes like `team-name/`, project-specific prefixes, or any other naming convention.

## Relevant Files

Use these files to complete the chore:

- `agf/config/models.py:47-126` - `AGFConfig` model definition where `branch_prefix` field needs to be added
- `agf/config/models.py:128-163` - `CLIConfig` model definition where `branch_prefix` CLI override field needs to be added
- `agf/config/models.py:174-229` - `EffectiveConfig` model definition where resolved `branch_prefix` field needs to be added
- `agf/config/loader.py:110-164` - `merge_configs()` function that needs to merge `branch_prefix` with proper precedence
- `agf/triggers/process_tasks.py:282-400` - Click command definition where `--branch-prefix` option needs to be added and passed to `CLIConfig`
- `agf/workflow/task_handler.py:62-104` - `_get_username()` and `_get_branch_name()` methods that need to use `branch_prefix` from config
- `sample.agf.yaml` - Sample config file where `branch-prefix` example should be added
- `tests/config/test_agf_config.py` - Tests for `AGFConfig` model
- `tests/config/test_cli_config.py` - Tests for `CLIConfig` model
- `tests/config/test_config_integration.py` - Tests for config merging
- `tests/agf/workflow/test_task_handler.py:70-118` - Tests for `WorkflowTaskHandler` helper methods including branch name generation

### New Files

None required - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `branch_prefix` Field to AGFConfig

- Add `branch_prefix: str | None = Field(default=None, alias="branch-prefix")` to `AGFConfig` class in `agf/config/models.py`
- Position it after `model_type` field (around line 92)
- The field should be `None` by default (meaning use `USER` environment variable)
- Update the class docstring to document the new field

### 2. Update AGFConfig.default() Method

- Update the `default()` class method in `AGFConfig` to include `branch_prefix=None`
- The default behavior (using `USER` env var) is preserved when `branch_prefix` is `None`

### 3. Add `branch_prefix` Field to CLIConfig

- Add `branch_prefix: str | None = None` to `CLIConfig` class in `agf/config/models.py`
- Position it after `model_type` field (around line 163)
- Update the class docstring to document the CLI override field

### 4. Add `branch_prefix` Field to EffectiveConfig

- Add `branch_prefix: str | None` to `EffectiveConfig` class in `agf/config/models.py`
- Position it in the "Resolved values" section after `model_type` (around line 228)
- Update the class docstring to document the resolved field

### 5. Update merge_configs() Function

- Add precedence logic for `branch_prefix` in `agf/config/loader.py`
- Add: `resolved_branch_prefix = cli_config.branch_prefix if cli_config.branch_prefix is not None else agf_config.branch_prefix`
- Pass `branch_prefix=resolved_branch_prefix` to `EffectiveConfig` constructor

### 6. Add CLI Option to process_tasks.py

- Add `--branch-prefix` option after `--model-type` option in `agf/triggers/process_tasks.py`
- Type: `str`, Default: `None`
- Help text: "Override the branch name prefix (default: uses USER environment variable)"
- Add `branch_prefix: str | None` parameter to `main()` function signature
- Pass `branch_prefix=branch_prefix` to `CLIConfig` constructor
- Add logging: `log(f"Branch prefix: {effective_config.branch_prefix or 'USER env var'}")`

### 7. Update WorkflowTaskHandler to Use branch_prefix

- Modify `_get_branch_name()` method in `agf/workflow/task_handler.py`
- Replace hardcoded `username = self._get_username()` with:
  ```python
  prefix = self.config.branch_prefix if self.config.branch_prefix else self._get_username()
  ```
- Update branch name format strings to use `prefix` instead of `username`
- The `_get_username()` method remains as fallback when `branch_prefix` is `None`

### 8. Update sample.agf.yaml

- Add commented example for `branch-prefix` in `sample.agf.yaml`
- Add after `model-type` section:
  ```yaml
  # Branch name prefix for git worktrees (default: uses USER env var)
  # Can be overridden with --branch-prefix CLI option
  # branch-prefix: my-team
  ```

### 9. Add Tests for AGFConfig.branch_prefix

- Add tests in `tests/config/test_agf_config.py`:
  - Test default value is `None`
  - Test YAML hyphen alias works (`branch-prefix`)
  - Test custom value is preserved

### 10. Add Tests for CLIConfig.branch_prefix

- Add tests in `tests/config/test_cli_config.py`:
  - Test default value is `None`
  - Test custom value is preserved

### 11. Add Tests for Config Merging with branch_prefix

- Add tests in `tests/config/test_config_integration.py`:
  - Test CLI override wins over AGF config
  - Test AGF config used when CLI is `None`
  - Test `None` passed through when both are `None`

### 12. Update WorkflowTaskHandler Tests

- Update tests in `tests/agf/workflow/test_task_handler.py`:
  - Update `mock_config` fixture to include `branch_prefix` field
  - Add test for `_get_branch_name()` with custom `branch_prefix`
  - Add test for `_get_branch_name()` with `None` (falls back to USER)

### 13. Validate Implementation

- Run all tests to ensure nothing is broken
- Verify CLI help shows new `--branch-prefix` option
- Test precedence: CLI > AGF Config > Default (USER env var)

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/config/models.py` - Verify models compile
- `uv run python -m py_compile agf/config/loader.py` - Verify loader compiles
- `uv run python -m py_compile agf/triggers/process_tasks.py` - Verify trigger compiles
- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify handler compiles
- `uv run agf/triggers/process_tasks.py --help` - Verify `--branch-prefix` option appears
- `uv run pytest tests/config/ -v` - Run all config tests
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run task handler tests
- `uv run pytest tests/ -v` - Run all tests

## Notes

### Configuration Precedence

The branch_prefix follows the same precedence chain as other config options:
```
CLI Arguments (--branch-prefix)
    ↓
AGF Config File (branch-prefix: my-team)
    ↓
Default (None → falls back to USER env var)
```

### Backward Compatibility

This change is fully backward compatible:
- Default behavior is preserved (uses `USER` environment variable when `branch_prefix` is `None`)
- No existing configuration files need to be updated
- No breaking changes to any interfaces

### Branch Name Examples

| Config State | Resulting Branch Name |
|--------------|----------------------|
| `branch_prefix=None`, `USER=alex` | `alex/agf-023-feature-name` |
| `branch_prefix="team"` | `team/agf-023-feature-name` |
| `branch_prefix="project/team"` | `project/team/agf-023-feature-name` |

### Integration with Existing Code

The `WorkflowTaskHandler` already has a `_get_username()` helper method that retrieves the `USER` environment variable. The implementation should:
1. Check if `self.config.branch_prefix` is set
2. If set, use it as the prefix
3. If `None`, fall back to `_get_username()` behavior
