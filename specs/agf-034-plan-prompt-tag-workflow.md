# Plan: Prompt Tag Direct Execution Workflow

## Metadata

agf_id: `agf-034`
prompt: `whenever task is tagged with prompt the description of the task is passed in as prompt. These tasks do not need to call command prompt, they call AgentRun.run method on the agent. The configuration is handled the same way as the run_command method call.`
task_type: feature
complexity: medium

## Task Description

Implement a new task type "prompt" that allows tasks to pass their description directly to `AgentRunner.run()` method instead of using the standard command template workflow. When a task is tagged with `{prompt}`, the task handler should:

1. Skip the planning/implementation phases (no spec file needed)
2. Pass the task description directly to `AgentRunner.run()` as the prompt
3. Apply the same configuration (agent selection, model, working directory, etc.) as `run_command()`
4. Proceed to commit phase after execution (like the build workflow)

This provides a lightweight execution path for simple tasks where the task description itself is sufficient as a prompt.

## Objective

Add support for the "prompt" tag that enables direct prompt execution, bypassing the planning and implementation phases while maintaining the same agent configuration and commit workflow as other task types.

## Problem Statement

Currently, all task types (chore, feature, plan, build) follow structured workflows that require either:
- A planning phase that creates a spec file followed by implementation phase (chore, feature, plan)
- A build prompt that formats the description into a command template (build)

There's no way to simply pass a task description directly to an agent as a raw prompt. This limits flexibility for simpler tasks or tasks that are already well-defined prompts.

## Solution Approach

1. Add "prompt" to the list of valid task types in `_get_task_type()`
2. Create a new `_run_prompt()` method that calls `AgentRunner.run()` directly
3. Add a new branch in `handle_task()` for "prompt" task type that:
   - Calls `_run_prompt()` with the task description
   - Proceeds directly to commit phase (like build)
4. Configure the agent execution using the same pattern as `_execute_command()`:
   - Use worktree.agent if set, else config.agent
   - Resolve model from configuration
   - Apply working directory and permissions

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - Main file to modify; contains `WorkflowTaskHandler` class with `_get_task_type()`, `handle_task()`, and execution methods
- `agf/agent/runner.py` - Reference for `AgentRunner.run()` method signature and behavior
- `agf/agent/base.py` - Reference for `AgentConfig`, `AgentResult`, and `ModelType` definitions
- `tests/agf/workflow/test_task_handler.py` - Add tests for the new prompt workflow

## Implementation Phases

### Phase 1: Foundation

Add "prompt" to valid task types in `_get_task_type()` method.

### Phase 2: Core Implementation

Create `_run_prompt()` method and add execution branch in `handle_task()`.

### Phase 3: Integration & Polish

Add comprehensive tests and ensure configuration handling matches existing patterns.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Task Type Detection

- Modify `_get_task_type()` in `agf/workflow/task_handler.py` to include "prompt" in the valid_types list
- Ensure the docstring is updated to reflect the new task type

### 2. Create Prompt Execution Method

- Add new `_run_prompt()` method in `WorkflowTaskHandler` class
- Method signature: `def _run_prompt(self, worktree: Worktree, task: Task) -> AgentResult:`
- Determine effective agent (worktree.agent or config.agent)
- Validate agent exists in config (same pattern as `_execute_command`)
- Resolve model from configuration using `ModelType.STANDARD` as default
- Create `AgentConfig` with working directory, skip_permissions, and logger
- Call `AgentRunner.run()` with task.description as the prompt
- Log execution and result (same pattern as `_execute_command`)
- Return the `AgentResult`

### 3. Add Prompt Task Type Handling in handle_task

- In the `handle_task()` method, add a new conditional branch for "prompt" task type
- Place it alongside the "build" workflow branch since both skip planning/implementation phases
- The workflow should be: `_run_prompt()` -> `_create_commit()`
- Follow the same error handling pattern as other task types
- Update the docstring to document the prompt workflow

### 4. Add Unit Tests for Prompt Task Type Detection

- Add test `test_get_task_type_prompt` in `TestWorkflowTaskHandlerTaskType` class
- Add test `test_get_task_type_prompt_with_other_tags` to verify prompt detection with mixed tags
- Ensure prompt takes precedence when appearing first in tags list

### 5. Add Unit Tests for _run_prompt Method

- Create new test class `TestWorkflowTaskHandlerPromptExecution` or add to existing `TestWorkflowTaskHandlerPromptWrappers`
- Add test `test_run_prompt_success` - verify AgentRunner.run is called with task description
- Add test `test_run_prompt_uses_worktree_agent` - verify worktree.agent override works
- Add test `test_run_prompt_uses_config_agent_fallback` - verify falls back to config.agent

### 6. Add Integration Tests for Prompt Workflow

- Add test `test_handle_task_prompt_workflow_success` in `TestWorkflowTaskHandlerSDLCFlow`
- Verify the complete workflow: prompt execution -> commit
- Verify only 2 agent calls are made (prompt + commit)
- Add test `test_handle_task_prompt_workflow_failure` for error handling

### 7. Validate Implementation

- Run all tests to ensure no regressions
- Verify type checking passes
- Verify the code compiles

## Testing Strategy

Unit tests should cover:
1. Task type detection for "prompt" tag (isolated and mixed tags)
2. `_run_prompt()` method with successful execution
3. `_run_prompt()` method with agent override from worktree
4. `_run_prompt()` method with model configuration
5. Complete workflow integration: prompt + commit phases
6. Error handling for failed prompt execution

Edge cases to test:
- Prompt tag with other non-type tags (e.g., `{prompt, urgent}`)
- Prompt tag with other type tags (priority order)
- Empty task description handling
- Agent not found in config (fallback behavior)

## Acceptance Criteria

- [ ] Tasks tagged with `{prompt}` are detected as "prompt" task type
- [ ] `_run_prompt()` method calls `AgentRunner.run()` with task description
- [ ] Prompt workflow skips planning and implementation phases
- [ ] Prompt workflow proceeds to commit phase after execution
- [ ] Agent configuration (worktree override, model, working dir) matches existing patterns
- [ ] Error handling follows existing error handling patterns
- [ ] All existing tests pass (no regressions)
- [ ] New unit tests for prompt task type detection
- [ ] New unit tests for `_run_prompt()` method
- [ ] New integration tests for prompt workflow

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify syntax
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run task handler tests
- `uv run pytest tests/ -v` - Run all tests to verify no regressions
- `uv run ruff check agf/workflow/task_handler.py` - Check code style

## Notes

- The `AgentRunner.run()` method is marked as deprecated but is still functional and appropriate for this use case since we're passing a raw prompt rather than a structured command
- The prompt workflow is similar to the build workflow in that it skips the planning/implementation phases
- Consider whether future enhancements might allow specifying model type via additional tags (e.g., `{prompt, thinking}`)
- The task description is used verbatim as the prompt; no additional formatting is applied
