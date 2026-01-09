# Chore: Rename `prompt_template` parameter to `command_template`

## Metadata

agf_id: `agf-021`
prompt: `rename \`prompt_template\` parameter in \`AgentRunner\` to \`command_template\`. Make sure all call references are updated and all tests are still passing.`

## Chore Description

Rename the `prompt_template` parameter to `command_template` throughout the codebase to better reflect its purpose. The parameter represents a structured command template (CommandTemplate) that contains metadata, configuration, and parameters for agent execution. The current name `prompt_template` is misleading as it suggests simple prompt templating rather than comprehensive command configuration.

This rename affects:
- The `AgentRunner.run_command()` method signature
- The `Agent` protocol's `run_command()` method signature
- All concrete agent implementations (ClaudeCodeAgent, OpenCodeAgent)
- All call sites in the workflow task handler
- All test assertions that verify the parameter name
- Related documentation and specification files

## Relevant Files

Use these files to complete the chore:

- `agf/agent/runner.py` - Contains AgentRunner.run_command() method with the `prompt_template` parameter
- `agf/agent/base.py` - Contains Agent protocol definition with run_command() method signature
- `agf/agent/claude_code.py` - Contains ClaudeCodeAgent implementation of run_command() method
- `agf/agent/opencode.py` - Contains OpenCodeAgent implementation of run_command() method
- `agf/workflow/task_handler.py` - Contains WorkflowTaskHandler that calls AgentRunner.run_command() with the parameter
- `tests/agf/workflow/test_task_handler.py` - Contains tests that verify the parameter name in assertions
- `specs/agf-016-plan-unify-prompt-processing.md` - Contains specification documentation referencing prompt_template
- `prompts/agf-add-agents-template.md` - Contains template documentation referencing prompt_template

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Agent Protocol Definition

- Edit `agf/agent/base.py` to rename the parameter in the `Agent` protocol's `run_command()` method from `prompt_template` to `command_template`
- Update the docstring to reflect the new parameter name

### 2. Update AgentRunner Implementation

- Edit `agf/agent/runner.py` to rename the parameter in `AgentRunner.run_command()` method from `prompt_template` to `command_template`
- Update the docstring to reflect the new parameter name
- Update the method call to `agent.run_command()` to use the new parameter name

### 3. Update ClaudeCodeAgent Implementation

- Edit `agf/agent/claude_code.py` to rename the parameter in `run_command()` method from `prompt_template` to `command_template`
- Update all references to `prompt_template` within the method body to use `command_template`
- Update the docstring to reflect the new parameter name

### 4. Update OpenCodeAgent Implementation

- Edit `agf/agent/opencode.py` to rename the parameter in `run_command()` method from `prompt_template` to `command_template`
- Update all references to `prompt_template` within the method body to use `command_template`
- Update the docstring to reflect the new parameter name

### 5. Update WorkflowTaskHandler Call Sites

- Edit `agf/workflow/task_handler.py` to update the call to `AgentRunner.run_command()` to use the new parameter name `command_template`

### 6. Update Test Assertions

- Edit `tests/agf/workflow/test_task_handler.py` to update all assertions that check for `prompt_template` parameter to check for `command_template` instead
- This affects 8 test assertions that verify the parameter name in mock call arguments

### 7. Update Documentation Files

- Edit `specs/agf-016-plan-unify-prompt-processing.md` to replace all references to `prompt_template` with `command_template`
- Edit `prompts/agf-add-agents-template.md` to replace references to `prompt_template` with `command_template`

### 8. Run Tests and Verify

- Run the test suite to ensure all tests pass with the new parameter name
- Verify no regressions were introduced
- Check that all references have been updated

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run task handler tests to ensure all assertions pass with new parameter name
- `uv run pytest tests/agf/agent/ -v` - Run agent tests to ensure protocol compliance
- `uv run pytest -v` - Run full test suite to ensure no regressions
- `grep -r "prompt_template" agf/ tests/ --include="*.py" | grep -v "CommandTemplate"` - Verify no remaining references to the old parameter name (should only find CommandTemplate class references)

## Notes

- The parameter type `CommandTemplate` remains unchanged - only the parameter name is being renamed
- This is a pure refactoring with no functional changes
- All existing functionality should continue to work exactly as before
- The rename improves code clarity by aligning the parameter name with its actual purpose as a command template rather than just a prompt template
