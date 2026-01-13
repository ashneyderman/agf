# Plan: Worktree Agent Override

## Metadata

agf_id: `agf-032`
prompt: `use the Worktree.agent field to override the agent name to override the config when calling the agent.`
task_type: enhancement
complexity: simple

## Task Description

Modify the `WorkflowTaskHandler` class to use the `Worktree.agent` field to override the default agent from `EffectiveConfig` when executing commands. Currently, the `_execute_command` method always uses `self.config.agent` to determine which agent to run. This change will allow individual worktrees to specify their own agent, enabling mixed-agent workflows where different worktrees can use different agents (e.g., claude-code, opencode).

## Objective

When a worktree has the `agent` field set (e.g., `## Git Worktree feature-auth {SCHIP-123,opencode}`), the task handler should use that agent instead of the default config agent when executing commands for that worktree.

## Solution Approach

The `_execute_command` method needs to be updated to:
1. Accept a `worktree` parameter to access the agent override
2. Check if `worktree.agent` is set and not None
3. If set, use `worktree.agent` instead of `self.config.agent` for agent selection
4. Ensure agent model config is also resolved using the effective agent name

All methods that call `_execute_command` already have access to the worktree object, so passing it is straightforward.

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - The main file to modify. Contains `WorkflowTaskHandler` class with `_execute_command` method that needs to accept worktree parameter and use worktree.agent override
- `agf/task_manager/models.py` - Contains the `Worktree` model with the `agent: str | None = None` field (already implemented)
- `agf/task_manager/markdown_source.py` - Already parses the agent field from markdown headers (already implemented)
- `tests/agf/workflow/test_task_handler.py` - Test file that needs new tests for worktree agent override functionality

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update _execute_command Method Signature

- Add `worktree: Worktree` parameter to `_execute_command` method
- Determine the effective agent: use `worktree.agent` if set, otherwise `self.config.agent`
- Resolve agent model config using the effective agent name
- Update log message to show which agent is being used

### 2. Update All Callers of _execute_command

Update all methods that call `_execute_command` to pass the worktree parameter:
- `_run_plan` - already has worktree parameter
- `_run_chore` - already has worktree parameter
- `_run_feature` - already has worktree parameter
- `_run_implement` - already has worktree parameter
- `_run_build` - already has worktree parameter
- `_create_commit` - already has worktree parameter
- `_create_empty_commit` - already has worktree parameter
- `_create_github_pr` - already has worktree parameter

### 3. Add Validation for Worktree Agent

- Add validation that if `worktree.agent` is set, it exists in `self.config.agents`
- Log a warning if the agent is not found and fall back to default config agent
- This prevents runtime errors if an invalid agent name is specified

### 4. Add Unit Tests for Worktree Agent Override

Add new tests in `tests/agf/workflow/test_task_handler.py`:
- Test that worktree.agent overrides config.agent when set
- Test that config.agent is used when worktree.agent is None
- Test that invalid worktree.agent falls back to config.agent with warning
- Test integration with actual command execution using worktree agent

### 5. Validate Changes

- Run all existing tests to ensure no regressions
- Run new tests to verify worktree agent override functionality
- Verify the code compiles without errors

## Testing Strategy

1. **Unit Tests**: Add tests in `test_task_handler.py` to verify:
   - `_execute_command` uses worktree.agent when set
   - `_execute_command` falls back to config.agent when worktree.agent is None
   - Invalid agent names in worktree.agent are handled gracefully

2. **Edge Cases**:
   - Worktree with agent not in config.agents dictionary
   - Worktree with empty string agent (should fall back to default)
   - Multiple worktrees with different agents in same run

## Acceptance Criteria

- When `worktree.agent` is set, that agent is used instead of `config.agent`
- When `worktree.agent` is None or empty, `config.agent` is used (existing behavior)
- Invalid `worktree.agent` values fall back to `config.agent` with a warning log
- All existing tests continue to pass
- New tests cover the worktree agent override functionality
- Code compiles without type errors

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the modified file compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run task handler tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `uv run ruff check agf/workflow/task_handler.py` - Check code style

## Notes

- The `Worktree.agent` field and markdown parsing are already implemented in previous work
- The `AgentModelConfig` dictionary in `EffectiveConfig.agents` maps agent names to their model configurations
- Both `claude-code` and `opencode` agents are pre-registered in `AgentRunner`
