# Plan: Unify Prompt Processing with CommandTemplate

## Metadata

agf_id: `agf-016`
prompt: `@prompts/agf-add-agents-template.md`
task_type: refactor
complexity: medium

## Task Description

Unify prompt processing across all available command prompts by creating a single CommandTemplate model that standardizes how prompts are passed to agents. Currently, agents accept raw prompt strings, but we need a structured approach that includes namespace, parameters, JSON output configuration, and model type selection in a single unified interface.

## Objective

Create a unified prompt processing interface that:
1. Introduces a `CommandTemplate` model in `agf/agent/models.py` with standard fields for all prompt executions
2. Refactors the Agent protocol to use `run_command(command_template: CommandTemplate)` instead of `run(prompt: str, config: AgentConfig)`
3. Updates both ClaudeCodeAgent and OpenCodeAgent implementations to use the new interface
4. Maintains backward compatibility where needed during the transition

## Problem Statement

Currently, each agent's `run` method accepts a raw prompt string and optional AgentConfig. This approach lacks structure and makes it difficult to:
- Standardize prompt execution across different agent types
- Pass namespace information for prompt organization
- Specify prompt-specific parameters in a type-safe way
- Configure JSON output requirements at the prompt level
- Select models on a per-prompt basis

## Solution Approach

Introduce a CommandTemplate model that encapsulates all prompt-related configuration in a single structured object. The Agent protocol will be updated to use this model, and both agent implementations will be modified to extract the necessary information from the template. This creates a clear separation between prompt-level configuration (namespace, prompt text, params, json_output, model) and execution-level configuration (timeout, working directory, CLI flags).

## Relevant Files

- **agf/agent/base.py** - Contains Agent protocol, AgentConfig, AgentResult, and ModelType enum. Need to update Agent protocol to define run_command method.
- **agf/agent/claude_code.py** - ClaudeCodeAgent implementation. Need to rename run to run_command and adapt to use CommandTemplate.
- **agf/agent/opencode.py** - OpenCodeAgent implementation. Need to rename run to run_command and adapt to use CommandTemplate.
- **agf/agent/runner.py** - AgentRunner that executes agents. May need to update to support the new run_command interface.

### New Files

- **agf/agent/models.py** - New file containing the CommandTemplate model with fields: namespace, prompt, params, json_output, and model.

## Implementation Phases

### Phase 1: Foundation

Create the CommandTemplate model and update the Agent protocol:
- Create agf/agent/models.py with CommandTemplate class
- Update Agent protocol in base.py to add run_command method signature
- Import CommandTemplate in relevant modules

### Phase 2: Core Implementation

Update agent implementations to use CommandTemplate:
- Implement run_command in ClaudeCodeAgent
- Implement run_command in OpenCodeAgent
- Ensure both implementations properly extract prompt text, model type, and json_output from the template

### Phase 3: Integration & Cleanup

Ensure the new interface works correctly:
- Update AgentRunner if needed to support run_command
- Validate that existing functionality continues to work
- Consider deprecation path for the old run method

## Step by Step Tasks

### 1. Create CommandTemplate model

- Create new file agf/agent/models.py
- Import necessary dependencies (Pydantic BaseModel, ModelType from base.py)
- Define CommandTemplate class with the following fields:
  - `namespace: str` with default value "agf"
  - `prompt: str` as a required field (no default)
  - `params: list | None` with default value None
  - `json_output: bool` with default value False
  - `model: ModelType | None` with default value None
- Add docstring explaining the purpose and usage of CommandTemplate

### 2. Update Agent protocol

- In agf/agent/base.py, import CommandTemplate from agf.agent.models
- Add new method signature to Agent protocol: `run_command(self, command_template: CommandTemplate, config: AgentConfig | None = None) -> AgentResult`
- Add docstring for run_command explaining it replaces the run method
- Keep the existing run method in the protocol for now to maintain backward compatibility

### 3. Implement run_command in ClaudeCodeAgent

- In agf/agent/claude_code.py, import CommandTemplate from agf.agent.models
- Add run_command method to ClaudeCodeAgent class
- Extract prompt text from command_template.prompt
- If command_template.model is not None, merge it into config (create new config if needed)
- If command_template.json_output is True, ensure config.json_output is set
- Call the internal _build_command and execution logic with the extracted values
- Return AgentResult as before

### 4. Implement run_command in OpenCodeAgent

- In agf/agent/opencode.py, import CommandTemplate from agf.agent.models
- Add run_command method to OpenCodeAgent class
- Extract prompt text from command_template.prompt
- If command_template.model is not None, merge it into config (create new config if needed)
- If command_template.json_output is True, ensure config.json_output is set
- Call the internal _build_command and execution logic with the extracted values
- Return AgentResult as before

### 5. Update AgentRunner

- Review agf/agent/runner.py to determine if updates are needed
- If AgentRunner.run needs to support CommandTemplate, add a new method or update the existing one
- Ensure backward compatibility with existing callers

### 6. Validate implementation

- Run all existing tests to ensure no regressions: `uv run python -m pytest tests/agent/ -v`
- Test CommandTemplate creation with various field combinations
- Verify that run_command correctly extracts and uses model type from template
- Verify that run_command correctly sets json_output from template
- Ensure both agents work with the new interface

## Testing Strategy

**Unit Tests:**
- Test CommandTemplate model creation with various field combinations
- Test CommandTemplate with default values (namespace="agf", params=None, json_output=False, model=None)
- Test CommandTemplate with custom values for all fields
- Test ClaudeCodeAgent.run_command extracts prompt correctly
- Test ClaudeCodeAgent.run_command merges model from template into config
- Test ClaudeCodeAgent.run_command sets json_output from template
- Test OpenCodeAgent.run_command with same scenarios as ClaudeCodeAgent
- Test backward compatibility of existing run method if maintained

**Edge Cases:**
- CommandTemplate with empty prompt string (should fail validation if required)
- CommandTemplate with model=None (should use config default or agent default)
- CommandTemplate with json_output=True but config.json_output=False (template should take precedence)
- CommandTemplate with params containing various data types
- Concurrent calls to run_command with different templates

## Acceptance Criteria

1. agf/agent/models.py exists and contains CommandTemplate class
2. CommandTemplate has all required fields: namespace (default "agf"), prompt (required), params (default None), json_output (default False), model (default None)
3. Agent protocol defines run_command method accepting CommandTemplate
4. ClaudeCodeAgent implements run_command and correctly uses all CommandTemplate fields
5. OpenCodeAgent implements run_command and correctly uses all CommandTemplate fields
6. Model type from CommandTemplate is properly passed to AgentConfig
7. JSON output flag from CommandTemplate is properly passed to AgentConfig
8. All existing tests pass without modification
9. Code compiles without errors

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/agent/*.py` - Verify all agent files compile without errors
- `uv run python -c "from agf.agent.models import CommandTemplate; print(CommandTemplate(prompt='test'))"` - Test CommandTemplate can be imported and instantiated
- `uv run python -c "from agf.agent.models import CommandTemplate; from agf.agent.base import ModelType; pt = CommandTemplate(prompt='test', model=ModelType.THINKING); print(pt)"` - Test CommandTemplate with ModelType
- `uv run python -m pytest tests/ -v` - Run all tests to ensure no regressions (if tests exist)

## Notes

- The CommandTemplate model should use Pydantic BaseModel for consistency with other models in the codebase (see agf/config/models.py for examples)
- Consider whether params should be `list[str]` or `list[Any]` - lean towards `list[Any]` for flexibility
- The model field in CommandTemplate should accept ModelType enum values, not raw strings
- When merging CommandTemplate settings into AgentConfig, template values should take precedence
- The namespace field is included for future use in organizing prompts by category (e.g., "agf", "custom")
- Keep the existing run method in Agent protocol and implementations initially to avoid breaking existing code - a separate cleanup task can deprecate it later
- The params field is intended for template variable substitution in future enhancements
