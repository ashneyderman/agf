"""Tests for the agent base module."""

import pytest

from af.agent.base import AgentConfig, AgentResult, ModelMapping


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


class TestModelMapping:
    """Tests for ModelMapping class."""

    def test_get_model_claude_code_thinking(self):
        """Test getting thinking model for claude-code."""
        model = ModelMapping.get_model("claude-code", "thinking")
        assert model == "opus"

    def test_get_model_claude_code_standard(self):
        """Test getting standard model for claude-code."""
        model = ModelMapping.get_model("claude-code", "standard")
        assert model == "sonnet"

    def test_get_model_claude_code_light(self):
        """Test getting light model for claude-code."""
        model = ModelMapping.get_model("claude-code", "light")
        assert model == "haiku"

    def test_get_model_opencode_thinking(self):
        """Test getting thinking model for opencode."""
        model = ModelMapping.get_model("opencode", "thinking")
        assert model == "github-copilot/claude-opus-4.5"

    def test_get_model_opencode_standard(self):
        """Test getting standard model for opencode."""
        model = ModelMapping.get_model("opencode", "standard")
        assert model == "github-copilot/claude-sonnet-4.5"

    def test_get_model_opencode_light(self):
        """Test getting light model for opencode."""
        model = ModelMapping.get_model("opencode", "light")
        assert model == "github-copilot/claude-haiku-4.5"

    def test_get_model_unknown_agent(self):
        """Test that unknown agent returns None."""
        model = ModelMapping.get_model("unknown-agent", "standard")
        assert model is None

    def test_get_model_unknown_model_type(self):
        """Test that unknown model type returns None."""
        model = ModelMapping.get_model("claude-code", "unknown-type")
        assert model is None

    def test_list_agents(self):
        """Test listing registered agents."""
        agents = ModelMapping.list_agents()
        assert "claude-code" in agents
        assert "opencode" in agents

    def test_list_models(self):
        """Test listing models for an agent."""
        models = ModelMapping.list_models("claude-code")
        assert models is not None
        assert "thinking" in models
        assert "standard" in models
        assert "light" in models

    def test_list_models_unknown_agent(self):
        """Test listing models for unknown agent returns None."""
        models = ModelMapping.list_models("unknown-agent")
        assert models is None

    def test_register_agent(self):
        """Test registering a new agent."""
        ModelMapping.register_agent(
            "test-agent",
            {
                "thinking": "test-opus",
                "standard": "test-sonnet",
                "light": "test-haiku",
            },
        )

        assert ModelMapping.get_model("test-agent", "thinking") == "test-opus"
        assert ModelMapping.get_model("test-agent", "standard") == "test-sonnet"
        assert ModelMapping.get_model("test-agent", "light") == "test-haiku"

        # Clean up
        del ModelMapping._mappings["test-agent"]

    def test_update_model(self):
        """Test updating a specific model mapping."""
        # Save original value
        original = ModelMapping.get_model("claude-code", "thinking")

        # Update
        ModelMapping.update_model("claude-code", "thinking", "new-opus")
        assert ModelMapping.get_model("claude-code", "thinking") == "new-opus"

        # Restore
        ModelMapping.update_model("claude-code", "thinking", original)
