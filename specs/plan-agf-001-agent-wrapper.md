# Plan: AI Agent Calling Wrapper

## Metadata

agf_id: `agent-wrapper`
prompt: `Create AI agent calling wrapper that can call variety of agents (Claude Code, OpenCode) in the same manner with JSON output by default`
task_type: feature
complexity: complex

## Task Description

Create a unified Python wrapper in the `./agent` package that provides a consistent interface for invoking different AI coding agents (Claude Code, OpenCode). The wrapper should:

1. Abstract away the differences between agent CLIs
2. Support JSON output format by default for programmatic consumption
3. Allow specification of additional options (model selection, timeout, etc.)
4. Return structured results from agent runs
5. Be extensible to support additional agents in the future

## Objective

When this plan is complete, there will be a functional `agent` package that:
1. Provides a unified interface (`AgentRunner`) for calling different AI agents
2. Supports Claude Code via `claude -p` with JSON output
3. Supports OpenCode via `opencode run` with JSON output
4. Returns structured results including output, errors, and metadata
5. Allows configuration of agent-specific options (model, timeout, tools, etc.)

## Problem Statement

The Agentic Flow project needs to orchestrate multiple AI coding agents. Each agent has a different CLI interface:
- Claude Code: `claude --dangerously-skip-permissions -p "<prompt>" --output-format json`
- OpenCode: `opencode run "<prompt>" --format json`

Calling these agents directly requires knowledge of their specific CLI options. A unified wrapper would allow higher-level workflows to invoke any supported agent through a consistent interface.

## Solution Approach

Create an abstraction layer using:
1. **Base `Agent` Protocol/ABC** - Defines the common interface all agents must implement
2. **Concrete Agent Implementations** - `ClaudeCodeAgent` and `OpenCodeAgent` classes
3. **`AgentRunner`** - Factory/facade that creates and runs agents by name
4. **`AgentResult`** - Structured dataclass for agent responses
5. **`AgentConfig`** - Configuration dataclass for agent options

The design follows the Strategy pattern, allowing easy addition of new agents without modifying existing code.

## Relevant Files

Use these files to complete the task:

- `pyproject.toml` - Add agent package and any new dependencies
- `README.md` - Update with agent package documentation

### New Files

- `agent/__init__.py` - Package exports
- `agent/base.py` - Base Agent protocol, AgentResult, AgentConfig dataclasses
- `agent/claude_code.py` - ClaudeCodeAgent implementation
- `agent/opencode.py` - OpenCodeAgent implementation
- `agent/runner.py` - AgentRunner facade for creating and running agents
- `agent/exceptions.py` - Custom exceptions for agent errors
- `tests/test_agent/__init__.py` - Test package init
- `tests/test_agent/test_base.py` - Tests for base classes
- `tests/test_agent/test_claude_code.py` - Tests for Claude Code agent
- `tests/test_agent/test_opencode.py` - Tests for OpenCode agent
- `tests/test_agent/test_runner.py` - Tests for AgentRunner

## Implementation Phases

### Phase 1: Foundation

- Create the `agent` package structure
- Define core abstractions: `Agent` protocol, `AgentResult`, `AgentConfig`
- Define custom exceptions for error handling

### Phase 2: Core Implementation

- Implement `ClaudeCodeAgent` with support for:
  - `-p` flag for non-interactive mode
  - `--output-format json` for JSON output
  - `--model` for model selection
  - `--dangerously-skip-permissions` (optional, configurable)
  - `--max-turns` for limiting agentic turns
  - `--tools` for tool control
  - `--append-system-prompt` for custom instructions
- Implement `OpenCodeAgent` with support for:
  - `run` command for non-interactive mode
  - `--format json` for JSON output
  - `--model` for model selection (format: `provider/model`)
  - `--file` for file attachments
  - `--agent` for agent selection

### Phase 3: Integration & Polish

- Implement `AgentRunner` facade
- Add comprehensive error handling
- Create unit tests with mocked subprocess calls
- Add type hints and documentation

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Package Structure

- Create `agent/` directory
- Create `agent/__init__.py` with version and public exports
- Create `tests/test_agent/` directory
- Create `tests/test_agent/__init__.py`
- Update `pyproject.toml` to include the agent package

### 2. Define Core Abstractions

Create `agent/base.py` with:
- `AgentResult` dataclass:
  - `success: bool` - Whether the agent run succeeded
  - `output: str` - Raw output from the agent
  - `parsed_output: dict | list | None` - Parsed JSON output (if JSON format)
  - `error: str | None` - Error message if failed
  - `exit_code: int` - Process exit code
  - `duration_seconds: float` - Execution duration
  - `agent_name: str` - Name of the agent used
- `AgentConfig` dataclass:
  - `model: str | None` - Model to use
  - `timeout_seconds: int` - Execution timeout (default: 300)
  - `working_dir: str | None` - Working directory
  - `output_format: str` - Output format (default: "json")
  - `extra_args: list[str]` - Additional CLI arguments
  - Agent-specific options as optional fields
- `Agent` Protocol:
  - `name: str` property - Agent identifier
  - `run(prompt: str, config: AgentConfig | None) -> AgentResult` method

### 3. Define Custom Exceptions

Create `agent/exceptions.py` with:
- `AgentError` - Base exception for all agent errors
- `AgentNotFoundError` - Agent CLI not installed
- `AgentTimeoutError` - Execution timeout exceeded
- `AgentExecutionError` - Non-zero exit code from agent
- `AgentOutputParseError` - Failed to parse agent output

### 4. Implement ClaudeCodeAgent

Create `agent/claude_code.py` with:
- `ClaudeCodeAgent` class implementing `Agent` protocol
- `name` property returning `"claude-code"`
- `run()` method that:
  - Builds command: `claude -p "<prompt>" --output-format json [options]`
  - Supports options:
    - `--model` from config
    - `--dangerously-skip-permissions` if config flag is set
    - `--max-turns` if specified
    - `--tools` if specified
    - `--append-system-prompt` if specified
  - Executes subprocess with timeout
  - Parses JSON output
  - Returns `AgentResult`
- Helper method `_build_command()` for command construction
- Error handling for missing CLI, timeouts, execution errors

### 5. Implement OpenCodeAgent

Create `agent/opencode.py` with:
- `OpenCodeAgent` class implementing `Agent` protocol
- `name` property returning `"opencode"`
- `run()` method that:
  - Builds command: `opencode run "<prompt>" --format json [options]`
  - Supports options:
    - `--model` / `-m` for model in `provider/model` format
    - `--agent` for agent selection
    - `--file` / `-f` for file attachments
  - Executes subprocess with timeout
  - Parses JSON output
  - Returns `AgentResult`
- Helper method `_build_command()` for command construction
- Error handling similar to ClaudeCodeAgent

### 6. Implement AgentRunner

Create `agent/runner.py` with:
- `AgentRunner` class:
  - Class-level registry of available agents
  - `register_agent(agent: Agent)` class method
  - `get_agent(name: str) -> Agent` class method
  - `list_agents() -> list[str]` class method
  - `run(agent_name: str, prompt: str, config: AgentConfig | None) -> AgentResult` method
- Pre-register Claude Code and OpenCode agents
- Factory pattern for agent instantiation

### 7. Update Package Exports

Update `agent/__init__.py` to export:
- `Agent`, `AgentResult`, `AgentConfig` from base
- `ClaudeCodeAgent` from claude_code
- `OpenCodeAgent` from opencode
- `AgentRunner` from runner
- All exceptions from exceptions
- `__version__`

### 8. Create Unit Tests

Create test files with mocked subprocess:
- `tests/test_agent/test_base.py`:
  - Test `AgentResult` dataclass creation
  - Test `AgentConfig` defaults and custom values
- `tests/test_agent/test_claude_code.py`:
  - Test command building with various options
  - Test successful run with mocked subprocess
  - Test error handling (missing CLI, timeout, non-zero exit)
  - Test JSON parsing
- `tests/test_agent/test_opencode.py`:
  - Test command building with various options
  - Test successful run with mocked subprocess
  - Test error handling
  - Test JSON parsing
- `tests/test_agent/test_runner.py`:
  - Test agent registration
  - Test agent lookup
  - Test run delegation

### 9. Add Dependencies

- Update `pyproject.toml`:
  - Add `pytest` as dev dependency if not present
  - Add `pytest-mock` for mocking subprocess

### 10. Validate Implementation

- Run syntax check on all Python files
- Run type checking if mypy is available
- Execute all unit tests
- Test with actual agents if installed

## Testing Strategy

1. **Unit Tests (Mocked)**: All tests mock `subprocess.run()` to test logic without actual CLI invocation
2. **Command Building Tests**: Verify correct CLI commands are constructed for various configurations
3. **Error Handling Tests**: Test all exception paths (missing CLI, timeout, parse error)
4. **Integration Tests**: If agents are installed, optional integration tests with simple prompts
5. **Edge Cases**:
   - Empty prompts
   - Very long prompts
   - Special characters in prompts
   - Invalid JSON output
   - Partial JSON output

## Acceptance Criteria

- [ ] `agent` package is properly structured and importable
- [ ] `ClaudeCodeAgent` correctly invokes `claude -p` with JSON output
- [ ] `OpenCodeAgent` correctly invokes `opencode run` with JSON output
- [ ] Both agents support model selection via config
- [ ] `AgentRunner` can run either agent by name
- [ ] JSON output is parsed and available in `AgentResult.parsed_output`
- [ ] Errors are properly caught and wrapped in custom exceptions
- [ ] Timeout handling works correctly
- [ ] All unit tests pass
- [ ] `from agent import AgentRunner, AgentConfig, AgentResult` works

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile agent/*.py` - Verify Python files compile
- `uv run python -c "from agent import AgentRunner, AgentConfig, AgentResult; print('Import OK')"` - Verify imports work
- `uv run python -c "from agent import ClaudeCodeAgent, OpenCodeAgent; print(ClaudeCodeAgent().name, OpenCodeAgent().name)"` - Verify agent names
- `uv run python -c "from agent import AgentRunner; print(AgentRunner.list_agents())"` - Verify agent registration
- `uv add --dev pytest pytest-mock` - Add test dependencies
- `uv run pytest tests/test_agent/ -v` - Run all agent tests

## Notes

- **Claude Code CLI Options** (relevant for -p mode):
  - `--output-format json|text|stream-json` - Output format
  - `--model sonnet|opus|<full-name>` - Model selection
  - `--dangerously-skip-permissions` - Skip all permission prompts
  - `--max-turns N` - Limit agentic turns
  - `--tools "Tool1,Tool2"` - Specify allowed tools
  - `--append-system-prompt "text"` - Add to system prompt
  - `--json-schema '{...}'` - Validate output against schema

- **OpenCode CLI Options** (relevant for run command):
  - `--format default|json` - Output format
  - `--model/-m provider/model` - Model in provider/model format
  - `--agent` - Select which agent to use
  - `--file/-f` - Attach files

- Both agents write output to stdout which can be captured via subprocess
- JSON output enables programmatic parsing of results
- Consider adding streaming support in future enhancement
- The `--dangerously-skip-permissions` flag for Claude Code should be opt-in via config for safety
