# Plan: Task Triggering Mechanism

## Metadata

agf_id: `agf-cron-trigger`
prompt: `@prompts/af-cron-trigger.md`
task_type: feature
complexity: medium

## Task Description

Create a task triggering mechanism that spins up workflows by periodically scanning a tasks file and identifying tasks ready to run. The script will be placed in a `triggers` package and will use the existing agent infrastructure to call the `/agf:process_tasks` prompt. It will support both single-run and continuous scheduling modes.

## Objective

Deliver a fully functional `find_and_start_tasks.py` script that:

1. Accepts CLI arguments for tasks-file, project-dir, sync-interval, dry-run, and single-run
2. Calls the `/agf:process_tasks` prompt to identify eligible tasks
3. Parses and prints the list of ready-to-run tasks
4. Supports continuous scheduling with configurable intervals

## Problem Statement

The agentic flow system needs an automated way to discover and initiate tasks from a task list file. Currently, there's no mechanism to periodically scan task files and trigger workflows for eligible tasks.

## Solution Approach

Create a Python script using:

- `click` package (already available) for CLI argument parsing
- `schedule` package (needs to be added) for cron-like scheduling
- Existing `AgentRunner` infrastructure to execute the `/agf:process_tasks` prompt
- Signal handling for graceful termination in continuous mode

## Relevant Files

- `agent/runner.py` - Contains `AgentRunner` class for executing agents
- `agent/claude_code.py` - `ClaudeCodeAgent` implementation for calling claude CLI
- `agent/base.py` - `AgentConfig` and `AgentResult` classes
- `.claude/commands/agf/process_tasks.md` - The prompt that analyzes tasks and returns eligible ones
- `pyproject.toml` - Project dependencies (needs `schedule` added)

### New Files

- `triggers/__init__.py` - Package init file
- `triggers/find_and_start_tasks.py` - Main trigger script

## Implementation Phases

### Phase 1: Foundation

Set up the triggers package structure and add the `schedule` dependency to pyproject.toml.

### Phase 2: Core Implementation

Implement the CLI using click with all required arguments and validation. Build the trigger loop logic that calls `/agf:process_tasks` and parses results.

### Phase 3: Integration & Polish

Implement continuous scheduling mode with proper signal handling for graceful shutdown. Add logging and status output.

## Step by Step Tasks

### 1. Add schedule dependency

- Edit `pyproject.toml` to add `schedule>=1.2.0` to dependencies
- Run `uv sync` to install the new dependency

### 2. Create triggers package

- Create `triggers/__init__.py` with package docstring
- Create basic structure for `triggers/find_and_start_tasks.py`

### 3. Implement CLI with click

- Add click command decorator with all required options:
  - `--tasks-file` (required, must exist, .md extension)
  - `--project-dir` (required, must be existing directory)
  - `--sync-interval` (default: 30 seconds)
  - `--dry-run` (default: False)
  - `--single-run` (default: False)
- Add validation for file and directory paths

### 4. Implement process_tasks invocation

- Create function to build the prompt for `/agf:process_tasks`
- Use `AgentRunner` with `ClaudeCodeAgent` to execute the prompt
- Configure `AgentConfig` with appropriate settings (working_dir, output_format)

### 5. Implement result parsing and output

- Parse the JSON output from the agent
- Extract worktree names and task descriptions
- Print formatted output of ready-to-run tasks

### 6. Implement single-run mode

- Execute one iteration of task discovery
- Print results and exit

### 7. Implement continuous scheduling mode

- Use `schedule` package to run task discovery at sync-interval
- Ensure scheduler waits for previous iteration to complete before scheduling next
- Add signal handling (SIGINT, SIGTERM) for graceful shutdown

### 8. Validate the implementation

- Run syntax check on the script
- Test with `--help` to verify CLI
- Test with a sample tasks file in dry-run mode

## Testing Strategy

1. **Unit Tests**: Create `tests/triggers/test_find_and_start_tasks.py` with:
   - CLI argument validation tests
   - Result parsing tests with mock agent responses
   - Scheduler behavior tests

2. **Integration Tests**:
   - Test single-run mode with actual prompt execution
   - Verify dry-run mode doesn't cause side effects

3. **Edge Cases**:
   - Empty tasks file
   - No eligible tasks
   - Invalid JSON response from agent
   - Graceful shutdown during execution

## Acceptance Criteria

- [ ] Script is executable via `uv run triggers/find_and_start_tasks.py`
- [ ] All CLI arguments work as specified (--tasks-file, --project-dir, --sync-interval, --dry-run, --single-run)
- [ ] Script correctly calls `/agf:process_tasks` prompt with the tasks file
- [ ] Script parses and prints eligible tasks from the response
- [ ] Single-run mode executes once and exits
- [ ] Continuous mode runs at specified intervals after each iteration completes
- [ ] Script handles SIGINT/SIGTERM gracefully in continuous mode
- [ ] Dry-run mode logs actions without executing them

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile triggers/find_and_start_tasks.py` - Verify syntax
- `uv run triggers/find_and_start_tasks.py --help` - Verify CLI interface
- `uv run triggers/find_and_start_tasks.py --tasks-file ./tasks.md --project-dir . --dry-run --single-run` - Test single-run dry-run mode (requires a tasks.md file)

## Notes

- The `schedule` package needs to be added via `uv add schedule`
- The script calls the prompt as `/agf:process_tasks <tasks-file>` where the prompt is expected to be available through the claude CLI's skill system
- The sync-interval stagger ensures iterations do NOT overlap - the next iteration starts only after the previous one completes plus the interval
- Consider adding logging with timestamps for operational visibility in continuous mode
