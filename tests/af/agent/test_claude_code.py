"""Tests for the Claude Code agent."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from af.agent.base import AgentConfig
from af.agent.claude_code import ClaudeCodeAgent
from af.agent.exceptions import (
    AgentNotFoundError,
    AgentOutputParseError,
    AgentTimeoutError,
)


class TestClaudeCodeAgent:
    """Tests for ClaudeCodeAgent."""

    def test_name_property(self):
        """Test that the agent name is correct."""
        agent = ClaudeCodeAgent()
        assert agent.name == "claude-code"

    def test_build_command_basic(self):
        """Test basic command building."""
        agent = ClaudeCodeAgent()
        config = AgentConfig()
        cmd = agent._build_command("Hello world", config)

        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "Hello world" in cmd
        assert "--output-format" in cmd
        assert "json" in cmd

    def test_build_command_with_model(self):
        """Test command building with direct model name (fallback behavior)."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(model="sonnet")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        # Direct model name should pass through as-is when no mapping exists
        assert cmd[model_idx + 1] == "sonnet"

    def test_build_command_with_model_type_thinking(self):
        """Test command building with 'thinking' model type."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(model="thinking")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "opus"

    def test_build_command_with_model_type_standard(self):
        """Test command building with 'standard' model type."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(model="standard")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "sonnet"

    def test_build_command_with_model_type_light(self):
        """Test command building with 'light' model type."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(model="light")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "haiku"

    def test_build_command_with_skip_permissions(self):
        """Test command building with skip permissions flag."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(skip_permissions=True)
        cmd = agent._build_command("test", config)

        assert "--dangerously-skip-permissions" in cmd

    def test_build_command_with_max_turns(self):
        """Test command building with max turns."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(max_turns=5)
        cmd = agent._build_command("test", config)

        assert "--max-turns" in cmd
        turns_idx = cmd.index("--max-turns")
        assert cmd[turns_idx + 1] == "5"

    def test_build_command_with_tools(self):
        """Test command building with tools."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(tools=["Read", "Write", "Bash"])
        cmd = agent._build_command("test", config)

        assert "--tools" in cmd
        tools_idx = cmd.index("--tools")
        assert cmd[tools_idx + 1] == "Read,Write,Bash"

    def test_build_command_with_system_prompt(self):
        """Test command building with append system prompt."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(append_system_prompt="Be concise")
        cmd = agent._build_command("test", config)

        assert "--append-system-prompt" in cmd
        prompt_idx = cmd.index("--append-system-prompt")
        assert cmd[prompt_idx + 1] == "Be concise"

    def test_build_command_with_extra_args(self):
        """Test command building with extra arguments."""
        agent = ClaudeCodeAgent()
        config = AgentConfig(extra_args=["--verbose", "--debug"])
        cmd = agent._build_command("test", config)

        assert "--verbose" in cmd
        assert "--debug" in cmd

    @patch("af.agent.claude_code.shutil.which")
    def test_cli_not_available(self, mock_which):
        """Test that AgentNotFoundError is raised when CLI is not found."""
        mock_which.return_value = None
        agent = ClaudeCodeAgent()

        with pytest.raises(AgentNotFoundError) as exc_info:
            agent.run("test prompt")

        assert "claude-code" in str(exc_info.value)

    @patch("af.agent.claude_code.shutil.which")
    @patch("af.agent.claude_code.subprocess.run")
    def test_successful_run(self, mock_run, mock_which):
        """Test a successful agent run."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        result = agent.run("test prompt")

        assert result.success is True
        assert result.exit_code == 0
        assert result.parsed_output == {"result": "success"}
        assert result.agent_name == "claude-code"

    @patch("af.agent.claude_code.shutil.which")
    @patch("af.agent.claude_code.subprocess.run")
    def test_failed_run(self, mock_run, mock_which):
        """Test a failed agent run."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Error occurred",
            returncode=1,
        )

        agent = ClaudeCodeAgent()
        result = agent.run("test prompt")

        assert result.success is False
        assert result.exit_code == 1
        assert result.error == "Error occurred"

    @patch("af.agent.claude_code.shutil.which")
    @patch("af.agent.claude_code.subprocess.run")
    def test_timeout(self, mock_run, mock_which):
        """Test that timeout is handled correctly."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=10)

        agent = ClaudeCodeAgent()
        config = AgentConfig(timeout_seconds=10)

        with pytest.raises(AgentTimeoutError) as exc_info:
            agent.run("test prompt", config)

        assert "10 seconds" in str(exc_info.value)

    @patch("af.agent.claude_code.shutil.which")
    @patch("af.agent.claude_code.subprocess.run")
    def test_invalid_json_output(self, mock_run, mock_which):
        """Test that invalid JSON output raises AgentOutputParseError."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout="not valid json",
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        config = AgentConfig(output_format="json")

        with pytest.raises(AgentOutputParseError) as exc_info:
            agent.run("test prompt", config)

        assert "Invalid JSON" in str(exc_info.value)

    @patch("af.agent.claude_code.shutil.which")
    @patch("af.agent.claude_code.subprocess.run")
    def test_text_output_format(self, mock_run, mock_which):
        """Test that text output format doesn't parse JSON."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout="Plain text output",
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        config = AgentConfig(output_format="text")
        result = agent.run("test prompt", config)

        assert result.success is True
        assert result.output == "Plain text output"
        assert result.parsed_output is None
