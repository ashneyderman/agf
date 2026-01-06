# Feature: Process Tasks Trigger

## Metadata

agf_id: `agf-012`
prompt: `prompts/agf-process-tasks-trigger.md`

## Feature Description

Create a task processing trigger mechanism that automatically discovers, selects, and processes tasks from a markdown task file. The trigger will use the `TaskManager` to collect tasks, run them in parallel batches respecting concurrency limits, and support both single-run and continuous scheduling modes. This script will orchestrate the execution of agentic workflows (agf) by processing ready-to-run tasks continuously or on-demand.

## User Story

As a developer using Agentic Flow
I want an automated trigger that discovers and processes tasks from my task file
So that I can run workflows continuously without manual intervention and control task execution through configuration

## Problem Statement

Currently, the Agentic Flow system has a `find_and_start_tasks.py` trigger that only discovers tasks and reports them, but doesn't actually process them. There is no automated mechanism to:

1. Load tasks from a markdown file using `TaskManager`
2. Select eligible tasks that are ready to run
3. Execute tasks in parallel while respecting concurrency limits
4. Run continuously with scheduled intervals between iterations
5. Handle graceful shutdown when interrupted
6. Integrate with the multi-level configuration system (AGFConfig/CLIConfig)
7. Support both dry-run mode for testing and single-run mode for one-off execution

This creates a gap where users must manually trigger task execution or build their own orchestration logic.

## Solution Statement

Implement a `process_tasks.py` trigger script in the `agf/triggers` package that:

1. **Configuration Integration**: Uses `EffectiveConfig` created from merging `AGFConfig` and `CLIConfig` to determine behavior
2. **Task Management**: Initializes `TaskManager` with `MarkdownTaskSource` to load tasks from a specified markdown file
3. **Execution Modes**:
   - **Single-run mode**: Executes one iteration and exits (useful for testing and CI/CD)
   - **Continuous mode**: Runs on a schedule with configurable intervals, staggering execution to avoid overlapping batches
4. **Parallel Processing**: Processes tasks in parallel batches limited by `EffectiveConfig.concurrent_tasks`
5. **Task Processor**: Creates a task processor function that simulates work (prints task info, sleeps 15-45 seconds) to demonstrate the execution flow
6. **CLI Interface**: Uses Click to provide a clean command-line interface matching the existing `find_and_start_tasks.py` pattern

The script will follow the parallelism pattern demonstrated in `main.py` using `asyncio.Semaphore` and `asyncio.TaskGroup` for bounded concurrency.

## Relevant Files

Use these files to implement the feature:

- `agf/task_manager/manager.py` - TaskManager class for task selection and state management (lines 6-334)
- `agf/task_manager/markdown_source.py` - MarkdownTaskSource for loading tasks from markdown files (lines 7-492)
- `agf/task_manager/models.py` - Task and Worktree data models (lines 1-57)
- `agf/config/models.py` - Configuration models (AGFConfig, CLIConfig, EffectiveConfig) (lines 1-229)
- `agf/config/loader.py` - Configuration loading and merging utilities
- `agf/triggers/find_and_start_tasks.py` - Reference implementation for CLI structure and configuration integration (lines 1-453)
- `main.py` - Example of bounded concurrency with asyncio.Semaphore (lines 61-82)

### New Files

- `agf/triggers/process_tasks.py` - Main trigger script for processing tasks

## Implementation Plan

### Phase 1: Foundation

Create the basic script structure with CLI argument parsing using Click, configuration loading using the existing multi-level config system, and setup for graceful shutdown with signal handlers.

### Phase 2: Core Implementation

Implement the task processor function that simulates work, the task selection logic using TaskManager, and the parallel execution engine using asyncio with bounded concurrency.

### Phase 3: Integration

Add scheduling support for continuous mode using the `schedule` package, implement the main execution loop with staggered execution, and ensure proper integration with dry-run mode for testing.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Script File Structure

- Create `agf/triggers/process_tasks.py` with shebang `#!/usr/bin/env python3`
- Add module docstring explaining the script's purpose
- Add standard imports: `asyncio`, `random`, `time`, `signal`, `sys`, `datetime`, `pathlib`
- Add Click import for CLI
- Add schedule import for scheduling
- Import configuration models: `AGFConfig`, `CLIConfig`, `EffectiveConfig`, `merge_configs`, `find_agf_config`, `load_agf_config_from_file`
- Import task manager: `TaskManager`, `MarkdownTaskSource`, `Task`, `Worktree`, `TaskStatus`

### 2. Implement Task Processor Function

- Create async function `process_task(worktree: Worktree, task: Task, dry_run: bool) -> None`
- Print task information in this order (one item per line):
  - `worktree.worktree_name`
  - `task.task_id`
  - First 20 characters of `task.description`
  - Sleep interval selected (between 15 and 45 seconds)
- Generate random sleep interval between 15 and 45 seconds using `random.uniform(15, 45)`
- If not dry-run mode, sleep for the selected interval using `await asyncio.sleep(interval)`
- If dry-run mode, skip the sleep but still print the interval
- Add docstring explaining the function simulates task processing

### 3. Implement Bounded Concurrency Helper

- Create async function `bounded_task(sem: asyncio.Semaphore, coro) -> Any`
- Use `async with sem:` to acquire semaphore
- Await the coroutine and return its result
- Add docstring explaining this limits concurrent execution
- This pattern matches the example in `main.py` (lines 61-63)

### 4. Implement Parallel Task Execution

- Create async function `process_tasks_parallel(task_manager: TaskManager, config: EffectiveConfig) -> None`
- Fetch next available tasks using `task_manager.fetch_next_available_tasks(count=config.concurrent_tasks)`
- If no tasks available, log "No tasks available for processing" and return
- Create `asyncio.Semaphore(config.concurrent_tasks)` to limit concurrency
- Use `async with asyncio.TaskGroup() as tg:` to manage task execution
- For each (worktree, task) tuple, create task with `tg.create_task(bounded_task(sem, process_task(worktree, task, config.dry_run)))`
- Add error handling to log any task failures
- Add docstring explaining parallel execution with bounded concurrency

### 5. Implement Single Iteration Logic

- Create function `run_iteration(task_manager: TaskManager, config: EffectiveConfig, iteration: int) -> int`
- Log "--- Iteration {iteration} ---" with timestamp
- Record start time using `time.time()`
- Call `process_tasks_parallel(task_manager, config)` using `asyncio.run()`
- Calculate and log duration: "Iteration {iteration} completed in {duration:.2f}s"
- Return count of tasks processed
- Add docstring explaining single iteration execution

### 6. Implement Logging Helper

- Create function `log(message: str, dry_run: bool = False) -> None`
- Format timestamp as "%Y-%m-%d %H:%M:%S"
- Add "[DRY-RUN] " prefix if dry_run is True
- Use `click.echo()` to output "[{timestamp}] {prefix}{message}"
- Add docstring explaining structured logging

### 7. Implement Graceful Shutdown Context

- Create class `TriggerContext` with fields:
  - `running: bool = True` - flag to control execution loop
  - `current_iteration: int = 0` - tracks iteration count
- Add method `stop() -> None` that sets `running = False`
- Add docstring explaining context for graceful shutdown

### 8. Implement Signal Handlers

- Create function `setup_signal_handlers(context: TriggerContext) -> None`
- Define nested function `handle_signal(signum: int, frame: Any) -> None`
- In handler, log "Received {signal_name}, shutting down gracefully..."
- Call `context.stop()` to trigger shutdown
- Register handler for `signal.SIGINT` and `signal.SIGTERM`
- Add docstring explaining signal handling for graceful shutdown

### 9. Implement CLI Validators

- Create function `validate_tasks_file(ctx, param, value) -> Path` as Click callback
- Check that file exists using `Path(value).exists()`
- Check that file has `.md` extension using `Path(value).suffix`
- Raise `click.BadParameter` with descriptive message if validation fails
- Return resolved absolute path using `Path(value).resolve()`
- Create function `validate_project_dir(ctx, param, value) -> Path` as Click callback
- Check that directory exists and is a directory
- Raise `click.BadParameter` if validation fails
- Return resolved absolute path

### 10. Implement Main CLI Command

- Create Click command decorated function `main()` with parameters:
  - `--tasks-file` (required, callback=validate_tasks_file) - Path to tasks markdown file
  - `--project-dir` (required, callback=validate_project_dir) - Root directory of project
  - `--agf-config` (optional, type=Path) - Path to AGF config file
  - `--sync-interval` (default=30, type=int) - Interval in seconds between runs
  - `--dry-run` (is_flag=True, default=False) - Read-only mode
  - `--single-run` (is_flag=True, default=False) - Run once and exit
- Add comprehensive docstring with examples matching the format in the prompt
- Follow the same CLI structure as `find_and_start_tasks.py` for consistency

### 11. Implement Configuration Loading in Main

- Load AGF config: if `--agf-config` provided, use it; else call `find_agf_config(project_dir)`
- If config path found, load with `load_agf_config_from_file()`; else use `AGFConfig.default()`
- Log the config file path or "No AGF config file found, using defaults"
- Handle exceptions during config loading and fall back to defaults with warning
- Create `CLIConfig` instance from CLI arguments
- Call `merge_configs(agf_config, cli_config)` to get `EffectiveConfig`
- Log configuration summary: tasks_file, project_dir, sync_interval, dry_run, single_run, concurrent_tasks

### 12. Implement TaskManager Initialization

- Create `MarkdownTaskSource(file_path=str(effective_config.tasks_file))` instance
- Create `TaskManager(task_source=markdown_source)` instance
- Add error handling for task source initialization failures
- Log "Initialized TaskManager with {count} worktrees" after initialization
- This follows the pattern described in the prompt

### 13. Implement Single-Run Mode

- Check if `effective_config.single_run` is True
- If True, set `context.current_iteration = 1`
- Call `run_iteration(task_manager, effective_config, context.current_iteration)`
- Log "Single run completed, exiting"
- Return from main function
- This matches the requirement: "IF single-run = True: run a single iteration"

### 14. Implement Continuous Mode Scheduling

- Create `TriggerContext()` instance
- Call `setup_signal_handlers(context)` to enable graceful shutdown
- Run first iteration immediately with `context.current_iteration = 1`
- Create while loop: `while context.running:`
- Inside loop, sleep for `sync_interval` seconds (check `context.running` during sleep for responsiveness)
- After sleep, if still running, increment `context.current_iteration` and call `run_iteration()`
- Log "Next iteration in {sync_interval}s" after each iteration
- This implements staggered execution as required

### 15. Implement Staggered Execution

- Ensure scheduling only triggers new iteration after previous one completes
- Use simple sleep loop instead of `schedule.every()` to avoid overlapping executions
- Break sleep into 1-second intervals to check `context.running` flag
- This satisfies: "Stagger execution i.e. only schedule new iteration if tasks queue is empty"
- Add comment explaining staggered execution strategy

### 16. Add Main Entry Point

- Add standard Python entry point:
  ```python
  if __name__ == "__main__":
      main()
  ```
- This allows script to be run directly or imported as module

### 17. Make Script Executable

- Add executable permission to `agf/triggers/process_tasks.py`
- Run `chmod +x agf/triggers/process_tasks.py`
- Verify shebang is present at top of file

### 18. Test Script Execution

- Create a test tasks markdown file `test_tasks.md` with sample worktrees and tasks
- Test basic execution: `uv run agf/triggers/process_tasks.py --tasks-file test_tasks.md --project-dir . --dry-run --single-run`
- Verify output shows task information in correct format
- Verify script respects dry-run mode (no actual sleeping)
- Verify script respects single-run mode (exits after one iteration)

### 19. Test Configuration Integration

- Create `.agf.yaml` in project root with custom concurrent_tasks setting
- Run script without explicit config: verify it auto-discovers the config file
- Run script with `--agf-config /path/to/config.yaml`: verify it uses specified config
- Verify effective configuration is logged correctly
- Test that concurrent_tasks from config is respected in parallel execution

### 20. Test Continuous Mode

- Run script without `--single-run` flag: `uv run agf/triggers/process_tasks.py --tasks-file test_tasks.md --project-dir . --dry-run --sync-interval 5`
- Verify script runs continuously with 5-second intervals
- Send SIGINT (Ctrl+C) and verify graceful shutdown
- Verify iteration counter increments correctly
- Verify staggered execution (new iteration starts only after previous completes)

### 21. Test Parallel Task Processing

- Create tasks file with multiple worktrees and tasks
- Set `concurrent-tasks: 3` in AGF config
- Run with `--single-run` and observe that max 3 tasks execute concurrently
- Verify sleep intervals are random between 15-45 seconds
- Verify task output format matches requirements (worktree_name, task_id, description first 20 chars, sleep interval)

### 22. Add Error Handling

- Add try-except around task processing to catch and log errors
- Add try-except around TaskManager initialization
- Add try-except around configuration loading
- Ensure errors don't crash the continuous mode loop
- Log errors with timestamps using the `log()` helper

### 23. Update Script Documentation

- Add detailed module docstring explaining:
  - Purpose of the script
  - Execution modes (single-run vs continuous)
  - Configuration integration
  - Examples of usage
- Add inline comments for complex logic
- Ensure all functions have clear docstrings

### 24. Clean Up Test Artifacts

- Remove test tasks file `test_tasks.md` if created for testing
- Remove any temporary config files
- Verify no test artifacts remain in repository

## Testing Strategy

### Unit Tests

Since this is a trigger script with heavy integration dependencies, unit testing will focus on:
- Validation functions (`validate_tasks_file`, `validate_project_dir`)
- Logging helper function
- Signal handler setup
- TriggerContext state management

### Integration Tests

The main testing will be manual integration testing:
- Test with real task markdown files
- Test with various AGF config files
- Test CLI argument validation
- Test both execution modes
- Test graceful shutdown
- Test parallel execution with different concurrency limits

### Edge Cases

- Empty task file (no worktrees)
- Task file with no eligible tasks
- Tasks file that doesn't exist (should fail validation)
- Project directory that doesn't exist (should fail validation)
- Invalid sync-interval (negative or zero)
- Config file that doesn't exist or is invalid
- Interrupted during task execution (signal handling)
- Very large number of concurrent tasks
- Tasks that complete immediately (zero sleep)
- Continuous mode with very short sync-interval (rapid iterations)

## Acceptance Criteria

- Script exists at `agf/triggers/process_tasks.py` and is executable
- Script uses Click for CLI interface matching the examples in the prompt
- Script accepts all required CLI arguments: `--tasks-file`, `--project-dir`
- Script accepts all optional CLI arguments: `--agf-config`, `--sync-interval`, `--dry-run`, `--single-run`
- Script validates that tasks file exists and has `.md` extension
- Script validates that project directory exists
- Script loads AGF config from file or uses defaults
- Script creates `EffectiveConfig` by merging AGFConfig and CLIConfig
- Script initializes `TaskManager` with `MarkdownTaskSource`
- Single-run mode executes one iteration and exits
- Continuous mode runs on schedule with configured sync-interval
- Parallel execution respects `concurrent_tasks` limit from config
- Task processor prints required information in correct order
- Task processor sleeps random interval between 15-45 seconds (or skips in dry-run)
- Script handles SIGINT and SIGTERM gracefully
- Execution is staggered (no overlapping batches)
- All output uses the `log()` helper with timestamps
- Dry-run mode works correctly (no actual sleeping, but shows what would happen)
- Script can be run with both usage examples from the prompt

## Validation Commands

Execute these commands to validate the feature is complete:

- `uv run python -m py_compile agf/triggers/process_tasks.py` - Test script compiles without syntax errors
- `uv run agf/triggers/process_tasks.py --help` - Verify CLI help text displays correctly
- `uv run agf/triggers/process_tasks.py --tasks-file ./tasks.md --project-dir . --dry-run --single-run` - Test single-run mode (replace with actual tasks file)
- `uv run agf/triggers/process_tasks.py --tasks-file /path/to/tasks.md --project-dir /path/to/project --sync-interval 15` - Test continuous mode (Ctrl+C to stop)
- `chmod +x agf/triggers/process_tasks.py && ./agf/triggers/process_tasks.py --help` - Verify script is executable
- Create test tasks file and run: `uv run agf/triggers/process_tasks.py --tasks-file test.md --project-dir . --dry-run --single-run` - Verify task output format
- Test with AGF config: create `.agf.yaml` with `concurrent-tasks: 2` and verify only 2 tasks run in parallel

## Notes

### Parallelism Pattern

The script uses the asyncio pattern demonstrated in `main.py` (lines 61-82):

```python
async def bounded_task(sem, coro):
    async with sem:
        return await coro

async def process_in_parallel():
    sem = asyncio.Semaphore(max_concurrent)
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(bounded_task(sem, process(item)))
```

This ensures that at most `concurrent_tasks` are running at any time, which matches the requirement to "process tasks in parallel in batches of no more than `EffectiveConfig.concurrent_tasks`".

### Staggered Execution

The requirement "Stagger execution i.e. only schedule new iteration if tasks queue is empty" is interpreted as:
- Don't start a new iteration while the previous one is still processing tasks
- Wait for `sync_interval` seconds AFTER the previous iteration completes
- This prevents overlapping task batches and ensures clean iteration boundaries

The implementation uses a simple sleep loop after each iteration completes, rather than `schedule.every()` which would schedule the next run while the current one is still executing.

### Task Output Format

The task processor must print exactly these items in order (one per line):
1. `worktree.worktree_name` - Name of the worktree
2. `task.task_id` - The 6-character task ID
3. First 20 characters of `task.description` - Truncated description
4. Sleep interval selected - The random value between 15 and 45 seconds

Example output:
```
feature-auth
ntjnwf
Implement login en
23.7
```

### Configuration Integration

The script fully integrates with the multi-level configuration system:
- Loads AGF config from file or discovers it automatically
- Merges with CLI config to create effective config
- Uses `effective_config.concurrent_tasks` for parallel execution limits
- Uses `effective_config.tasks_file` and `effective_config.project_dir` for task loading
- Respects `effective_config.dry_run` and `effective_config.single_run` flags

### Dependencies

All required dependencies are already in `pyproject.toml`:
- `click` - CLI interface
- `schedule` - Scheduling support (already present from previous work)
- `asyncio` - Built-in, no installation needed
- `pydantic` - Already present for models
- `pyyaml` - Already present for config loading

No new dependencies need to be added.

### Future Enhancements

After this feature is complete, consider:
- Actually executing agent workflows instead of simulating with sleep
- Updating task status in the task file as tasks complete
- Recording commit SHAs after successful task completion
- Metrics collection (tasks processed, success rate, average duration)
- Prometheus endpoint for monitoring
- Webhook notifications on task completion
- Integration with CI/CD pipelines
- Task retry logic for failed tasks
- Dead letter queue for permanently failed tasks
