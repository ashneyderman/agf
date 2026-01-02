#!/usr/bin/env python3
"""Task triggering script that discovers and initiates ready-to-run tasks."""

import json
import re
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import schedule

from agent.base import AgentConfig, AgentType, ModelType
from agent.runner import AgentRunner


def extract_json_from_markdown(text: str) -> str | None:
    """Extract JSON content from markdown code blocks.

    Looks for ```json ... ``` or ``` ... ``` blocks and extracts the content.
    Returns the first JSON block found, or None if no block is found.
    """
    # Try to find ```json ... ``` blocks first
    json_pattern = r"```json\s*([\s\S]*?)\s*```"
    match = re.search(json_pattern, text)
    if match:
        return match.group(1).strip()

    # Fall back to generic ``` ... ``` blocks
    generic_pattern = r"```\s*([\s\S]*?)\s*```"
    match = re.search(generic_pattern, text)
    if match:
        return match.group(1).strip()

    return None


def extract_tasks_from_agent_result(
    parsed_output: dict[str, Any] | list[Any] | None,
) -> list[Any] | None:
    """Extract the tasks list from agent result.

    Supports multiple agent output formats:

    Claude Code returns a nested structure where:
    - parsed_output is a dict with 'type', 'result', etc.
    - The 'result' field contains text with JSON in markdown code blocks

    OpenCode returns a list of NDJSON events where:
    - Each event has a 'type' field
    - The 'text' type event contains the response in 'part.text'
    - The text contains JSON in markdown code blocks

    This function extracts and parses the actual tasks JSON.
    """
    if parsed_output is None:
        return None

    # Handle list input (could be OpenCode events or direct task list)
    if isinstance(parsed_output, list):
        # Empty list is a valid result (no tasks)
        if len(parsed_output) == 0:
            return parsed_output

        # Check if first item is a task structure (direct task list)
        if isinstance(parsed_output[0], dict) and "worktree_name" in parsed_output[0]:
            return parsed_output

        # Otherwise, look for OpenCode's 'text' type event containing the response
        for event in parsed_output:
            if not isinstance(event, dict):
                continue

            event_type = event.get("type")
            if event_type == "text":
                # OpenCode text events have the content in part.text
                part = event.get("part", {})
                text_content = part.get("text", "")
                if text_content:
                    json_str = extract_json_from_markdown(text_content)
                    if json_str:
                        try:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, list):
                                return parsed
                        except json.JSONDecodeError:
                            pass

        return None

    # If it's a dict, check for Claude Code result structure
    if isinstance(parsed_output, dict):
        # Check for the 'result' field containing the text response
        result_text = parsed_output.get("result")
        if result_text and isinstance(result_text, str):
            # Extract JSON from markdown code blocks
            json_str = extract_json_from_markdown(result_text)
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

        # Maybe parsed_output itself is the tasks list structure
        if "worktree_name" in parsed_output:
            return [parsed_output]

    return None


class TriggerContext:
    """Context for managing trigger state and graceful shutdown."""

    def __init__(self) -> None:
        self.running = True
        self.current_iteration = 0

    def stop(self) -> None:
        """Signal the trigger to stop."""
        self.running = False


def log(message: str, dry_run: bool = False) -> None:
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "[DRY-RUN] " if dry_run else ""
    click.echo(f"[{timestamp}] {prefix}{message}")


def validate_tasks_file(ctx: click.Context, param: click.Parameter, value: str) -> Path:
    """Validate that tasks file exists and has .md extension."""
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Tasks file does not exist: {value}")
    if path.suffix != ".md":
        raise click.BadParameter(f"Tasks file must be a .md file: {value}")
    return path.resolve()


def validate_project_dir(
    ctx: click.Context, param: click.Parameter, value: str
) -> Path:
    """Validate that project directory exists."""
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Project directory does not exist: {value}")
    if not path.is_dir():
        raise click.BadParameter(f"Project path is not a directory: {value}")
    return path.resolve()


def build_process_tasks_prompt(tasks_file: Path) -> str:
    """Build the prompt to invoke /af:process_tasks."""
    return f"/af:process_tasks {tasks_file}"


def invoke_process_tasks(
    tasks_file: Path,
    project_dir: Path,
    agent: str,
    model: str,
    dry_run: bool = False,
) -> list[Any] | None:
    """Invoke the /af:process_tasks prompt and return parsed results."""
    prompt = build_process_tasks_prompt(tasks_file)

    if dry_run:
        log(f"Would invoke: {prompt}", dry_run=True)
        log(f"Working directory: {project_dir}", dry_run=True)
        return []

    log(f"Invoking: {prompt}")

    config = AgentConfig(
        working_dir=str(project_dir),
        output_format="json",
        timeout_seconds=300,
        skip_permissions=True,
        model=model,
    )

    try:
        result = AgentRunner.run(agent, prompt, config)

        log(f"result.parsed_output: {result.parsed_output}")

        if not result.success:
            log(f"Agent execution failed: {result.error}")
            return None

        # Extract tasks from the nested Claude Code result structure
        tasks = extract_tasks_from_agent_result(result.parsed_output)
        if tasks is None:
            log("Could not extract tasks from agent response")
            return None

        return tasks
    except Exception as e:
        log(f"Error invoking agent: {e}")
        return None


def parse_and_print_results(results: dict[str, Any] | list[Any] | None) -> int:
    """Parse results and print eligible tasks. Returns count of eligible tasks."""
    if results is None:
        log("No results to process (agent returned error)")
        return 0

    if not results:
        log("No eligible tasks found")
        return 0

    if not isinstance(results, list):
        log(f"Unexpected result format: {type(results)}")
        return 0

    total_tasks = 0
    for worktree_data in results:
        if not isinstance(worktree_data, dict):
            continue

        worktree_name = worktree_data.get("worktree_name", "unknown")
        tasks = worktree_data.get("tasks_to_start", [])

        if not tasks:
            continue

        log(f"Worktree: {worktree_name}")
        for task in tasks:
            if isinstance(task, dict):
                description = task.get("description", "No description")
                tags = task.get("tags", [])
                tags_str = f" [{', '.join(tags)}]" if tags else ""
                log(f"  - {description}{tags_str}")
                total_tasks += 1

    log(f"Total eligible tasks: {total_tasks}")
    return total_tasks


def run_iteration(
    tasks_file: Path,
    project_dir: Path,
    agent: str,
    model: str,
    dry_run: bool,
    iteration: int,
) -> None:
    """Run a single iteration of task discovery."""
    log(f"--- Iteration {iteration} ---")
    start_time = time.time()

    results = invoke_process_tasks(tasks_file, project_dir, agent, model, dry_run)
    parse_and_print_results(results)

    duration = time.time() - start_time
    log(f"Iteration {iteration} completed in {duration:.2f}s")


def setup_signal_handlers(context: TriggerContext) -> None:
    """Setup signal handlers for graceful shutdown."""

    def handle_signal(signum: int, frame: Any) -> None:
        signal_name = signal.Signals(signum).name
        log(f"Received {signal_name}, shutting down gracefully...")
        context.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


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
    "--sync-interval",
    default=30,
    type=int,
    help="Interval in seconds between task discovery runs (default: 30)",
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
@click.option(
    "--agent",
    type=click.Choice(AgentType.values(), case_sensitive=False),
    default=AgentType.default(),
    help="Agent to use for task processing (default: claude-code)",
)
@click.option(
    "--model",
    type=click.Choice(ModelType.values(), case_sensitive=False),
    default=ModelType.default(),
    help="Model type to use (default: standard)",
)
def main(
    tasks_file: Path,
    project_dir: Path,
    sync_interval: int,
    dry_run: bool,
    single_run: bool,
    agent: str,
    model: str,
) -> None:
    """Find and start eligible tasks from a task list.

    This script periodically scans a tasks file and identifies tasks that are
    ready to be picked up by agents. It calls the /af:process_tasks prompt
    to analyze the task list and returns eligible tasks.

    Example usage:

        uv run triggers/find_and_start_tasks.py --tasks-file ./tasks.md --project-dir .

        uv run triggers/find_and_start_tasks.py --tasks-file ./tasks.md --project-dir . --dry-run --single-run
    """
    log(f"Starting task trigger")
    log(f"Tasks file: {tasks_file}")
    log(f"Project dir: {project_dir}")
    log(f"Sync interval: {sync_interval}s")
    log(f"Dry run: {dry_run}")
    log(f"Single run: {single_run}")
    log(f"Agent: {agent}")
    log(f"Model: {model}")

    context = TriggerContext()

    if single_run:
        context.current_iteration = 1
        run_iteration(
            tasks_file, project_dir, agent, model, dry_run, context.current_iteration
        )
        log("Single run completed, exiting")
        return

    # Continuous mode
    setup_signal_handlers(context)

    def scheduled_job() -> None:
        """Job function for the scheduler."""
        context.current_iteration += 1
        run_iteration(
            tasks_file, project_dir, agent, model, dry_run, context.current_iteration
        )

    # Run first iteration immediately
    context.current_iteration = 1
    run_iteration(
        tasks_file, project_dir, agent, model, dry_run, context.current_iteration
    )

    # Schedule subsequent iterations
    # Using schedule.every().seconds ensures the next run starts
    # sync_interval seconds AFTER the previous one completes
    log(f"Scheduling next iteration in {sync_interval}s")

    while context.running:
        # Sleep for the interval
        for _ in range(sync_interval):
            if not context.running:
                break
            time.sleep(1)

        if context.running:
            scheduled_job()
            if context.running:
                log(f"Next iteration in {sync_interval}s")

    log("Trigger stopped")


if __name__ == "__main__":
    main()
