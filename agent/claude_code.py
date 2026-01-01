"""Claude Code agent implementation."""

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


class ClaudeCodeAgent:
    """Agent implementation for Claude Code CLI."""

    CLI_COMMAND = "claude"

    @property
    def name(self) -> str:
        """Return the agent identifier."""
        return "claude-code"

    def run(self, prompt: str, config: AgentConfig | None = None) -> AgentResult:
        """Execute Claude Code with the given prompt."""
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
        cmd = [self.CLI_COMMAND]

        # Non-interactive mode with prompt
        cmd.extend(["-p", prompt])

        # Output format
        cmd.extend(["--output-format", config.output_format])

        # Model selection
        if config.model:
            cmd.extend(["--model", config.model])

        # Skip permissions (for automated workflows)
        if config.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        # Max turns
        if config.max_turns is not None:
            cmd.extend(["--max-turns", str(config.max_turns)])

        # Tools
        if config.tools:
            cmd.extend(["--tools", ",".join(config.tools)])

        # Append system prompt
        if config.append_system_prompt:
            cmd.extend(["--append-system-prompt", config.append_system_prompt])

        # Extra arguments
        cmd.extend(config.extra_args)

        return cmd

    def _is_cli_available(self) -> bool:
        """Check if the Claude CLI is available in PATH."""
        return shutil.which(self.CLI_COMMAND) is not None

    def _parse_json_output(self, output: str) -> dict[str, Any] | list[Any] | None:
        """Parse JSON output from the agent."""
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise AgentOutputParseError(
                self.name, output, f"Invalid JSON: {e}"
            ) from e
