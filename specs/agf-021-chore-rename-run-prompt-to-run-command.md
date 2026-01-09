# Chore: Rename run_prompt to run_command

## Metadata

agf_id: `agf-021`
prompt: `rename method run_prompt in AgentRunner to run_command. Make sure all call references are updated and all tests are still passing.`

## Chore Description

Rename the method `run_prompt` to `run_command` throughout the codebase to better reflect its purpose of executing agent commands. This is a simple refactoring task that requires:

1. Renaming the method definition in the `Agent` protocol (base.py)
2. Renaming the method implementation in both agent implementations (ClaudeCodeAgent and OpenCodeAgent)
3. Renaming the wrapper method in AgentRunner
4. Updating all call sites throughout the codebase
5. Updating references in documentation and spec files
6. Ensuring all tests pass after the rename

The method currently accepts a `CommandTemplate` parameter and executes agent commands with structured prompts, so `run_command` is a more accurate name than `run_prompt`.

## Relevant Files

Use these files to complete the chore:

- **agf/agent/base.py** - Contains the `Agent` protocol definition with the `run_prompt` method signature that needs to be renamed
- **agf/agent/runner.py** - Contains `AgentRunner.run_prompt()` class method that wraps agent execution and needs to be renamed
- **agf/agent/claude_code.py** - Contains `ClaudeCodeAgent.run_prompt()` implementation that needs to be renamed
- **agf/agent/opencode.py** - Contains `OpenCodeAgent.run_prompt()` implementation that needs to be renamed
- **agf/workflow/task_handler.py** - Contains a call to `AgentRunner.run_prompt()` at line 234 that needs to be updated
- **tests/agf/workflow/test_task_handler.py** - Contains multiple test mocks for `mock_agent_runner.run_prompt` that need to be updated
- **specs/agf-018-plan-sdlc-prompt-wrappers.md** - Documentation referencing `AgentRunner.run_prompt` that needs to be updated
- **specs/agf-016-plan-unify-prompt-processing.md** - Documentation extensively referencing `run_prompt` that needs to be updated
- **prompts/agf-workflow-task-handler.md** - Prompt file referencing `AgentRunner.run_prompt` that needs to be updated
- **prompts/agf-add-agents-template.md** - Prompt file referencing `run_prompt` protocol function that needs to be updated

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Agent Protocol Definition

- Rename `run_prompt` method to `run_command` in the `Agent` protocol in `agf/agent/base.py` (line 206)
- Update the method docstring to reflect the new name if it references itself

### 2. Update AgentRunner Class Method

- Rename `AgentRunner.run_prompt()` to `AgentRunner.run_command()` in `agf/agent/runner.py` (line 54)
- Update the docstring to reflect the new method name
- Update the call to `agent.run_prompt()` to `agent.run_command()` at line 78

### 3. Update ClaudeCodeAgent Implementation

- Rename `run_prompt()` method to `run_command()` in `agf/agent/claude_code.py` (line 93)
- Update the method docstring to reflect the new name if needed

### 4. Update OpenCodeAgent Implementation

- Rename `run_prompt()` method to `run_command()` in `agf/agent/opencode.py` (line 93)
- Update the method docstring to reflect the new name if needed

### 5. Update Call Sites in Production Code

- Update `AgentRunner.run_prompt()` call to `AgentRunner.run_command()` in `agf/workflow/task_handler.py` at line 234

### 6. Update Test Files

- Update all `mock_agent_runner.run_prompt` references to `mock_agent_runner.run_command` in `tests/agf/workflow/test_task_handler.py`
- This includes both `side_effect` assignments and `assert_called_once()` assertions
- Expected locations: lines 285, 326, 465, 474, 475, 503, 512, 513, 541, 550, 551, 580, 591, 592, 625, 635, 636, 666, 675, 676, 706, 715, 716, 746, 755, 756, 883, 897, 959, 973, 1029, 1043, 1106, 1150, 1204

### 7. Update Documentation and Spec Files

- Update `AgentRunner.run_prompt` references to `AgentRunner.run_command` in `specs/agf-018-plan-sdlc-prompt-wrappers.md` (lines 143, 148, 154, 163, 172, 190)
- Update all `run_prompt` references to `run_command` in `specs/agf-016-plan-unify-prompt-processing.md` (multiple locations throughout the file)
- Update `AgentRunner.run_prompt` reference in `prompts/agf-workflow-task-handler.md` (line 16)
- Update `run_prompt` references in `prompts/agf-add-agents-template.md` (lines 15, 16, 17)

### 8. Validate Changes

- Run the Python syntax check to ensure all files compile correctly
- Run the full test suite to verify all tests pass
- Grep the codebase to ensure no remaining references to `run_prompt` exist

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/agent/base.py agf/agent/runner.py agf/agent/claude_code.py agf/agent/opencode.py agf/workflow/task_handler.py` - Test to ensure the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Test to ensure workflow tests pass
- `uv run pytest tests/agf/agent/ -v` - Test to ensure agent tests pass
- `uv run pytest` - Run full test suite to ensure all tests pass
- `grep -r "run_prompt" agf/ tests/ --include="*.py"` - Verify no remaining references to `run_prompt` in Python code
- `grep -r "run_prompt" specs/ prompts/ --include="*.md"` - Verify no remaining references to `run_prompt` in documentation

## Notes

This is a straightforward rename refactoring with no behavioral changes. The method signature and functionality remain identical - only the name changes from `run_prompt` to `run_command` to better reflect that it executes commands based on CommandTemplate objects.

The rename must be applied consistently across:
1. Protocol definition
2. Agent implementations (2 files)
3. AgentRunner wrapper
4. All call sites (production code and tests)
5. Documentation and spec files

Pay special attention to test files where the method is mocked - both the mock method name and assertion method names need to be updated.
