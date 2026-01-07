# Plan: Unify Prompt Processing with PromptTemplate

## Metadata

agf_id: `agf-016`
prompt: `@prompts/agf-add-agents-template.md`
task_type: refactor
complexity: medium

## Task Description

Unify prompt processing across all available command prompts by creating a single PromptTemplate model that standardizes how prompts are passed to agents. Currently, agents accept raw prompt strings, but we need a structured approach that includes namespace, parameters, JSON output configuration, and model type selection in a single unified interface.

## Objective

Create a unified prompt processing interface that:
1. Introduces a `PromptTemplate` model in `agf/agent/models.py` with standard fields for all prompt executions
2. Refactors the Agent protocol to use `run_prompt(prompt_template: PromptTemplate)` instead of `run(prompt: str, config: AgentConfig)`
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

Introduce a PromptTemplate model that encapsulates all prompt-related configuration in a single structured object. The Agent protocol will be updated to use this model, and both agent implementations will be modified to extract the necessary information from the template. This creates a clear separation between prompt-level configuration (namespace, prompt text, params, json_output, model) and execution-level configuration (timeout, working directory, CLI flags).

## Relevant Files

- **agf/agent/base.py** - Contains Agent protocol, AgentConfig, AgentResult, and ModelType enum. Need to update Agent protocol to define run_prompt method.
- **agf/agent/claude_code.py** - ClaudeCodeAgent implementation. Need to rename run to run_prompt and adapt to use PromptTemplate.
- **agf/agent/opencode.py** - OpenCodeAgent implementation. Need to rename run to run_prompt and adapt to use PromptTemplate.
- **agf/agent/runner.py** - AgentRunner that executes agents. May need to update to support the new run_prompt interface.

### New Files

- **agf/agent/models.py** - New file containing the PromptTemplate model with fields: namespace, prompt, params, json_output, and model.

## Implementation Phases

### Phase 1: Foundation

Create the PromptTemplate model and update the Agent protocol:
- Create agf/agent/models.py with PromptTemplate class
- Update Agent protocol in base.py to add run_prompt method signature
- Import PromptTemplate in relevant modules

### Phase 2: Core Implementation

Update agent implementations to use PromptTemplate:
- Implement run_prompt in ClaudeCodeAgent
- Implement run_prompt in OpenCodeAgent
- Ensure both implementations properly extract prompt text, model type, and json_output from the template

### Phase 3: Integration & Cleanup

Ensure the new interface works correctly:
- Update AgentRunner if needed to support run_prompt
- Validate that existing functionality continues to work
- Consider deprecation path for the old run method

## Step by Step Tasks

### 1. Create PromptTemplate model

- Create new file agf/agent/models.py
- Import necessary dependencies (Pydantic BaseModel, ModelType from base.py)
- Define PromptTemplate class with the following fields:
  - `namespace: str` with default value "agf"
  - `prompt: str` as a required field (no default)
  - `params: list | None` with default value None
  - `json_output: bool` with default value False
  - `model: ModelType | None` with default value None
- Add docstring explaining the purpose and usage of PromptTemplate

### 2. Update Agent protocol

- In agf/agent/base.py, import PromptTemplate from agf.agent.models
- Add new method signature to Agent protocol: `run_prompt(self, prompt_template: PromptTemplate, config: AgentConfig | None = None) -> AgentResult`
- Add docstring for run_prompt explaining it replaces the run method
- Keep the existing run method in the protocol for now to maintain backward compatibility

### 3. Implement run_prompt in ClaudeCodeAgent

- In agf/agent/claude_code.py, import PromptTemplate from agf.agent.models
- Add run_prompt method to ClaudeCodeAgent class
- Extract prompt text from prompt_template.prompt
- If prompt_template.model is not None, merge it into config (create new config if needed)
- If prompt_template.json_output is True, ensure config.json_output is set
- Call the internal _build_command and execution logic with the extracted values
- Return AgentResult as before

### 4. Implement run_prompt in OpenCodeAgent

- In agf/agent/opencode.py, import PromptTemplate from agf.agent.models
- Add run_prompt method to OpenCodeAgent class
- Extract prompt text from prompt_template.prompt
- If prompt_template.model is not None, merge it into config (create new config if needed)
- If prompt_template.json_output is True, ensure config.json_output is set
- Call the internal _build_command and execution logic with the extracted values
- Return AgentResult as before

### 5. Update AgentRunner

- Review agf/agent/runner.py to determine if updates are needed
- If AgentRunner.run needs to support PromptTemplate, add a new method or update the existing one
- Ensure backward compatibility with existing callers

### 6. Validate implementation

- Run all existing tests to ensure no regressions: `uv run python -m pytest tests/agent/ -v`
- Test PromptTemplate creation with various field combinations
- Verify that run_prompt correctly extracts and uses model type from template
- Verify that run_prompt correctly sets json_output from template
- Ensure both agents work with the new interface

## Testing Strategy

**Unit Tests:**
- Test PromptTemplate model creation with various field combinations
- Test PromptTemplate with default values (namespace="agf", params=None, json_output=False, model=None)
- Test PromptTemplate with custom values for all fields
- Test ClaudeCodeAgent.run_prompt extracts prompt correctly
- Test ClaudeCodeAgent.run_prompt merges model from template into config
- Test ClaudeCodeAgent.run_prompt sets json_output from template
- Test OpenCodeAgent.run_prompt with same scenarios as ClaudeCodeAgent
- Test backward compatibility of existing run method if maintained

**Edge Cases:**
- PromptTemplate with empty prompt string (should fail validation if required)
- PromptTemplate with model=None (should use config default or agent default)
- PromptTemplate with json_output=True but config.json_output=False (template should take precedence)
- PromptTemplate with params containing various data types
- Concurrent calls to run_prompt with different templates

## Acceptance Criteria

1. agf/agent/models.py exists and contains PromptTemplate class
2. PromptTemplate has all required fields: namespace (default "agf"), prompt (required), params (default None), json_output (default False), model (default None)
3. Agent protocol defines run_prompt method accepting PromptTemplate
4. ClaudeCodeAgent implements run_prompt and correctly uses all PromptTemplate fields
5. OpenCodeAgent implements run_prompt and correctly uses all PromptTemplate fields
6. Model type from PromptTemplate is properly passed to AgentConfig
7. JSON output flag from PromptTemplate is properly passed to AgentConfig
8. All existing tests pass without modification
9. Code compiles without errors

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/agent/*.py` - Verify all agent files compile without errors
- `uv run python -c "from agf.agent.models import PromptTemplate; print(PromptTemplate(prompt='test'))"` - Test PromptTemplate can be imported and instantiated
- `uv run python -c "from agf.agent.models import PromptTemplate; from agf.agent.base import ModelType; pt = PromptTemplate(prompt='test', model=ModelType.THINKING); print(pt)"` - Test PromptTemplate with ModelType
- `uv run python -m pytest tests/ -v` - Run all tests to ensure no regressions (if tests exist)

## Notes

- The PromptTemplate model should use Pydantic BaseModel for consistency with other models in the codebase (see agf/config/models.py for examples)
- Consider whether params should be `list[str]` or `list[Any]` - lean towards `list[Any]` for flexibility
- The model field in PromptTemplate should accept ModelType enum values, not raw strings
- When merging PromptTemplate settings into AgentConfig, template values should take precedence
- The namespace field is included for future use in organizing prompts by category (e.g., "agf", "custom")
- Keep the existing run method in Agent protocol and implementations initially to avoid breaking existing code - a separate cleanup task can deprecate it later
- The params field is intended for template variable substitution in future enhancements
