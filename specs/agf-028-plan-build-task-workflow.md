# Plan: Add build task type to workflow

## Metadata

agf_id: `agf-028`
prompt: `adjust workflow in task_handler.py. If task is tagged with "build" we skip both chore/feature/plan and implement phases and only call build prompt via the wrapper.`
task_type: enhancement
complexity: simple

## Task Description

Modify the `WorkflowTaskHandler.handle_task()` method to support a new task type "build". When a task is tagged with "build", the workflow should skip both the planning phase (chore/feature/plan prompts) and the implementation phase, and instead only execute the build prompt via the existing `_run_build()` wrapper method, followed by the commit phase.

## Objective

When this plan is complete, tasks tagged with "build" will execute a streamlined workflow:
1. Initialize worktree
2. Update task status to IN_PROGRESS
3. Run build prompt (skipping plan and implement phases)
4. Create commit
5. Update task status to COMPLETED
6. Auto-create GitHub PR if all tasks completed

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - Contains `WorkflowTaskHandler` class with `handle_task()` method (lines 479-602) and `_get_task_type()` method (lines 448-462) that need modification. The `_run_build()` method already exists (lines 352-374).
- `tests/agf/workflow/test_task_handler.py` - Contains existing tests for task type detection in `TestWorkflowTaskHandlerTaskType` class (lines 1021-1084) and SDLC flow tests in `TestWorkflowTaskHandlerSDLCFlow` class (lines 1086-1587). New tests should follow these patterns.

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update `_get_task_type()` to recognize "build" tag

- In `agf/workflow/task_handler.py`, locate the `_get_task_type()` method (lines 448-462)
- Add "build" to the `valid_types` list on line 458: `valid_types = ["chore", "feature", "plan", "build"]`
- Update the method's docstring to include "build" as a valid return value

### 2. Add build workflow branch in `handle_task()` method

- In `agf/workflow/task_handler.py`, locate the `handle_task()` method (lines 479-602)
- After detecting task type (line 541), add a conditional branch for "build" tasks
- The build workflow should:
  - Call `self._run_build(worktree, task)` to execute the build prompt
  - Skip directly to the commit phase (Phase 3)
  - The existing planning phase (Phase 1) and implementation phase (Phase 2) should only run for non-build tasks
- Update the docstring to document the build workflow variant

### 3. Add unit tests for `_get_task_type()` with "build" tag

- In `tests/agf/workflow/test_task_handler.py`, add test in `TestWorkflowTaskHandlerTaskType` class
- Add `test_get_task_type_build` test to verify "build" tag is detected correctly
- Verify "build" takes precedence when mixed with other non-type tags

### 4. Add integration tests for build workflow in `handle_task()`

- In `tests/agf/workflow/test_task_handler.py`, add tests in `TestWorkflowTaskHandlerSDLCFlow` class
- Add `test_handle_task_sdlc_flow_build_success` test:
  - Create a task with `tags=["build"]`
  - Mock agent to return successful build result and commit result
  - Verify agent was called exactly 2 times (build, commit) not 3 times (plan, implement, commit)
  - Verify task completed successfully with commit SHA
- Add `test_handle_task_build_phase_failure` test:
  - Verify proper error handling when build phase fails
  - Verify error message includes "build phase failed"

### 5. Validate the implementation

- Run tests to ensure all tests pass including the new tests
- Run type checking to ensure no type errors

## Acceptance Criteria

- Tasks tagged with "build" are detected by `_get_task_type()` and return "build"
- Build tasks skip the planning phase (no plan/chore/feature prompt executed)
- Build tasks skip the implementation phase (no implement prompt executed)
- Build tasks execute only: build prompt -> commit
- Build tasks complete successfully with proper status updates and commit SHA
- Build phase failures are properly handled and reported as "Build phase failed: ..."
- All existing tests continue to pass (no regression)
- Auto-PR creation still works after build task completes (if all tasks completed)

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the code compiles
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerTaskType -v` - Run task type detection tests
- `uv run pytest tests/agf/workflow/test_task_handler.py::TestWorkflowTaskHandlerSDLCFlow -v` - Run SDLC flow tests
- `uv run pytest tests/agf/workflow/test_task_handler.py -v` - Run all task handler tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The build workflow is designed for simpler tasks that don't require a planning phase
- The `_run_build()` method already exists and is fully tested (see `test_run_build_success` and `test_run_build_uses_worktree_id` tests)
- Build tasks use `ModelType.STANDARD` (not `THINKING`) since they are direct implementations
- The build prompt combines planning and implementation into a single execution
