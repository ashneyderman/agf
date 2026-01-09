# Chore: Log CLI Command Execution

## Metadata

agf_id: `agf-024`
prompt: `log the exact CLI command executed. The actual CLI command is assembled in the concrete Agent. Make AgentConfig carry logger function, that will be used to log the command. If logger is None at the time logging is attempted, skip logging.`

## Chore Description

Add CLI command logging capability to the agent framework. The logging mechanism should:
1. Add an optional logger function to `AgentConfig` that accepts a string (the CLI command)
2. When agents execute commands, they should log the fully assembled CLI command using this logger
3. If no logger is configured (logger is None), skip logging silently
4. The logger should be called just before executing the subprocess command

This allows callers to observe the exact commands being executed for debugging, auditing, or transparency purposes.

## Relevant Files

Use these files to complete the chore:

- **`agf/agent/base.py`** - Contains `AgentConfig` class where the logger function field needs to be added
- **`agf/agent/claude_code.py`** - Contains `ClaudeCodeAgent` where the CLI command is built and executed; needs to call the logger
- **`agf/agent/opencode.py`** - Contains `OpenCodeAgent` where the CLI command is built and executed; needs to call the logger
- **`tests/agf/agent/test_claude_code.py`** - Tests for Claude Code agent; needs tests for logger functionality
- **`tests/agf/agent/test_opencode.py`** - Tests for OpenCode agent; needs tests for logger functionality

### New Files

No new files needed.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Logger Field to AgentConfig

- Open `agf/agent/base.py`
- Add a `Callable[[str], None] | None` type import from `typing` module
- Add a new field `logger: Callable[[str], None] | None = None` to `AgentConfig` class
- Add a docstring comment explaining the field's purpose

### 2. Update ClaudeCodeAgent to Use Logger

- Open `agf/agent/claude_code.py`
- In the `run()` method, after building the command with `_build_command()` and before calling `subprocess.run()`:
  - Check if `config.logger` is not None
  - If logger exists, call it with the command string (join the command list with spaces for readability)
- Consider using `shlex.join()` for proper shell quoting of the command

### 3. Update OpenCodeAgent to Use Logger

- Open `agf/agent/opencode.py`
- In the `run()` method, after building the command with `_build_command()` and before calling `subprocess.run()`:
  - Check if `config.logger` is not None
  - If logger exists, call it with the command string (join the command list with spaces for readability)
- Consider using `shlex.join()` for proper shell quoting of the command

### 4. Add Tests for Logger in ClaudeCodeAgent

- Open `tests/agf/agent/test_claude_code.py`
- Add test `test_run_with_logger()`:
  - Create a mock logger function
  - Create `AgentConfig` with the logger
  - Run the agent (mock subprocess)
  - Verify the logger was called exactly once with the expected command string
- Add test `test_run_without_logger()`:
  - Verify that running without a logger (None) works correctly without errors
  - This essentially confirms existing tests still pass

### 5. Add Tests for Logger in OpenCodeAgent

- Open `tests/agf/agent/test_opencode.py`
- Add test `test_run_with_logger()`:
  - Create a mock logger function
  - Create `AgentConfig` with the logger
  - Run the agent (mock subprocess)
  - Verify the logger was called exactly once with the expected command string
- Add test `test_run_without_logger()`:
  - Verify that running without a logger (None) works correctly without errors

### 6. Validate the Implementation

- Run all tests to ensure nothing is broken
- Verify that the new logger functionality works as expected
- Check that existing tests still pass

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/agent/base.py agf/agent/claude_code.py agf/agent/opencode.py` - Verify code compiles without syntax errors
- `uv run pytest tests/agf/agent/test_claude_code.py -v` - Run Claude Code agent tests
- `uv run pytest tests/agf/agent/test_opencode.py -v` - Run OpenCode agent tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes

- The logger is intentionally optional (defaults to None) to maintain backward compatibility
- Using `shlex.join()` is preferred over simple `" ".join()` because it properly quotes arguments containing spaces or special characters
- The logger is called synchronously before command execution, so it won't interfere with the subprocess timing
- This pattern allows for flexible logging strategies: callers can log to stdout, a file, a logging framework, or any custom destination
