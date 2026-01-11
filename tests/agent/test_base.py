"""Tests for agent base classes and ModelMapping."""


from agf.agent.base import ModelMapping
from agf.config import AGFConfig, AgentModelConfig


def test_model_mapping_from_agf_config():
    """Test that ModelMapping.from_agf_config() registers agents."""
    config = AGFConfig(
        agents={
            "test-agent": AgentModelConfig(
                thinking="test-thinking",
                standard="test-standard",
                light="test-light",
            )
        }
    )

    # Register from config
    ModelMapping.from_agf_config(config)

    # Verify agent is registered
    assert "test-agent" in ModelMapping.list_agents()
    assert ModelMapping.get_model("test-agent", "thinking") == "test-thinking"
    assert ModelMapping.get_model("test-agent", "standard") == "test-standard"
    assert ModelMapping.get_model("test-agent", "light") == "test-light"


def test_model_mapping_from_default_config():
    """Test registering default AGFConfig agents."""
    config = AGFConfig.default()

    # Register from default config
    ModelMapping.from_agf_config(config)

    # Verify default agents are registered
    assert "claude-code" in ModelMapping.list_agents()
    assert "opencode" in ModelMapping.list_agents()

    # Verify model mappings
    assert ModelMapping.get_model("claude-code", "standard") == "sonnet"
    assert (
        ModelMapping.get_model("opencode", "thinking")
        == "github-copilot/claude-opus-4.5"
    )


def test_model_mapping_from_config_updates_existing():
    """Test that from_agf_config updates existing agent mappings."""
    # First config
    config1 = AGFConfig(
        agents={
            "updatable-agent": AgentModelConfig(
                thinking="old-thinking",
                standard="old-standard",
                light="old-light",
            )
        }
    )
    ModelMapping.from_agf_config(config1)

    # Verify initial values
    assert ModelMapping.get_model("updatable-agent", "standard") == "old-standard"

    # Second config with updated values
    config2 = AGFConfig(
        agents={
            "updatable-agent": AgentModelConfig(
                thinking="new-thinking",
                standard="new-standard",
                light="new-light",
            )
        }
    )
    ModelMapping.from_agf_config(config2)

    # Verify updated values
    assert ModelMapping.get_model("updatable-agent", "thinking") == "new-thinking"
    assert ModelMapping.get_model("updatable-agent", "standard") == "new-standard"
    assert ModelMapping.get_model("updatable-agent", "light") == "new-light"


def test_model_mapping_from_config_multiple_agents():
    """Test registering multiple agents from config."""
    config = AGFConfig(
        agents={
            "agent-1": AgentModelConfig(
                thinking="t1", standard="s1", light="l1"
            ),
            "agent-2": AgentModelConfig(
                thinking="t2", standard="s2", light="l2"
            ),
            "agent-3": AgentModelConfig(
                thinking="t3", standard="s3", light="l3"
            ),
        }
    )

    ModelMapping.from_agf_config(config)

    # Verify all agents registered
    agents = ModelMapping.list_agents()
    assert "agent-1" in agents
    assert "agent-2" in agents
    assert "agent-3" in agents

    # Verify each has correct mappings
    assert ModelMapping.get_model("agent-1", "standard") == "s1"
    assert ModelMapping.get_model("agent-2", "light") == "l2"
    assert ModelMapping.get_model("agent-3", "thinking") == "t3"
