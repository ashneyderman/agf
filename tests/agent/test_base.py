"""Tests for the agent base module."""

import pytest

from agent.base import AgentConfig, AgentResult


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = AgentResult(
            success=True,
            output='{"message": "hello"}',
            exit_code=0,
            duration_seconds=1.5,
            agent_name="test-agent",
            parsed_output={"message": "hello"},
        )
        assert result.success is True
        assert result.output == '{"message": "hello"}'
        assert result.exit_code == 0
        assert result.duration_seconds == 1.5
        assert result.agent_name == "test-agent"
        assert result.parsed_output == {"message": "hello"}
        assert result.error is None

    def test_create_failure_result(self):
        """Test creating a failed result."""
        result = AgentResult(
            success=False,
            output="",
            exit_code=1,
            duration_seconds=0.5,
            agent_name="test-agent",
            error="Command failed",
        )
        assert result.success is False
        assert result.exit_code == 1
        assert result.error == "Command failed"
        assert result.parsed_output is None


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = AgentConfig()
        assert config.model is None
        assert config.timeout_seconds == 300
        assert config.working_dir is None
        assert config.output_format == "json"
        assert config.extra_args == []
        assert config.skip_permissions is False
        assert config.max_turns is None
        assert config.tools is None
        assert config.append_system_prompt is None
        assert config.opencode_agent is None
        assert config.files is None

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = AgentConfig(
            model="sonnet",
            timeout_seconds=600,
            working_dir="/tmp",
            output_format="text",
            extra_args=["--verbose"],
            skip_permissions=True,
            max_turns=5,
            tools=["Read", "Write"],
            append_system_prompt="Be concise",
            opencode_agent="coder",
            files=["file1.py", "file2.py"],
        )
        assert config.model == "sonnet"
        assert config.timeout_seconds == 600
        assert config.working_dir == "/tmp"
        assert config.output_format == "text"
        assert config.extra_args == ["--verbose"]
        assert config.skip_permissions is True
        assert config.max_turns == 5
        assert config.tools == ["Read", "Write"]
        assert config.append_system_prompt == "Be concise"
        assert config.opencode_agent == "coder"
        assert config.files == ["file1.py", "file2.py"]
