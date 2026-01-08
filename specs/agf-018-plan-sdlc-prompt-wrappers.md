# Plan: Create SDLC Prompt Wrappers

## Metadata

agf_id: `agf-018`
prompt: `@prompts/agf-create-sdlc-prompt-wrappers.md`
task_type: feature
complexity: medium

## Task Description

Create wrapper functions for each of the SDLC-related prompts (plan.md, chore.md, feature.md, implement.md) that the AGF project provides. These wrappers will provide a clean, type-safe interface for executing SDLC workflows by encapsulating the prompt execution logic and handling parameter passing and result parsing.

## Objective

Implement protected wrapper functions in `agf/workflow/task_handler.py` that:
1. Accept all required variables from each prompt's `## Variables` section
2. Build and execute CommandTemplate objects with appropriate configuration
3. Parse and return results based on each prompt's `## Report` specification
4. Are fully covered by unit tests

## Problem Statement

Currently, there's no structured way to invoke SDLC prompts (plan, chore, feature, implement) from Python code. The prompts exist as markdown files with variable placeholders, but there's no programmatic interface to execute them. This makes it difficult to build higher-level automation that chains these prompts together or invokes them from other parts of the codebase.

## Solution Approach

Create four protected wrapper functions in the WorkflowTaskHandler class:
- `_run_plan()` - Executes plan.md prompt and returns the plan file path (parses JSON output)
- `_run_chore()` - Executes chore.md prompt and returns the chore plan file path (parses JSON output)
- `_run_feature()` - Executes feature.md prompt and returns the feature plan file path (parses JSON output)
- `_run_implement()` - Executes implement.md prompt and returns summary of work completed (string output)

Each wrapper will:
1. Accept `worktree` and `task` objects (implement also accepts `spec_path`)
2. Construct a CommandTemplate with the appropriate prompt name, parameters, and json_output flag
3. Execute the command using the existing `_execute_command` method with worktree_path
4. Parse the result based on the prompt's output specification (JSON dict for plan/chore/feature, string for implement)
5. Return the parsed result in the expected format (path string extracted from JSON for plan/chore/feature, summary string for implement)

## Relevant Files

- **agf/workflow/task_handler.py** - Main file where wrapper functions will be added. Contains WorkflowTaskHandler class with existing `_execute_command` method that can be leveraged.
- **agf_commands/plan.md** - Plan prompt specification. Variables: agf_id, prompt. Returns: path to plan file.
- **agf_commands/chore.md** - Chore prompt specification. Variables: agf_id, prompt. Returns: path to chore plan file.
- **agf_commands/feature.md** - Feature prompt specification. Variables: agf_id, prompt. Returns: path to feature plan file.
- **agf_commands/implement.md** - Implement prompt specification. Variables: $ARGUMENTS (plan content). Returns: summary string.
- **agf/agent/models.py** - Contains CommandTemplate model used for prompt execution.
- **agf/agent/base.py** - Contains AgentResult, ModelType, and AgentConfig used in execution.
- **tests/agf/workflow/test_task_handler.py** - Existing test file where new tests will be added.

## Implementation Phases

### Phase 1: Foundation

Understand the existing code structure and prompt specifications:
- Review all four SDLC prompt files to understand their variables and return values
- Study the existing `_execute_command` method to understand how to leverage it
- Determine the appropriate model type for each prompt (THINKING for planning, STANDARD for implementation)

### Phase 2: Core Implementation

Implement the four wrapper functions:
- Create `_run_plan()` wrapper for plan.md
- Create `_run_chore()` wrapper for chore.md
- Create `_run_feature()` wrapper for feature.md
- Create `_run_implement()` wrapper for implement.md
- Ensure each wrapper properly constructs CommandTemplate and parses results

### Phase 3: Integration & Polish

Add comprehensive test coverage:
- Write unit tests for each wrapper function
- Test successful execution paths
- Test error handling scenarios
- Ensure tests follow existing patterns in test_task_handler.py

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Implement _run_plan wrapper function

- Add `_run_plan()` method to WorkflowTaskHandler class
- Method signature: `def _run_plan(self, worktree: Worktree, task: Task) -> str`
- Extract worktree_path using `self._get_worktree_path(worktree)`
- Create CommandTemplate with:
  - prompt="plan"
  - params=[task.task_id, task.description]
  - model=ModelType.THINKING (planning requires deep thinking)
  - json_output=True (returns JSON with path field)
- Call `_execute_command(worktree_path, command_template)`
- Extract and return the plan file path from result.json_output["path"]
- Add docstring explaining the function's purpose and parameters

### 2. Implement _run_chore wrapper function

- Add `_run_chore()` method to WorkflowTaskHandler class
- Method signature: `def _run_chore(self, worktree: Worktree, task: Task) -> str`
- Extract worktree_path using `self._get_worktree_path(worktree)`
- Create CommandTemplate with:
  - prompt="chore"
  - params=[task.task_id, task.description]
  - model=ModelType.STANDARD (chores are simpler than features)
  - json_output=True (returns JSON with path field)
- Call `_execute_command(worktree_path, command_template)`
- Extract and return the chore plan file path from result.json_output["path"]
- Add docstring explaining the function's purpose and parameters

### 3. Implement _run_feature wrapper function

- Add `_run_feature()` method to WorkflowTaskHandler class
- Method signature: `def _run_feature(self, worktree: Worktree, task: Task) -> str`
- Extract worktree_path using `self._get_worktree_path(worktree)`
- Create CommandTemplate with:
  - prompt="feature"
  - params=[task.task_id, task.description]
  - model=ModelType.THINKING (features require careful design)
  - json_output=True (returns JSON with path field)
- Call `_execute_command(worktree_path, command_template)`
- Extract and return the feature plan file path from result.json_output["path"]
- Add docstring explaining the function's purpose and parameters

### 4. Implement _run_implement wrapper function

- Add `_run_implement()` method to WorkflowTaskHandler class
- Method signature: `def _run_implement(self, worktree: Worktree, task: Task, spec_path: str) -> str`
- Extract worktree_path using `self._get_worktree_path(worktree)`
- Read the spec file content from spec_path
- Create CommandTemplate with:
  - prompt="implement"
  - params=[f"@{spec_path}"] (spec file path as argument)
  - model=ModelType.STANDARD (implementation follows established plan)
  - json_output=False (returns summary string)
- Call `_execute_command(worktree_path, command_template)`
- Extract and return the implementation summary from result.output.strip()
- Add docstring explaining the function's purpose and parameters

### 5. Add unit tests for _run_plan

- In tests/agf/workflow/test_task_handler.py, create new test class `TestWorkflowTaskHandlerPromptWrappers`
- Add test method `test_run_plan_success` that:
  - Mocks AgentRunner.run_prompt to return successful result with plan file path
  - Calls handler._run_plan with test parameters
  - Asserts the correct plan file path is returned
  - Verifies CommandTemplate was constructed correctly
- Add test method `test_run_plan_failure` that:
  - Mocks AgentRunner.run_prompt to return failed result
  - Verifies appropriate error handling

### 6. Add unit tests for _run_chore

- Add test method `test_run_chore_success` that:
  - Mocks AgentRunner.run_prompt to return successful result with chore plan file path
  - Calls handler._run_chore with test parameters
  - Asserts the correct chore plan file path is returned
  - Verifies CommandTemplate was constructed with prompt="chore"
- Add test method `test_run_chore_failure` for error handling

### 7. Add unit tests for _run_feature

- Add test method `test_run_feature_success` that:
  - Mocks AgentRunner.run_prompt to return successful result with feature plan file path
  - Calls handler._run_feature with test parameters
  - Asserts the correct feature plan file path is returned
  - Verifies CommandTemplate was constructed with prompt="feature" and model=ModelType.THINKING
- Add test method `test_run_feature_failure` for error handling

### 8. Add unit tests for _run_implement

- Add test method `test_run_implement_success` that:
  - Mocks AgentRunner.run_prompt to return successful result with implementation summary
  - Calls handler._run_implement with test plan content
  - Asserts the correct summary is returned
  - Verifies CommandTemplate was constructed with prompt="implement"
- Add test method `test_run_implement_failure` for error handling

### 9. Run tests and validate implementation

- Execute pytest on the test file: `uv run pytest tests/agf/workflow/test_task_handler.py -v`
- Verify all tests pass
- Check test coverage to ensure all new functions are covered
- Fix any failing tests or coverage gaps

## Testing Strategy

### Unit Tests

Each wrapper function will have dedicated unit tests that:
1. Mock the AgentRunner.run_prompt method to avoid actual agent execution
2. Verify correct CommandTemplate construction (prompt name, params, model type)
3. Test successful execution path with expected return values
4. Test error handling when agent execution fails
5. Follow existing test patterns in test_task_handler.py (using fixtures, mocks, and assertions)

### Edge Cases

- Empty or None parameters (agf_id, prompt, plan_content)
- Agent execution timeout
- Agent returns unexpected output format
- Missing plan file path in agent output
- Invalid JSON parsing (if applicable to future prompts)

## Acceptance Criteria

- [ ] Four protected wrapper functions implemented in WorkflowTaskHandler class
- [ ] `_run_plan()` accepts worktree and task, returns plan file path string (extracted from JSON)
- [ ] `_run_chore()` accepts worktree and task, returns chore plan file path string (extracted from JSON)
- [ ] `_run_feature()` accepts worktree and task, returns feature plan file path string (extracted from JSON)
- [ ] `_run_implement()` accepts worktree, task, and spec_path, returns implementation summary string
- [ ] Each wrapper uses appropriate ModelType (THINKING for plan/feature, STANDARD for chore/implement)
- [ ] All wrappers use CommandTemplate with correct prompt names, parameters, and json_output flags
- [ ] Plan/chore/feature wrappers set json_output=True and extract path from result.json_output["path"]
- [ ] Implement wrapper sets json_output=False and returns result.output.strip()
- [ ] Comprehensive unit tests added with both success and failure scenarios
- [ ] All tests pass when run with pytest
- [ ] Code follows existing patterns and conventions in the codebase
- [ ] All functions have clear docstrings

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify code compiles without syntax errors
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerPromptWrappers -v` - Run new tests and verify they pass
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task_handler tests to ensure no regressions
- `uv run pytest tests/ -v` - Run full test suite to ensure no system-wide regressions

## Notes

### Design Considerations

1. **Protected Functions**: All wrappers are protected (_run_*) because they're internal utilities for the WorkflowTaskHandler class, not part of the public API.

2. **Model Selection**:
   - THINKING model for plan and feature prompts because they require design and architectural thinking
   - STANDARD model for chore and implement prompts because they follow more straightforward execution paths

3. **Return Value Parsing**: Plan, chore, and feature prompts return JSON objects with a "path" field containing the file path. The implement prompt returns a plain string summary. Wrappers handle this correctly by setting json_output=True for plan/chore/feature and extracting result.json_output["path"], while implement uses json_output=False and returns result.output.strip().

4. **Error Handling**: The wrappers delegate error handling to the existing `_execute_command` method, which returns AgentResult. Callers are responsible for checking result.success before using the output.

5. **Future Extensibility**: This design makes it easy to add more SDLC prompt wrappers (e.g., review, test, deploy) following the same pattern.

### Dependencies

No new external dependencies required. All functionality uses existing imports and patterns from the codebase.
