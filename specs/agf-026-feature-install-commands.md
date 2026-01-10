# Plan: Install AGF Commands to Worktree

## Metadata

agf_id: `agf-026`
prompt: `the installer has to implement a method, that verifies wether all prompts from agf_commands directory are installed in the worktree_path of the project_dir. If they are not they have to be copied over to {worktree_path}/.claude/commands/AGF|.opencode/command)/{namespace}/ if they do not exist there or if any of them are outdated. Make note in {worktree_path}/.gitignore if these temporary directories are not listed in the file already.`
task_type: feature
complexity: medium

## Task Description

Implement a method in the `Installer` class that synchronizes AGF command prompts from the source `agf_commands` directory to the appropriate agent-specific commands directory within a git worktree. The method must:

1. Determine the correct target directory based on the agent type:
   - Claude Code: `{worktree_path}/.claude/commands/{namespace}/`
   - OpenCode: `{worktree_path}/.opencode/command/{namespace}/`
2. Compare source files with target files to detect missing or outdated commands
3. Copy commands that are missing or have been updated in the source
4. Ensure the `.gitignore` file in the worktree excludes the agent-specific command directories

## Objective

When this plan is complete, the `Installer` class will have a method (`install_commands` or similar) that can be called to ensure all AGF command prompts are properly installed in a worktree, enabling the agent to use them during SDLC operations.

## Problem Statement

Currently, the AGF system uses symlinks (`.claude/commands/agf -> ../../agf_commands`) in the main project directory to make commands available to agents. However, worktrees are separate directories that need their own copies of these commands. Without a mechanism to install/sync commands to worktrees, agents running in worktrees won't have access to the AGF command prompts.

## Solution Approach

Implement a file synchronization method in the `Installer` class that:
1. Reads the source `agf_commands` directory from the AGF project
2. Determines the target directory based on the current agent configuration
3. Compares files by content hash or modification time to detect changes
4. Copies new or updated files to the target directory
5. Ensures proper `.gitignore` entries exist

## Relevant Files

Use these files to complete the task:

- `agf/installer.py` - The Installer class that will be extended with the new method
- `agf/config/models.py` - Contains `EffectiveConfig` with `agent`, `commands_namespace`, and `project_dir` fields
- `agf/task_manager/models.py` - Contains `Worktree` with `directory_path` field
- `agf/agent/base.py` - Contains `AgentType` enum defining "claude-code" and "opencode"
- `tests/agf/test_installer.py` - Existing test file to extend with new tests
- `agf_commands/*.md` - Source command files to be installed

### New Files

None - all changes will be made to existing files.

## Implementation Phases

### Phase 1: Foundation

- Define helper methods for path resolution (source dir, target dir)
- Define method to determine agent-specific command directory structure

### Phase 2: Core Implementation

- Implement file comparison logic (check if file exists and is up-to-date)
- Implement file copy operation with directory creation
- Implement `.gitignore` update logic

### Phase 3: Integration & Polish

- Integrate all components into the main `install_commands` method
- Add comprehensive tests
- Handle edge cases (empty directories, missing permissions, etc.)

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Helper Methods for Path Resolution

- Add a method `_get_agf_commands_source_dir()` that returns the path to the `agf_commands` directory relative to the AGF project (can use `__file__` to locate the agf package)
- Add a method `_get_target_commands_dir()` that returns the target directory path based on:
  - `self._worktree.directory_path` for the worktree path
  - `self._config.agent` to determine agent type ("claude-code" → `.claude/commands/`, "opencode" → `.opencode/command/`)
  - `self._config.commands_namespace` for the namespace subdirectory

### 2. Add File Comparison Logic

- Add a method `_is_file_outdated(source_path: Path, target_path: Path) -> bool` that:
  - Returns `True` if target doesn't exist
  - Returns `True` if source is newer than target (using `os.path.getmtime`)
  - Returns `False` otherwise
- Consider using content comparison (file hash) as an alternative or fallback

### 3. Implement Command Installation Method

- Add the main method `install_commands() -> list[str]` that:
  - Gets the source directory using `_get_agf_commands_source_dir()`
  - Gets the target directory using `_get_target_commands_dir()`
  - Creates the target directory if it doesn't exist (`os.makedirs(..., exist_ok=True)`)
  - Iterates over all `.md` files in the source directory
  - For each file, checks if it needs to be copied using `_is_file_outdated()`
  - Copies files that are missing or outdated using `shutil.copy2()` to preserve timestamps
  - Returns a list of files that were copied

### 4. Implement Gitignore Update Logic

- Add a method `_ensure_gitignore_entry(entry: str)` that:
  - Reads the `.gitignore` file at `{worktree_path}/.gitignore`
  - Checks if the entry already exists (accounting for trailing slashes, etc.)
  - Appends the entry if not present
  - Creates the file if it doesn't exist
- The entry should be the agent-specific directory (e.g., `.claude/commands/agf/` or `.opencode/command/agf/`)
- Call this method from `install_commands()` after successful installation

### 5. Add Unit Tests

- Add tests in `tests/agf/test_installer.py`:
  - Test `_get_target_commands_dir()` for both claude-code and opencode agents
  - Test `_is_file_outdated()` with various scenarios (missing file, older file, newer file, same file)
  - Test `install_commands()` with a mocked filesystem (using `tmp_path` fixture)
  - Test `.gitignore` update logic (entry missing, entry present, file doesn't exist)
- Use `pytest` fixtures for test setup

### 6. Validate the Implementation

- Run type checker and linter
- Run all tests to ensure no regressions
- Manually verify the behavior with sample data

## Testing Strategy

Unit tests will cover:

1. **Path Resolution Tests**
   - `_get_agf_commands_source_dir()` returns valid path to agf_commands
   - `_get_target_commands_dir()` returns correct path for claude-code agent
   - `_get_target_commands_dir()` returns correct path for opencode agent
   - Custom namespace is correctly applied

2. **File Comparison Tests**
   - Target file doesn't exist → returns True
   - Target file is older than source → returns True
   - Target file is same age or newer → returns False

3. **Installation Tests**
   - Empty source directory → no files copied
   - New files copied to target
   - Outdated files updated
   - Up-to-date files not copied
   - Target directory created if missing

4. **Gitignore Tests**
   - Entry added when .gitignore doesn't exist
   - Entry added when .gitignore exists but entry missing
   - Entry not duplicated when already present
   - Works with various entry formats (with/without trailing slash)

## Acceptance Criteria

- [ ] `Installer` class has `install_commands()` method that returns list of copied files
- [ ] Commands are installed to correct agent-specific directory based on config
- [ ] Only missing or outdated files are copied (efficiency)
- [ ] `.gitignore` is updated with the appropriate entry
- [ ] All new functionality has unit tests with >90% coverage
- [ ] All existing tests continue to pass
- [ ] Code compiles without type errors
- [ ] Works for both claude-code and opencode agents

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/installer.py` - Verify the installer module compiles
- `uv run python -c "from agf.installer import Installer; print('Import successful')"` - Verify the Installer class can be imported
- `uv run pytest tests/agf/test_installer.py -v` - Run the installer tests
- `uv run pytest` - Run all tests to ensure no regressions

## Notes

- The `agf_commands` directory location can be determined using `Path(__file__).parent.parent / "agf_commands"` from within the installer module
- Use `shutil.copy2()` instead of `shutil.copy()` to preserve file metadata (modification times)
- The `.gitignore` entry should include the full path from the worktree root (e.g., `.claude/commands/agf/`)
- Consider adding logging for visibility into what files are being copied
- Edge case: If `directory_path` is `None` on the Worktree, the method should raise a clear error
