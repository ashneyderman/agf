"""Tests for the OpenCode agent."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from agf.agent.base import AgentConfig
from agf.agent.exceptions import (
    AgentNotFoundError,
    AgentOutputParseError,
    AgentTimeoutError,
)
from agf.agent.opencode import OpenCodeAgent


class TestOpenCodeAgent:
    """Tests for OpenCodeAgent."""

    def test_name_property(self):
        """Test that the agent name is correct."""
        agent = OpenCodeAgent()
        assert agent.name == "opencode"

    def test_build_command_basic(self):
        """Test basic command building."""
        agent = OpenCodeAgent()
        config = AgentConfig()
        cmd = agent._build_command("Hello world", config)

        assert cmd[0] == "opencode"
        assert cmd[1] == "run"
        assert "Hello world" in cmd
        assert "--format" in cmd
        assert "json" in cmd

    def test_build_command_with_model(self):
        """Test command building with direct model name (fallback behavior)."""
        agent = OpenCodeAgent()
        config = AgentConfig(model="anthropic/claude-sonnet")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        # Direct model name should pass through as-is when no mapping exists
        assert cmd[model_idx + 1] == "anthropic/claude-sonnet"

    def test_build_command_with_model_type_thinking(self):
        """Test command building with 'thinking' model type."""
        agent = OpenCodeAgent()
        config = AgentConfig(model="thinking")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "github-copilot/claude-opus-4.5"

    def test_build_command_with_model_type_standard(self):
        """Test command building with 'standard' model type."""
        agent = OpenCodeAgent()
        config = AgentConfig(model="standard")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "github-copilot/claude-sonnet-4.5"

    def test_build_command_with_model_type_light(self):
        """Test command building with 'light' model type."""
        agent = OpenCodeAgent()
        config = AgentConfig(model="light")
        cmd = agent._build_command("test", config)

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "github-copilot/claude-haiku-4.5"

    def test_build_command_with_agent(self):
        """Test command building with agent selection."""
        agent = OpenCodeAgent()
        config = AgentConfig(opencode_agent="coder")
        cmd = agent._build_command("test", config)

        assert "--agent" in cmd
        agent_idx = cmd.index("--agent")
        assert cmd[agent_idx + 1] == "coder"

    def test_build_command_with_files(self):
        """Test command building with file attachments."""
        agent = OpenCodeAgent()
        config = AgentConfig(files=["file1.py", "file2.py"])
        cmd = agent._build_command("test", config)

        file_indices = [i for i, x in enumerate(cmd) if x == "--file"]
        assert len(file_indices) == 2
        assert cmd[file_indices[0] + 1] == "file1.py"
        assert cmd[file_indices[1] + 1] == "file2.py"

    def test_build_command_with_extra_args(self):
        """Test command building with extra arguments."""
        agent = OpenCodeAgent()
        config = AgentConfig(extra_args=["--continue", "--share"])
        cmd = agent._build_command("test", config)

        assert "--continue" in cmd
        assert "--share" in cmd

    @patch("agf.agent.opencode.shutil.which")
    def test_cli_not_available(self, mock_which):
        """Test that AgentNotFoundError is raised when CLI is not found."""
        mock_which.return_value = None
        agent = OpenCodeAgent()

        with pytest.raises(AgentNotFoundError) as exc_info:
            agent.run("test prompt")

        assert "opencode" in str(exc_info.value)

    @patch("agf.agent.opencode.shutil.which")
    @patch("agf.agent.opencode.subprocess.run")
    def test_successful_run(self, mock_run, mock_which):
        """Test a successful agent run."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = OpenCodeAgent()
        result = agent.run("test prompt")

        assert result.success is True
        assert result.exit_code == 0
        assert result.parsed_output == [{"result": "success"}]
        assert result.agent_name == "opencode"

    @patch("agf.agent.opencode.shutil.which")
    @patch("agf.agent.opencode.subprocess.run")
    def test_failed_run(self, mock_run, mock_which):
        """Test a failed agent run."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Error occurred",
            returncode=1,
        )

        agent = OpenCodeAgent()
        result = agent.run("test prompt")

        assert result.success is False
        assert result.exit_code == 1
        assert result.error == "Error occurred"

    @patch("agf.agent.opencode.shutil.which")
    @patch("agf.agent.opencode.subprocess.run")
    def test_timeout(self, mock_run, mock_which):
        """Test that timeout is handled correctly."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="opencode", timeout=10)

        agent = OpenCodeAgent()
        config = AgentConfig(timeout_seconds=10)

        with pytest.raises(AgentTimeoutError) as exc_info:
            agent.run("test prompt", config)

        assert "10 seconds" in str(exc_info.value)

    @patch("agf.agent.opencode.shutil.which")
    @patch("agf.agent.opencode.subprocess.run")
    def test_invalid_json_output(self, mock_run, mock_which):
        """Test that invalid JSON output raises AgentOutputParseError."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.return_value = MagicMock(
            stdout="not valid json",
            stderr="",
            returncode=0,
        )

        agent = OpenCodeAgent()
        config = AgentConfig(output_format="json")

        with pytest.raises(AgentOutputParseError) as exc_info:
            agent.run("test prompt", config)

        assert "Invalid JSON" in str(exc_info.value)

    @patch("agf.agent.opencode.shutil.which")
    @patch("agf.agent.opencode.subprocess.run")
    def test_text_output_format(self, mock_run, mock_which):
        """Test that text output format doesn't parse JSON."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.return_value = MagicMock(
            stdout="Plain text output",
            stderr="",
            returncode=0,
        )

        agent = OpenCodeAgent()
        config = AgentConfig(output_format="text")
        result = agent.run("test prompt", config)

        assert result.success is True
        assert result.output == "Plain text output"
        assert result.parsed_output is None
