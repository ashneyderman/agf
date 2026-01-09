"""Tests for the Claude Code agent."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from agf.agent.base import AgentConfig
from agf.agent.claude_code import ClaudeCodeAgent
from agf.agent.exceptions import (
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

    @patch("agf.agent.claude_code.shutil.which")
    def test_cli_not_available(self, mock_which):
        """Test that AgentNotFoundError is raised when CLI is not found."""
        mock_which.return_value = None
        agent = ClaudeCodeAgent()

        with pytest.raises(AgentNotFoundError) as exc_info:
            agent.run("test prompt")

        assert "claude-code" in str(exc_info.value)

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
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

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
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

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_timeout(self, mock_run, mock_which):
        """Test that timeout is handled correctly."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=10)

        agent = ClaudeCodeAgent()
        config = AgentConfig(timeout_seconds=10)

        with pytest.raises(AgentTimeoutError) as exc_info:
            agent.run("test prompt", config)

        assert "10 seconds" in str(exc_info.value)

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
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

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
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

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_with_logger(self, mock_run, mock_which):
        """Test that the logger is called with the command when configured."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        # Create a mock logger function
        mock_logger = MagicMock()

        agent = ClaudeCodeAgent()
        config = AgentConfig(logger=mock_logger)
        result = agent.run("test prompt", config)

        # Verify the logger was called exactly once
        assert mock_logger.call_count == 1

        # Verify the logged command contains expected parts
        logged_command = mock_logger.call_args[0][0]
        assert "claude" in logged_command
        assert "-p" in logged_command
        assert "test prompt" in logged_command
        assert "--output-format" in logged_command

        # Verify the run was successful
        assert result.success is True

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_without_logger(self, mock_run, mock_which):
        """Test that running without a logger works correctly."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        config = AgentConfig(logger=None)
        result = agent.run("test prompt", config)

        # Verify the run was successful without errors
        assert result.success is True
        assert result.exit_code == 0

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_with_params(self, mock_run, mock_which):
        """Test run_command wraps parameters in double quotes."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
            params=["param1", "param2"],
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called with properly quoted parameters
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify parameters are wrapped in double quotes
        assert '/test:command "param1" "param2"' == prompt

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_with_params_containing_spaces(self, mock_run, mock_which):
        """Test run_command handles parameters with spaces correctly."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
            params=["param with spaces", "another param"],
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called with properly quoted parameters
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify parameters with spaces are wrapped in double quotes
        assert '/test:command "param with spaces" "another param"' == prompt

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_with_params_containing_quotes(self, mock_run, mock_which):
        """Test run_command escapes double quotes in parameters."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
            params=['param with "quotes"', "normal"],
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called with properly quoted and escaped parameters
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify double quotes are escaped and parameters are wrapped in double quotes
        assert '/test:command "param with \\"quotes\\"" "normal"' == prompt

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_with_params_containing_single_quotes(self, mock_run, mock_which):
        """Test run_command escapes single quotes in parameters."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
            params=["param with 'single quotes'", "normal"],
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called with properly quoted and escaped parameters
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify single quotes are escaped and parameters are wrapped in double quotes
        assert r'/test:command "param with \'single quotes\'" "normal"' == prompt

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_with_params_containing_mixed_quotes(self, mock_run, mock_which):
        """Test run_command escapes both single and double quotes in parameters."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
            params=['param with "double" and \'single\' quotes'],
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called with properly quoted and escaped parameters
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify both quote types are escaped and parameters are wrapped in double quotes
        assert r'/test:command "param with \"double\" and \'single\' quotes"' == prompt

    @patch("agf.agent.claude_code.shutil.which")
    @patch("agf.agent.claude_code.subprocess.run")
    def test_run_command_without_params(self, mock_run, mock_which):
        """Test run_command works without parameters."""
        from agf.agent.models import CommandTemplate

        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        agent = ClaudeCodeAgent()
        template = CommandTemplate(
            namespace="test",
            prompt="command",
        )
        result = agent.run_command(template)

        # Verify the run was successful
        assert result.success is True

        # Verify the command was called
        mock_run.assert_called_once()
        called_cmd = mock_run.call_args[0][0]

        # Find the -p flag index to get the prompt
        p_idx = called_cmd.index("-p")
        prompt = called_cmd[p_idx + 1]

        # Verify no parameters are appended
        assert '/test:command' == prompt
