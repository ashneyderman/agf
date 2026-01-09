# Chore: Create Installer Class

## Metadata

agf_id: `agf-026`
prompt: `in agf/ create an installer class. it must have EffectiveConfig and Worktree references in its state.`

## Chore Description

Create a new `Installer` class within the `agf/` module that manages installation operations. The class should maintain references to `EffectiveConfig` (from `agf/config/models.py`) and `Worktree` (from `agf/task_manager/models.py`) in its state. This class will serve as the foundation for installation capabilities in the Agentic Flow system.

## Relevant Files

Use these files to complete the chore:

- `agf/config/models.py` - Contains the `EffectiveConfig` class that will be referenced in the Installer state
- `agf/task_manager/models.py` - Contains the `Worktree` class that will be referenced in the Installer state
- `agf/task_manager/manager.py` - Reference for class structure patterns used in the codebase
- `tests/agf/task_manager/test_manager.py` - Reference for test patterns used in the codebase

### New Files

- `agf/installer.py` - New file containing the `Installer` class
- `tests/agf/test_installer.py` - New file containing tests for the `Installer` class

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create the Installer Class Module

- Create `agf/installer.py` with the `Installer` class
- Import `EffectiveConfig` from `agf.config.models`
- Import `Worktree` from `agf.task_manager.models`
- Define the `Installer` class with an `__init__` method that accepts `config: EffectiveConfig` and `worktree: Worktree` parameters
- Store both references as instance attributes (`self._config` and `self._worktree`)
- Add property methods to access the config and worktree (`config` and `worktree` properties)
- Add appropriate docstrings following the existing codebase style

### 2. Update the agf Package Init

- Review `agf/__init__.py` to determine if the `Installer` class should be exported
- If appropriate based on existing patterns, add the `Installer` import to `agf/__init__.py`

### 3. Create Unit Tests for the Installer Class

- Create `tests/agf/test_installer.py`
- Add test fixtures for `EffectiveConfig` and `Worktree` mock objects
- Test that `Installer` can be instantiated with config and worktree parameters
- Test that the `config` property returns the correct `EffectiveConfig` instance
- Test that the `worktree` property returns the correct `Worktree` instance
- Follow the existing test patterns from `tests/agf/task_manager/test_manager.py`

### 4. Validate the Implementation

- Run the type checker to ensure no type errors
- Run the test suite to ensure all tests pass
- Verify the new class can be imported from the `agf` module

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/installer.py` - Verify the installer module compiles
- `uv run python -c "from agf.installer import Installer; print('Import successful')"` - Verify the Installer class can be imported
- `uv run pytest tests/agf/test_installer.py -v` - Run the installer tests
- `uv run pytest` - Run all tests to ensure no regressions

## Notes

- The `Installer` class is intentionally minimal at this stage, serving as a foundation for future installation capabilities
- Follow the existing Pydantic-based modeling patterns seen in the codebase (though `Installer` itself may not need to be a Pydantic model if it's primarily a service class)
- Consider whether `Installer` should be a Pydantic `BaseModel` or a plain Python class based on its intended use; since it holds references to mutable state and will perform operations, a plain class is likely more appropriate
