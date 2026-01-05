# Plan: Worktree APIs for Orchestration Scripts

## Metadata

agf_id: `agf-010`
prompt: `prompts/af-worktree-apis.md`
task_type: feature
complexity: medium

## Task Description

Create worktree management APIs that orchestration scripts can use to programmatically create and remove git worktrees. The APIs will be implemented in a new `git_repo.py` module and will provide two primary functions:

1. `mk_worktree(project_dir, target_dir, branch_name)` - Creates a new git worktree at the target directory with the specified branch
2. `rm_worktree(project_dir, target_dir, remove_branch=False)` - Removes an existing git worktree and optionally its associated branch

These APIs will use the GitPython library to interact with git, following the patterns established in `main.py` where GitPython is already used for worktree operations.

## Objective

Create a reusable Python module (`git_repo.py`) that provides clean, well-tested APIs for git worktree management operations. These APIs will be used by orchestration scripts to dynamically create and manage worktrees for parallel task execution.

## Problem Statement

The project currently uses worktrees for task management (as evidenced by the `Worktree` model in `task_manager/models.py` and the `.worktrees` directory), but lacks a centralized, reusable API for creating and removing worktrees programmatically. The example code in `main.py` demonstrates the low-level GitPython calls needed, but this logic needs to be extracted into a proper module with:

- Proper error handling and validation
- Clear API contracts
- Comprehensive test coverage
- Documentation of expected behavior

## Solution Approach

Create a new `git_repo.py` module that encapsulates all git worktree operations. The module will:

1. Use GitPython's `Repo` class to interact with the git repository
2. Provide high-level functions that handle the complete worktree lifecycle
3. Include proper error handling for edge cases (directory doesn't exist, worktree already exists, etc.)
4. Follow the existing codebase patterns for error handling and validation
5. Use the `--no-checkout` flag followed by explicit checkout to ensure the worktree is properly initialized

The implementation will be based on the working examples already present in `main.py` (lines 38-57) and the guidance provided in the prompt.

## Relevant Files

Use these files to complete the task:

- `task_manager/models.py` - Contains the `Worktree` model that represents worktrees in the system; provides context for how worktrees are used
- `main.py` - Contains working example code for git worktree operations using GitPython (lines 38-57); serves as a reference implementation
- `pyproject.toml` - Project dependencies file where GitPython needs to be added
- `.worktrees/` directory - Target location for worktrees (referenced in main.py examples)

### New Files

- `git_repo.py` - New module containing the worktree management APIs (will be created at project root level, alongside `main.py`)
- `tests/test_git_repo.py` - Comprehensive test suite for the git_repo module

## Implementation Phases

### Phase 1: Foundation

Set up the module structure and add GitPython as a project dependency. Review existing GitPython usage patterns in the codebase to ensure consistency.

### Phase 2: Core Implementation

Implement the two core API functions (`mk_worktree` and `rm_worktree`) with proper error handling, validation, and documentation. Follow the working examples from `main.py` and the guidance in the prompt.

### Phase 3: Integration & Polish

Create comprehensive tests covering normal operations and edge cases. Ensure the APIs integrate well with the existing task management system and follow project conventions.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add GitPython Dependency

- Add GitPython to project dependencies in `pyproject.toml` using `uv add gitpython`
- Verify the dependency is properly installed by running `uv sync`

### 2. Create git_repo.py Module Structure

- Create new file `git_repo.py` at the project root
- Add module docstring explaining the purpose and usage
- Import required dependencies: `os`, `os.path`, `Repo` from `git`
- Follow the code style conventions observed in existing modules like `task_manager/manager.py`

### 3. Implement mk_worktree Function

- Define function signature: `def mk_worktree(project_dir: str, target_dir: str, branch_name: str) -> None:`
- Add comprehensive docstring with parameters, return value, and raises documentation
- Implement validation:
  - Check if `project_dir` exists, raise `ValueError` if not
  - Check if `target_dir` parent directory exists, create it if it doesn't exist
  - Check if `target_dir` already exists, raise `ValueError` if it does (to prevent accidental overwrites)
- Implement worktree creation logic:
  - Initialize `Repo` object from `project_dir`
  - Use `repo.git.execute(["git", "worktree", "add", "--no-checkout", target_dir, branch_name])` to create worktree
  - The `--no-checkout` flag creates the worktree without checking out files
  - The branch_name parameter will create a new branch if it doesn't exist (implicit `-b` behavior)
- Implement checkout logic:
  - Initialize a new `Repo` object from `target_dir`
  - Call `repo1.git.checkout()` to checkout the branch content
- Add error handling for git command failures

### 4. Implement rm_worktree Function

- Define function signature: `def rm_worktree(project_dir: str, target_dir: str, remove_branch: bool = False) -> None:`
- Add comprehensive docstring with parameters, return value, and raises documentation
- Implement validation:
  - Check if `target_dir` exists, raise `ValueError` if not (can't remove what doesn't exist)
- Implement worktree removal logic:
  - Initialize `Repo` object from `project_dir`
  - Use `repo.git.execute(["git", "worktree", "remove", "--force", target_dir])` to remove worktree
  - The `--force` flag ensures removal even if there are uncommitted changes
- Implement branch removal logic (if `remove_branch=True`):
  - Extract branch name from the worktree before removing it (may need to parse `git worktree list --porcelain`)
  - After worktree removal, use `repo.git.execute(["git", "branch", "-D", branch_name])` to delete the branch
  - Use `-D` flag to force deletion regardless of merge status
- Add error handling for git command failures

### 5. Add Helper Function for Branch Name Extraction (if needed)

- If branch removal requires extracting the branch name from a worktree, create a helper function
- Use `git worktree list --porcelain` to get structured worktree information
- Parse the output to find the branch associated with the target directory

### 6. Create Comprehensive Tests

- Create `tests/test_git_repo.py` test file
- Add tests for `mk_worktree`:
  - Test successful worktree creation with new branch
  - Test successful worktree creation with existing branch (if applicable)
  - Test error when project_dir doesn't exist
  - Test error when target_dir already exists
  - Test that files are checked out after creation
- Add tests for `rm_worktree`:
  - Test successful worktree removal without branch removal
  - Test successful worktree removal with branch removal (`remove_branch=True`)
  - Test error when target_dir doesn't exist
  - Test that branch is preserved when `remove_branch=False`
  - Test that branch is removed when `remove_branch=True`
- Use pytest fixtures to set up temporary test repositories
- Use `pytest-mock` if needed for mocking git operations
- Ensure all tests clean up after themselves

### 7. Add Module Documentation

- Add usage examples in the module docstring showing typical usage patterns
- Document expected error conditions and exceptions
- Reference the GitPython documentation URLs provided in the prompt

### 8. Validate Implementation

- Run all tests to ensure they pass
- Verify Python syntax with py_compile
- Test manual integration with a real repository
- Ensure the APIs work correctly with the `.worktrees` directory structure used in the project

## Testing Strategy

### Unit Tests

- Test each function in isolation using temporary test repositories
- Mock git operations where appropriate to test error handling
- Use pytest fixtures to create and tear down test repositories
- Cover both success and error paths for each function

### Integration Tests

- Create end-to-end tests that exercise the full workflow:
  1. Create a worktree with `mk_worktree`
  2. Verify the worktree exists and has files checked out
  3. Remove the worktree with `rm_worktree`
  4. Verify the worktree is removed
  5. Test branch preservation and removal options

### Edge Cases

- Project directory that isn't a git repository
- Target directory with permission issues
- Worktree creation when branch already has an active worktree
- Concurrent worktree operations
- Invalid branch names with special characters

## Acceptance Criteria

- [ ] GitPython dependency is added to `pyproject.toml`
- [ ] `git_repo.py` module exists at project root with proper documentation
- [ ] `mk_worktree()` function creates worktrees with proper validation and error handling
- [ ] `rm_worktree()` function removes worktrees with optional branch removal
- [ ] All functions have comprehensive docstrings with type hints
- [ ] Test suite in `tests/test_git_repo.py` covers all functions and edge cases
- [ ] All tests pass with 100% success rate
- [ ] Code follows existing project conventions and style
- [ ] Module can be imported and used by orchestration scripts
- [ ] Branch removal works correctly when `remove_branch=True`
- [ ] Branch is preserved when `remove_branch=False`

## Validation Commands

Execute these commands to validate the task is complete:

- `uv sync` - Ensure GitPython dependency is installed
- `uv run python -m py_compile git_repo.py` - Verify syntax of the git_repo module
- `uv run pytest tests/test_git_repo.py -v` - Run all git_repo tests
- `uv run python -c "from git_repo import mk_worktree, rm_worktree; print('Import successful')"` - Verify module can be imported
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

### GitPython Documentation References

From the prompt, the following documentation sources are available:
- Intro/Tutorial: https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
- API Reference: https://gitpython.readthedocs.io/en/stable/reference.html#api-reference-toplevel

### Key Implementation Details

1. **Worktree Creation Process**: Use `--no-checkout` followed by explicit checkout to ensure proper initialization
   ```python
   repo.git.execute(["git", "worktree", "add", "--no-checkout", worktree_target_dir, branch_name])
   repo1 = Repo.init(worktree_target_dir)
   repo1.git.checkout()
   ```

2. **Branch Creation**: When `branch_name` doesn't exist, git worktree will automatically create it. No need for explicit `-b` flag based on the prompt examples.

3. **Force Removal**: Always use `--force` flag when removing worktrees to handle cases with uncommitted changes

4. **Directory Management**: Create parent directories for target_dir if they don't exist (convenience feature)

### Existing Pattern Reference

The `main.py` file already contains working example code (lines 38-57) that demonstrates:
- Initializing a Repo from project directory
- Creating worktrees with `--no-checkout`
- Checking out files in the new worktree
- Removing worktrees with `--force`

These examples should be used as the basis for the implementation.

### Integration with Task Management

While not required for this task, the `git_repo.py` module will be used by orchestration scripts that work with the `TaskManager` and `Worktree` model. The APIs should be designed to integrate naturally with this workflow:
1. TaskManager identifies a task to execute in a worktree
2. Orchestration script calls `mk_worktree()` to create the worktree
3. Agent executes the task in the worktree
4. Orchestration script calls `rm_worktree()` to clean up

### Testing Considerations

- Use temporary directories for test repositories to avoid polluting the project
- Ensure all tests clean up worktrees and branches they create
- Consider using `pytest` fixtures for common test setup (creating test repos, etc.)
- Test both the happy path and error conditions thoroughly
