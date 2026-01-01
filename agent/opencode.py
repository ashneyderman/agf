"""OpenCode agent implementation."""

import json
import shutil
import subprocess
import time
from typing import Any

from .base import Agent, AgentConfig, AgentResult
from .exceptions import (
    AgentExecutionError,
    AgentNotFoundError,
    AgentOutputParseError,
    AgentTimeoutError,
)


class OpenCodeAgent:
    """Agent implementation for OpenCode CLI."""

    CLI_COMMAND = "opencode"

    @property
    def name(self) -> str:
        """Return the agent identifier."""
        return "opencode"

    def run(self, prompt: str, config: AgentConfig | None = None) -> AgentResult:
        """Execute OpenCode with the given prompt."""
        config = config or AgentConfig()
        start_time = time.time()

        # Check if CLI is available
        if not self._is_cli_available():
            raise AgentNotFoundError(self.name)

        # Build the command
        cmd = self._build_command(prompt, config)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds,
                cwd=config.working_dir,
            )
        except subprocess.TimeoutExpired as e:
            raise AgentTimeoutError(self.name, config.timeout_seconds) from e
        except FileNotFoundError as e:
            raise AgentNotFoundError(self.name) from e

        duration = time.time() - start_time
        output = result.stdout
        stderr = result.stderr

        # Parse output if JSON format
        parsed_output = None
        if config.output_format == "json" and output:
            parsed_output = self._parse_json_output(output)

        # Check for errors
        if result.returncode != 0:
            return AgentResult(
                success=False,
                output=output,
                parsed_output=parsed_output,
                error=stderr or f"Process exited with code {result.returncode}",
                exit_code=result.returncode,
                duration_seconds=duration,
                agent_name=self.name,
            )

        return AgentResult(
            success=True,
            output=output,
            parsed_output=parsed_output,
            error=None,
            exit_code=result.returncode,
            duration_seconds=duration,
            agent_name=self.name,
        )

    def _build_command(self, prompt: str, config: AgentConfig) -> list[str]:
        """Build the CLI command with all options."""
        cmd = [self.CLI_COMMAND, "run"]

        # The prompt comes after 'run'
        cmd.append(prompt)

        # Output format (OpenCode uses --format)
        if config.output_format == "json":
            cmd.extend(["--format", "json"])

        # Model selection (OpenCode uses provider/model format)
        if config.model:
            cmd.extend(["--model", config.model])

        # Agent selection
        if config.opencode_agent:
            cmd.extend(["--agent", config.opencode_agent])

        # File attachments
        if config.files:
            for file_path in config.files:
                cmd.extend(["--file", file_path])

        # Extra arguments
        cmd.extend(config.extra_args)

        return cmd

    def _is_cli_available(self) -> bool:
        """Check if the OpenCode CLI is available in PATH."""
        return shutil.which(self.CLI_COMMAND) is not None

    def _parse_json_output(self, output: str) -> dict[str, Any] | list[Any] | None:
        """Parse JSON output from the agent.

        OpenCode outputs NDJSON (Newline Delimited JSON) where each line
        is a separate JSON object representing an event.
        """
        lines = output.strip().split("\n")
        events = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise AgentOutputParseError(
                    self.name, output, f"Invalid JSON on line {line_num}: {e}"
                ) from e

        return events
