"""Claude Code agent implementation."""

import json
import re
import shlex
import shutil
import subprocess
import time
from typing import Any

from .base import AgentConfig, AgentResult, JSONValue, ModelMapping
from .exceptions import (
    AgentNotFoundError,
    AgentOutputParseError,
    AgentTimeoutError,
)
from .models import CommandTemplate


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

        # Log the command if logger is configured
        if config.logger is not None:
            config.logger(shlex.join(cmd))

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

        # Create successful result
        agent_result = AgentResult(
            success=True,
            output=output,
            parsed_output=parsed_output,
            error=None,
            exit_code=result.returncode,
            duration_seconds=duration,
            agent_name=self.name,
        )

        # Extract JSON output if requested
        if config.json_output:
            agent_result.json_output = self.extract_json_output(agent_result)

        return agent_result

    def run_command(
        self, command_template: CommandTemplate, config: AgentConfig | None = None
    ) -> AgentResult:
        """Execute Claude Code with a structured command template.

        This method provides a unified interface for command execution, merging
        template-level configuration (model, json_output) with execution-level
        configuration (timeout, working directory, etc.).

        Args:
            command_template: Structured command with metadata and configuration
            config: Optional execution configuration (timeout, working dir, etc.)

        Returns:
            AgentResult containing the execution outcome and any extracted data
        """
        # Initialize config if not provided
        config = config or AgentConfig()

        # Merge template configuration into config
        # Template values take precedence over config defaults
        if command_template.model is not None:
            config.model = command_template.model.value

        if command_template.json_output:
            config.json_output = True

        # Format prompt with namespace and params
        # Escape double and single quotes in params to prevent command parsing issues
        params_str = (
            " ".join(f'"{str(p).replace('"', '\\"').replace("'", "\\'")}"' for p in command_template.params)
            if command_template.params
            else ""
        )
        prompt = f"/{command_template.namespace}:{command_template.prompt} {params_str}".rstrip()

        # Execute using the existing run method with merged config
        return self.run(prompt, config)

    def _build_command(self, prompt: str, config: AgentConfig) -> list[str]:
        """Build the CLI command with all options."""
        cmd = [self.CLI_COMMAND]

        # Non-interactive mode with prompt
        cmd.extend(["-p", prompt])

        # Output format
        cmd.extend(["--output-format", config.output_format])

        # Model selection - resolve abstract model type to concrete model name
        if config.model:
            concrete_model = ModelMapping.get_model(self.name, config.model)
            if concrete_model:
                cmd.extend(["--model", concrete_model])
            else:
                # Fall back to using the model as-is if no mapping exists
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
            raise AgentOutputParseError(self.name, output, f"Invalid JSON: {e}") from e

    def extract_json_output(self, result: AgentResult) -> JSONValue:
        """Extract JSON output from Claude Code result.

        Claude Code returns structured JSON with a "result" field containing
        the actual text output. This method searches for ```json blocks within
        that result field and extracts the first one found.

        Args:
            result: The agent result containing parsed output

        Returns:
            Extracted JSON value (can be dict, list, str, int, float, bool, or None)
        """
        if not result.parsed_output or not isinstance(result.parsed_output, dict):
            return None

        # Get the result field from parsed output
        result_text = result.parsed_output.get("result")
        if not result_text or not isinstance(result_text, str):
            return None

        # Search for ```json blocks (case insensitive)
        pattern = r"```json\s*\n(.*?)\n```"
        match = re.search(pattern, result_text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        json_content = match.group(1).strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            return None
