"""Tests for the AgentRunner."""

from unittest.mock import MagicMock, patch

import pytest

from agent.base import AgentConfig, AgentResult
from agent.claude_code import ClaudeCodeAgent
from agent.exceptions import AgentError
from agent.opencode import OpenCodeAgent
from agent.runner import AgentRunner


class TestAgentRunner:
    """Tests for AgentRunner."""

    def test_list_agents(self):
        """Test that list_agents returns registered agents."""
        agents = AgentRunner.list_agents()
        assert "claude-code" in agents
        assert "opencode" in agents

    def test_get_agent_claude_code(self):
        """Test getting Claude Code agent by name."""
        agent = AgentRunner.get_agent("claude-code")
        assert isinstance(agent, ClaudeCodeAgent)
        assert agent.name == "claude-code"

    def test_get_agent_opencode(self):
        """Test getting OpenCode agent by name."""
        agent = AgentRunner.get_agent("opencode")
        assert isinstance(agent, OpenCodeAgent)
        assert agent.name == "opencode"

    def test_get_agent_unknown(self):
        """Test that getting an unknown agent raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            AgentRunner.get_agent("unknown-agent")

        assert "Unknown agent" in str(exc_info.value)
        assert "unknown-agent" in str(exc_info.value)

    @patch("agent.claude_code.shutil.which")
    @patch("agent.claude_code.subprocess.run")
    def test_run_claude_code(self, mock_run, mock_which):
        """Test running Claude Code via AgentRunner."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        result = AgentRunner.run("claude-code", "test prompt")

        assert result.success is True
        assert result.agent_name == "claude-code"

    @patch("agent.opencode.shutil.which")
    @patch("agent.opencode.subprocess.run")
    def test_run_opencode(self, mock_run, mock_which):
        """Test running OpenCode via AgentRunner."""
        mock_which.return_value = "/usr/bin/opencode"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        result = AgentRunner.run("opencode", "test prompt")

        assert result.success is True
        assert result.agent_name == "opencode"

    @patch("agent.claude_code.shutil.which")
    @patch("agent.claude_code.subprocess.run")
    def test_run_with_config(self, mock_run, mock_which):
        """Test running an agent with custom configuration."""
        mock_which.return_value = "/usr/bin/claude"
        mock_run.return_value = MagicMock(
            stdout='{"result": "success"}',
            stderr="",
            returncode=0,
        )

        config = AgentConfig(model="sonnet", timeout_seconds=600)
        result = AgentRunner.run("claude-code", "test prompt", config)

        assert result.success is True
        # Verify the command includes the model
        call_args = mock_run.call_args[0][0]
        assert "--model" in call_args
        assert "sonnet" in call_args

    def test_register_custom_agent(self):
        """Test registering a custom agent."""

        class CustomAgent:
            @property
            def name(self) -> str:
                return "custom-agent"

            def run(self, prompt: str, config: AgentConfig | None = None) -> AgentResult:
                return AgentResult(
                    success=True,
                    output="custom output",
                    exit_code=0,
                    duration_seconds=0.1,
                    agent_name=self.name,
                )

        AgentRunner.register_agent(CustomAgent)

        assert "custom-agent" in AgentRunner.list_agents()
        agent = AgentRunner.get_agent("custom-agent")
        assert agent.name == "custom-agent"

        # Clean up
        del AgentRunner._registry["custom-agent"]
