#!/usr/bin/env python3
"""Task processing trigger that discovers and processes tasks from a markdown file.

This script provides an automated trigger mechanism that:
- Loads tasks from a markdown file using TaskManager
- Selects eligible tasks that are ready to run
- Executes tasks in parallel while respecting concurrency limits
- Supports both single-run and continuous scheduling modes
- Integrates with the multi-level configuration system (AGFConfig/CLIConfig)

Execution Modes:
- Single-run: Executes one iteration and exits (useful for testing and CI/CD)
- Continuous: Runs on a schedule with configurable intervals between iterations

Configuration Integration:
The script uses EffectiveConfig created from merging AGFConfig and CLIConfig to
determine behavior. Configuration precedence: CLI > AGF Config > Defaults

Examples:
    Single-run with dry-run mode:
        uv run agf/triggers/process_tasks.py --tasks-file ./tasks.md --project-dir . --dry-run --single-run

    Continuous mode with custom interval:
        uv run agf/triggers/process_tasks.py --tasks-file /home/my_tasks.md --project-dir /home/alex/projects/my_project --sync-interval 15
"""

import asyncio
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from agf.config import (
    AGFConfig,
    CLIConfig,
    EffectiveConfig,
    find_agf_config,
    load_agf_config_from_file,
    merge_configs,
)
from agf.task_manager import TaskManager
from agf.task_manager.markdown_source import MarkdownTaskSource
from agf.task_manager.models import Task, TaskStatus, Worktree


def log(message: str, dry_run: bool = False) -> None:
    """Log a message with timestamp.

    Args:
        message: The message to log
        dry_run: If True, adds [DRY-RUN] prefix to the message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "[DRY-RUN] " if dry_run else ""
    click.echo(f"[{timestamp}] {prefix}{message}")


class TriggerContext:
    """Context for managing trigger state and graceful shutdown.

    Attributes:
        running: Flag to control execution loop
        current_iteration: Tracks iteration count
    """

    def __init__(self) -> None:
        self.running = True
        self.current_iteration = 0

    def stop(self) -> None:
        """Signal the trigger to stop."""
        self.running = False


def setup_signal_handlers(context: TriggerContext) -> None:
    """Setup signal handlers for graceful shutdown.

    Registers handlers for SIGINT and SIGTERM that will gracefully stop
    the trigger by setting the context.running flag to False.

    Args:
        context: The trigger context to control
    """

    def handle_signal(signum: int, frame: Any) -> None:
        signal_name = signal.Signals(signum).name
        log(f"Received {signal_name}, shutting down gracefully...")
        context.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


async def process_task(worktree: Worktree, task: Task, dry_run: bool) -> None:
    """Process a single task by simulating work.

    Prints task information and sleeps for a random interval to simulate
    task processing. In dry-run mode, skips the sleep but still prints
    the interval that would have been used.

    Args:
        worktree: The worktree containing the task
        task: The task to process
        dry_run: If True, skip the actual sleep

    Output format (one per line, "<field-name>: <field-value>"):
        - worktree: worktree.worktree_name
        - task_id: task.task_id
        - description: First 5 words of task.description (with ellipsis if truncated)
        - sleep_interval: Sleep interval in seconds (rounded to nearest integer)
    """
    # Generate random sleep interval between 15 and 45 seconds
    sleep_interval = random.uniform(15, 45)

    # Truncate description to first 5 words with ellipsis if needed
    words = task.description.split()
    if len(words) > 5:
        truncated_desc = " ".join(words[:5]) + "..."
    else:
        truncated_desc = task.description

    # Print task information
    print(f"worktree: {worktree.worktree_name}")
    print(f"task_id: {task.task_id}")
    print(f"description: {truncated_desc}")
    print(f"sleep_interval: {round(sleep_interval)}")

    # Sleep to simulate work (skip in dry-run mode)
    if not dry_run:
        await asyncio.sleep(sleep_interval)


async def bounded_task(sem: asyncio.Semaphore, coro) -> Any:
    """Execute a coroutine with semaphore-based concurrency control.

    This helper ensures that at most N coroutines run concurrently,
    where N is the semaphore's value.

    Args:
        sem: Semaphore to control concurrency
        coro: Coroutine to execute

    Returns:
        The result of the coroutine
    """
    async with sem:
        return await coro


async def process_tasks_parallel(
    task_manager: TaskManager, config: EffectiveConfig
) -> int:
    """Process tasks in parallel with bounded concurrency.

    Fetches next available tasks and processes them in parallel,
    respecting the concurrent_tasks limit from configuration.

    Args:
        task_manager: TaskManager instance for task selection
        config: Effective configuration with execution parameters

    Returns:
        Number of tasks processed
    """
    # Fetch next available tasks
    available_tasks = task_manager.fetch_next_available_tasks(
        count=config.concurrent_tasks
    )

    if not available_tasks:
        log("No tasks available for processing", dry_run=config.dry_run)
        return 0

    log(
        f"Processing {len(available_tasks)} tasks in parallel (max concurrent: {config.concurrent_tasks})",
        dry_run=config.dry_run,
    )

    # Create semaphore to limit concurrency
    sem = asyncio.Semaphore(config.concurrent_tasks)

    # Process tasks in parallel using TaskGroup
    try:
        async with asyncio.TaskGroup() as tg:
            for worktree, task in available_tasks:
                tg.create_task(
                    bounded_task(sem, process_task(worktree, task, config.dry_run))
                )
    except Exception as e:
        log(f"Error during task processing: {e}", dry_run=config.dry_run)
        raise

    return len(available_tasks)


def run_iteration(
    task_manager: TaskManager, config: EffectiveConfig, iteration: int
) -> int:
    """Run a single iteration of task processing.

    Logs iteration start, processes tasks in parallel, and logs completion
    with duration.

    Args:
        task_manager: TaskManager instance for task selection
        config: Effective configuration with execution parameters
        iteration: Current iteration number

    Returns:
        Number of tasks processed
    """
    log(f"--- Iteration {iteration} ---", dry_run=config.dry_run)
    start_time = time.time()

    # Process tasks
    tasks_processed = asyncio.run(process_tasks_parallel(task_manager, config))

    duration = time.time() - start_time
    log(
        f"Iteration {iteration} completed in {duration:.2f}s (processed {tasks_processed} tasks)",
        dry_run=config.dry_run,
    )

    return tasks_processed


def validate_tasks_file(ctx: click.Context, param: click.Parameter, value: str) -> Path:
    """Validate that tasks file exists and has .md extension.

    Args:
        ctx: Click context
        param: Click parameter
        value: File path value

    Returns:
        Resolved absolute path to tasks file

    Raises:
        click.BadParameter: If validation fails
    """
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Tasks file does not exist: {value}")
    if path.suffix != ".md":
        raise click.BadParameter(f"Tasks file must be a .md file: {value}")
    return path.resolve()


def validate_project_dir(
    ctx: click.Context, param: click.Parameter, value: str
) -> Path:
    """Validate that project directory exists.

    Args:
        ctx: Click context
        param: Click parameter
        value: Directory path value

    Returns:
        Resolved absolute path to project directory

    Raises:
        click.BadParameter: If validation fails
    """
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Project directory does not exist: {value}")
    if not path.is_dir():
        raise click.BadParameter(f"Project path is not a directory: {value}")
    return path.resolve()


@click.command()
@click.option(
    "--tasks-file",
    required=True,
    callback=validate_tasks_file,
    help="Path to the tasks markdown file (must exist and have .md extension)",
)
@click.option(
    "--project-dir",
    required=True,
    callback=validate_project_dir,
    help="Root directory of the project for which workflows are started",
)
@click.option(
    "--agf-config",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to AGF config file (default: auto-discover .agf.yaml or agf.yaml)",
)
@click.option(
    "--sync-interval",
    default=30,
    type=int,
    help="Interval in seconds between task processing runs (default: 30)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run in read-only mode without executing operations",
)
@click.option(
    "--single-run",
    is_flag=True,
    default=False,
    help="Run once and exit instead of continuous scheduling",
)
def main(
    tasks_file: Path,
    project_dir: Path,
    agf_config: Path | None,
    sync_interval: int,
    dry_run: bool,
    single_run: bool,
) -> None:
    """Process tasks from a task list continuously or on-demand.

    This script periodically scans a tasks file, selects eligible tasks,
    and processes them in parallel batches. It supports both single-run
    mode for testing and continuous mode for production use.

    Configuration precedence: CLI arguments > AGF config file > defaults

    Examples:

        Single-run with dry-run mode:

            uv run agf/triggers/process_tasks.py --tasks-file ./tasks.md --project-dir . --dry-run --single-run

        Continuous mode with custom interval:

            uv run agf/triggers/process_tasks.py --tasks-file /home/my_tasks.md --project-dir /home/alex/projects/my_project --sync-interval 15
    """
    # Load AGF configuration
    agf_config_path = agf_config
    if agf_config_path is None:
        # Auto-discover config file
        agf_config_path = find_agf_config(project_dir)

    if agf_config_path is not None:
        try:
            system_config = load_agf_config_from_file(agf_config_path)
            log(f"Loaded AGF config from: {agf_config_path}")
        except Exception as e:
            log(f"Warning: Failed to load AGF config from {agf_config_path}: {e}")
            log("Using default configuration")
            system_config = AGFConfig.default()
    else:
        log("No AGF config file found, using defaults")
        system_config = AGFConfig.default()

    # Create CLI config
    cli_config = CLIConfig(
        tasks_file=tasks_file,
        project_dir=project_dir,
        agf_config=agf_config,
        sync_interval=sync_interval,
        dry_run=dry_run,
        single_run=single_run,
    )

    # Merge configurations with precedence: CLI > AGF > defaults
    effective_config = merge_configs(system_config, cli_config)

    log("Starting task processing trigger")
    log(f"Tasks file: {tasks_file}")
    log(f"Project dir: {project_dir}")
    log(f"Sync interval: {sync_interval}s")
    log(f"Dry run: {dry_run}")
    log(f"Single run: {single_run}")
    log(f"Concurrent tasks: {effective_config.concurrent_tasks}")

    # Initialize TaskManager
    try:
        markdown_source = MarkdownTaskSource(file_path=str(effective_config.tasks_file))
        task_manager = TaskManager(task_source=markdown_source)
        worktree_count = len(task_manager.list_worktrees())
        log(f"Initialized TaskManager with {worktree_count} worktrees")
    except Exception as e:
        log(f"Error initializing TaskManager: {e}")
        sys.exit(1)

    context = TriggerContext()

    # Single-run mode
    if effective_config.single_run:
        context.current_iteration = 1
        run_iteration(task_manager, effective_config, context.current_iteration)
        log("Single run completed, exiting")
        return

    # Continuous mode with staggered execution
    setup_signal_handlers(context)

    # Run first iteration immediately
    context.current_iteration = 1
    run_iteration(task_manager, effective_config, context.current_iteration)

    # Schedule subsequent iterations
    # Use simple sleep loop to ensure staggered execution (no overlapping batches)
    log(f"Scheduling next iteration in {sync_interval}s")

    while context.running:
        # Sleep for the interval, checking running flag for responsiveness
        for _ in range(sync_interval):
            if not context.running:
                break
            time.sleep(1)

        # Run next iteration if still running
        if context.running:
            context.current_iteration += 1
            run_iteration(task_manager, effective_config, context.current_iteration)
            if context.running:
                log(f"Next iteration in {sync_interval}s")

    log("Trigger stopped")


if __name__ == "__main__":
    main()
