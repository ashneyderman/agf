# Plan: Prompt Task Type Support

## Metadata

agf_id: `agf-033`
prompt: `whenever task is tagged with prompt the description of the task is passed in as prompt. These tasks do not need to call command prompt, they call AgentRun.run method on the agent. The configuration is handled the same way as the run_command method call.`
task_type: feature
complexity: medium

## Task Description

Add support for a new task type "prompt" that allows task descriptions to be passed directly to the agent's `run()` method instead of being formatted as structured commands. When a task has the "prompt" tag, the workflow handler should:

1. Recognize "prompt" as a valid task type
2. Pass the task description directly to `AgentRunner.run()`
3. Handle configuration (model selection, working directory, skip_permissions, logging) the same way as `run_command()` does

This differs from other task types (plan, chore, feature, build) which use `run_command()` with structured `CommandTemplate` objects that format prompts as `/{namespace}:{prompt} {params}`.

## Objective

Enable tasks to execute arbitrary prompts directly through the agent without going through the skill/command system, providing flexibility for ad-hoc agent invocations while maintaining consistent configuration handling.

## Problem Statement

Currently, all task types (plan, chore, feature, build) execute through `run_command()` which formats prompts as structured commands (`/{namespace}:{prompt} {params}`). There's no way to pass a raw prompt directly to an agent, which limits flexibility for tasks that don't fit into predefined command templates.

## Solution Approach

1. Add "prompt" to the list of valid task types in `_get_task_type()`
2. Create a new `_run_prompt()` method that:
   - Constructs the `AgentConfig` the same way `_execute_command()` does
   - Determines the effective agent (worktree.agent override or config.agent)
   - Resolves the model from configuration (using a default model type)
   - Calls `AgentRunner.run()` directly with the task description
3. Update `handle_task()` to call `_run_prompt()` when the task type is "prompt"
4. Define the workflow for prompt tasks (prompt execution only, no planning/implementation phases)

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - Main handler file where `_get_task_type()`, `_execute_command()`, and `handle_task()` are defined. This is where the "prompt" task type support will be added.
- `agf/agent/runner.py` - Contains `AgentRunner.run()` method that will be called for prompt tasks
- `agf/agent/base.py` - Contains `AgentConfig`, `AgentResult`, and `ModelType` definitions
- `tests/agf/workflow/test_task_handler.py` - Test file for WorkflowTaskHandler, where new tests will be added

## Implementation Phases

### Phase 1: Foundation

- Add "prompt" to the valid task types list
- Create the `_run_prompt()` method with proper configuration handling

### Phase 2: Core Implementation

- Update `handle_task()` to handle "prompt" task type
- Define the workflow for prompt tasks (single execution phase followed by commit)

### Phase 3: Integration & Polish

- Add comprehensive unit tests for the new functionality
- Verify all tests pass
- Ensure proper error handling

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add "prompt" to Valid Task Types

- In `agf/workflow/task_handler.py`, update `_get_task_type()` method
- Add "prompt" to the `valid_types` list: `["chore", "feature", "plan", "build", "prompt"]`

### 2. Create `_run_prompt()` Method

- Add new method `_run_prompt(self, worktree: Worktree, task: Task) -> str` in `WorkflowTaskHandler`
- Implement agent and model resolution (same logic as `_execute_command()`):
  - Determine effective agent: `worktree.agent if worktree.agent else self.config.agent`
  - Validate agent exists in config
  - Get model from agent config (use STANDARD as default model type)
- Create `AgentConfig` with same parameters as `_execute_command()`:
  - `working_dir` = worktree_path
  - `skip_permissions` = True
  - `logger` = self._log
  - `model` = resolved model string
- Call `AgentRunner.run()` with:
  - `agent_name` = effective_agent
  - `prompt` = task.description
  - `config` = constructed AgentConfig
- Return `result.output.strip()`

### 3. Update `handle_task()` for Prompt Task Type

- In the `handle_task()` method, add handling for the "prompt" task type
- Add a new branch in the workflow execution section:
  ```python
  elif task_type == "prompt":
      # Prompt workflow: run prompt -> commit phase
      try:
          self._run_prompt(worktree, task)
      except Exception as e:
          raise Exception(f"Prompt phase failed: {str(e)}") from e

      # Commit phase
      try:
          commit_info = self._create_commit(worktree, task)
          commit_sha = commit_info.get("commit_sha")
      except Exception as e:
          raise Exception(f"Commit phase failed: {str(e)}") from e
  ```

### 4. Add Unit Tests for `_run_prompt()`

- Add test class or methods in `tests/agf/workflow/test_task_handler.py`
- Test successful prompt execution:
  - Mock `AgentRunner.run` to return success
  - Verify prompt is passed as task.description
  - Verify correct agent and model resolution
  - Verify AgentConfig parameters (working_dir, skip_permissions, model)
- Test prompt with worktree agent override:
  - Verify worktree.agent is used when set
- Test prompt task type detection:
  - Verify `_get_task_type()` returns "prompt" for tasks with prompt tag

### 5. Add Integration Tests for handle_task() with Prompt

- Test complete workflow for prompt-tagged task
- Verify task status transitions: NOT_STARTED -> IN_PROGRESS -> COMPLETED
- Test error handling when prompt execution fails
- Test commit creation after successful prompt execution

### 6. Validate the Implementation

- Run all tests to ensure no regressions
- Verify the code compiles without errors

## Testing Strategy

1. **Unit Tests for `_run_prompt()`**:
   - Test that `AgentRunner.run()` is called with correct parameters
   - Test agent override from worktree
   - Test model resolution from configuration
   - Test output handling

2. **Unit Tests for `_get_task_type()`**:
   - Test that "prompt" tag is recognized
   - Test priority when multiple tags are present

3. **Integration Tests for `handle_task()`**:
   - Test complete prompt task workflow
   - Test status updates
   - Test error handling and failure states
   - Test commit creation after prompt execution

## Acceptance Criteria

- [x] "prompt" is recognized as a valid task type by `_get_task_type()`
- [x] `_run_prompt()` method exists and calls `AgentRunner.run()` with task description
- [x] Configuration (model, working_dir, skip_permissions, logger) is handled the same way as `run_command()`
- [x] `handle_task()` correctly routes "prompt" tasks to the new workflow
- [x] Prompt tasks follow the workflow: prompt execution -> commit
- [x] All existing tests continue to pass
- [x] New unit tests cover the prompt task type functionality

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify task_handler.py compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run task handler tests
- `uv run pytest tests/ -v` - Run all tests to verify no regressions

## Notes

- The prompt task type differs from other types by not requiring a planning phase
- The workflow is simpler: just execute the prompt and commit
- Model selection uses STANDARD by default (same as build tasks)
- No new dependencies required
