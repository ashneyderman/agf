# Plan: Refactor Installer to Use Symlinks

## Metadata

agf_id: `agf-031`
prompt: `change the installer to do the following (feel free to remove current implementation): 1. copy all files in .agf_config to {worktree_path}/.agf. 2. make a soft link to point {worktree_path}/.claude/commands/{namespace} to {worktree_path}/.agf/claude/commands. 3. make a soft link to point {worktree_path}/.opencode/command/{namespace} to {worktree_path}/.agf/opencode/commands. 4. make sure that {worktree_path}/.gitignore contains entries for .agf/, .claude/commands/{namespace} and .opencode/command/{namespace}. If any on the entries are missing add them.`
task_type: refactor
complexity: medium

## Task Description

Refactor the `Installer` class in `agf/installer.py` to change the command installation mechanism from individual file copying to a directory copy + symlink approach. The new implementation will:

1. Copy the entire `.agf_config/` directory contents to `{worktree_path}/.agf/`
2. Create symbolic links from agent-specific command directories to the copied `.agf` structure
3. Update `.gitignore` with entries for all three directories (`.agf/`, `.claude/commands/{namespace}`, `.opencode/command/{namespace}`)

## Objective

Replace the current file-by-file copy approach with a more maintainable symlink-based approach that:
- Reduces redundancy by storing a single copy of configuration files
- Supports both claude-code and opencode simultaneously via symlinks
- Properly ignores all installed paths in `.gitignore`

## Problem Statement

The current installer implementation:
- Copies individual `.md` files from `agf_commands/` to agent-specific target directories
- Only sets up commands for the currently configured agent (not both)
- Uses timestamp-based file comparison to determine if files need updating
- Only adds a single entry to `.gitignore` based on the active agent

The new approach provides:
- A centralized copy of all configuration in `.agf/`
- Symlinks that allow both agents to work without duplicating files
- Complete `.gitignore` coverage for all installed paths

## Solution Approach

1. Replace the source directory from `agf_commands/` to `.agf_config/` (located relative to the installer module)
2. Replace file-by-file copying with `shutil.copytree()` to copy the entire directory structure
3. Create symlinks using `os.symlink()` for both agent command directories
4. Update the `.gitignore` logic to handle multiple entries (`.agf/`, `.claude/commands/{namespace}`, `.opencode/command/{namespace}`)

## Relevant Files

Use these files to complete the task:

- `agf/installer.py` - Main file to refactor. Contains the `Installer` class with `install_commands()` and `_ensure_gitignore_entry()` methods that need to be rewritten.
- `tests/agf/test_installer.py` - Test file that needs to be updated to reflect the new behavior. Many existing tests will need modification.
- `.agf_config/` - Source directory containing the command files organized by agent type (claude/commands/, opencode/commands/)
- `agf_commands/` - Old source directory that may become obsolete after this refactor
- `agf/config/models.py` - Contains `EffectiveConfig` with `commands_namespace` property used for symlink paths

## Implementation Phases

### Phase 1: Foundation

- Update the source directory resolution to point to `.agf_config/`
- Implement the directory copy logic using `shutil.copytree()`

### Phase 2: Core Implementation

- Implement symlink creation for both `.claude/commands/{namespace}` and `.opencode/command/{namespace}`
- Handle existing symlinks (remove and recreate if they exist but point elsewhere)
- Refactor `_ensure_gitignore_entry()` to handle multiple entries

### Phase 3: Integration & Polish

- Update all tests to reflect the new behavior
- Remove obsolete helper methods
- Ensure proper error handling and logging

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Source Directory Resolution

- Modify `_get_agf_commands_source_dir()` to return the path to `.agf_config/` instead of `agf_commands/`
- Rename the method to `_get_agf_config_source_dir()` to better reflect its purpose

### 2. Implement Directory Copy Logic

- Remove `_is_file_outdated()` method (no longer needed)
- Create new helper method `_copy_agf_config()` that:
  - Gets the target path: `{worktree_path}/.agf`
  - Removes existing `.agf` directory if it exists
  - Uses `shutil.copytree()` to copy the entire `.agf_config/` directory

### 3. Implement Symlink Creation

- Create new helper method `_create_command_symlinks()` that:
  - Creates parent directories for `.claude/commands/` and `.opencode/command/` if they don't exist
  - Removes existing symlinks at `{namespace}` paths if they exist
  - Creates symlink: `{worktree_path}/.claude/commands/{namespace}` → `{worktree_path}/.agf/claude/commands`
  - Creates symlink: `{worktree_path}/.opencode/command/{namespace}` → `{worktree_path}/.agf/opencode/commands`
  - Use relative symlinks where possible for portability

### 4. Update Gitignore Logic

- Refactor `_ensure_gitignore_entry()` to handle multiple entries:
  - `.agf/`
  - `.claude/commands/{namespace}/`
  - `.opencode/command/{namespace}/`
- Extract entry checking logic into a helper method `_gitignore_has_entry()`
- Create helper method `_add_gitignore_entries()` to add missing entries

### 5. Refactor install_commands Method

- Update `install_commands()` to:
  1. Call `_copy_agf_config()` to copy the config directory
  2. Call `_create_command_symlinks()` to create symlinks
  3. Call `_ensure_gitignore_entry()` to update gitignore
  4. Return appropriate result (e.g., list of actions taken or success status)

### 6. Update Tests

- Remove tests for obsolete methods (`_is_file_outdated()`, `_get_target_commands_dir()`)
- Add tests for `_get_agf_config_source_dir()`
- Add tests for `_copy_agf_config()`:
  - Verifies directory structure is copied correctly
  - Handles case when target `.agf` already exists
- Add tests for `_create_command_symlinks()`:
  - Verifies symlinks are created correctly for both agents
  - Verifies symlinks point to correct targets
  - Handles case when symlinks already exist
- Update tests for `_ensure_gitignore_entry()`:
  - Verifies all three entries are added
  - Verifies no duplicates when entries already exist
- Update integration tests for `install_commands()`

### 7. Validate Implementation

- Run all tests to ensure functionality works correctly
- Run linters and type checkers
- Verify the installer works in a real worktree scenario

## Testing Strategy

**Unit Tests:**
- Test `_get_agf_config_source_dir()` returns correct path
- Test `_copy_agf_config()` copies directory structure correctly
- Test `_create_command_symlinks()` creates valid symlinks
- Test symlinks handle edge cases (existing symlinks, missing parent dirs)
- Test `_ensure_gitignore_entry()` adds all required entries
- Test `.gitignore` deduplication logic

**Integration Tests:**
- Test `install_commands()` performs complete installation
- Test repeated calls to `install_commands()` are idempotent
- Test installation works with different namespace values

**Edge Cases:**
- Existing `.agf/` directory
- Existing symlinks pointing to wrong targets
- Existing `.gitignore` with partial entries
- Missing `.gitignore` file
- Worktree with `directory_path = None`

## Acceptance Criteria

- The `.agf_config/` directory is copied to `{worktree_path}/.agf/`
- Symlink `{worktree_path}/.claude/commands/{namespace}` points to `{worktree_path}/.agf/claude/commands`
- Symlink `{worktree_path}/.opencode/command/{namespace}` points to `{worktree_path}/.agf/opencode/commands`
- `.gitignore` contains all three entries: `.agf/`, `.claude/commands/{namespace}/`, `.opencode/command/{namespace}/`
- All existing tests pass (after being updated for new behavior)
- New tests cover the new functionality
- `uv run ruff check` passes with no errors
- `uv run pytest` passes with no failures

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agf/installer.py` - Verify installer compiles
- `uv run ruff check agf/installer.py tests/agf/test_installer.py` - Run linter
- `uv run pytest tests/agf/test_installer.py -v` - Run installer tests
- `uv run pytest` - Run all tests to ensure no regressions

## Notes

- The `agf_commands/` directory may become obsolete after this refactor. Consider removing it in a separate cleanup task.
- Symlinks should be relative to improve portability when worktrees are moved.
- On Windows, symlink creation may require elevated privileges. The implementation should handle this gracefully with appropriate error messages.
- The `_get_target_commands_dir()` method may be removed or simplified since both agent paths are now created via symlinks.
