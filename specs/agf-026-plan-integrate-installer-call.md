# Plan: Integrate Installer Call After Worktree Initialization

## Metadata

agf_id: `agf-026`
prompt: `in 'agf/workflow/task_handler.py' we need to call the installer to make sure that all the command this project offers are installed in the target project. Add the call to installer after intialize_worktree finished`
task_type: chore
complexity: simple

## Task Description

Integrate the `Installer` class into the `WorkflowTaskHandler` to ensure that all AGF command prompts are properly installed in the worktree after initialization. This will guarantee that the agent has access to all necessary commands when executing tasks.

## Objective

Add a call to `Installer.install_commands()` in the `handle_task` method of `WorkflowTaskHandler`, immediately after `_initialize_worktree()` completes successfully. This ensures commands are synchronized to the worktree before task execution begins.

## Relevant Files

Use these files to complete the task:

- `agf/workflow/task_handler.py` - Contains the `WorkflowTaskHandler` class where the installer call needs to be added (specifically in the `handle_task` method around line 440)
- `agf/installer.py` - Contains the `Installer` class with the `install_commands()` method that needs to be invoked
- `agf/config/models.py` - Contains `EffectiveConfig` which is needed to instantiate the Installer
- `agf/task_manager/models.py` - Contains `Worktree` model which is needed to instantiate the Installer

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Import Statement

- Add `from agf.installer import Installer` to the imports section at the top of `agf/workflow/task_handler.py`

### 2. Call Installer After Worktree Initialization

- Locate the `handle_task` method in `WorkflowTaskHandler` class (around line 415)
- After the `_initialize_worktree(worktree)` call completes (around line 440), add:
  - Create an `Installer` instance: `installer = Installer(self.config, worktree)`
  - Call the install method: `copied_files = installer.install_commands()`
  - Add logging to track installation: `self._log(f"Installed {len(copied_files)} command files to worktree")`
- Ensure this happens before updating task status to `IN_PROGRESS`

### 3. Update Worktree Directory Path

- Before creating the Installer instance, ensure the worktree has its `directory_path` set
- The `worktree` parameter passed to `handle_task` may not have `directory_path` populated
- Set it using: `worktree.directory_path = worktree_path` (where `worktree_path` is returned from `_initialize_worktree`)
- This ensures the Installer can determine the correct target directory

### 4. Validate the Implementation

- Run the compilation check to ensure no syntax errors
- Run the full test suite to ensure no regressions
- Manually verify the logic flow makes sense

## Acceptance Criteria

- [ ] `Installer` is imported in `task_handler.py`
- [ ] Installer instance is created with correct config and worktree after `_initialize_worktree()` completes
- [ ] `install_commands()` is called and result is logged
- [ ] The worktree's `directory_path` is properly set before passing to Installer
- [ ] Installation happens before task status changes to `IN_PROGRESS`
- [ ] Code compiles without errors
- [ ] Existing tests continue to pass

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/workflow/task_handler.py` - Verify the module compiles without syntax errors
- `uv run python -c "from agf.workflow.task_handler import WorkflowTaskHandler; print('Import successful')"` - Verify the class can be imported
- `uv run pytest tests/` - Run all tests to ensure no regressions

## Notes

- The `Installer` class already implements all necessary functionality via `install_commands()`
- The worktree's `directory_path` field needs to be populated before creating the Installer instance
- This is a critical integration point that ensures commands are available to agents in worktrees
- The installation should happen early in the task execution flow, before any agent commands are executed
- If installation fails, consider whether it should fail the entire task or just log a warning
