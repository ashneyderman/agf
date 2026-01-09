"""Tests for AGFConfig model."""

import pytest
from pydantic import ValidationError

from agf.config.models import AGFConfig, AgentModelConfig


def test_agf_config_default():
    """Test that AGFConfig.default() returns expected defaults."""
    config = AGFConfig.default()

    assert config.worktrees == ".worktrees"
    assert config.concurrent_tasks == 5
    assert config.agent == "claude-code"
    assert config.model_type == "standard"
    assert "claude-code" in config.agents
    assert "opencode" in config.agents


def test_agf_config_default_claude_code_models():
    """Test that default claude-code agent has correct model mappings."""
    config = AGFConfig.default()
    claude_code = config.agents["claude-code"]

    assert claude_code.thinking == "opus"
    assert claude_code.standard == "sonnet"
    assert claude_code.light == "haiku"


def test_agf_config_default_opencode_models():
    """Test that default opencode agent has correct model mappings."""
    config = AGFConfig.default()
    opencode = config.agents["opencode"]

    assert opencode.thinking == "github-copilot/claude-opus-4.5"
    assert opencode.standard == "github-copilot/claude-sonnet-4.5"
    assert opencode.light == "github-copilot/claude-haiku-4.5"


def test_agf_config_create_with_all_fields():
    """Test creating AGFConfig with all fields specified."""
    config = AGFConfig(
        worktrees=".custom-worktrees",
        concurrent_tasks=10,
        agent="opencode",
        model_type="thinking",
        agents={
            "custom-agent": AgentModelConfig(
                thinking="model-1", standard="model-2", light="model-3"
            )
        },
    )

    assert config.worktrees == ".custom-worktrees"
    assert config.concurrent_tasks == 10
    assert config.agent == "opencode"
    assert config.model_type == "thinking"
    assert "custom-agent" in config.agents
    assert config.agents["custom-agent"].thinking == "model-1"


def test_agf_config_create_with_partial_fields():
    """Test creating AGFConfig with partial fields uses defaults."""
    config = AGFConfig(agent="opencode")

    assert config.worktrees == ".worktrees"  # default
    assert config.concurrent_tasks == 5  # default
    assert config.agent == "opencode"  # specified
    assert config.model_type == "standard"  # default


def test_agf_config_negative_concurrent_tasks():
    """Test that negative concurrent_tasks raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        AGFConfig(concurrent_tasks=-1)

    assert "concurrent_tasks must be positive" in str(exc_info.value)


def test_agf_config_zero_concurrent_tasks():
    """Test that zero concurrent_tasks raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        AGFConfig(concurrent_tasks=0)

    assert "concurrent_tasks must be positive" in str(exc_info.value)


def test_agf_config_hyphen_alias_concurrent_tasks():
    """Test that YAML hyphen alias works for concurrent_tasks."""
    # Simulating YAML parsing which would use hyphen names
    config = AGFConfig(**{"concurrent-tasks": 10})

    assert config.concurrent_tasks == 10


def test_agf_config_hyphen_alias_model_type():
    """Test that YAML hyphen alias works for model_type."""
    # Simulating YAML parsing which would use hyphen names
    config = AGFConfig(**{"model-type": "thinking"})

    assert config.model_type == "thinking"


def test_agf_config_populate_by_name():
    """Test that both hyphen and underscore names work."""
    # Underscore (Python style)
    config1 = AGFConfig(concurrent_tasks=10, model_type="thinking")
    assert config1.concurrent_tasks == 10
    assert config1.model_type == "thinking"

    # Hyphen (YAML style)
    config2 = AGFConfig(**{"concurrent-tasks": 10, "model-type": "thinking"})
    assert config2.concurrent_tasks == 10
    assert config2.model_type == "thinking"


def test_agf_config_custom_agents():
    """Test AGFConfig with custom agent configurations."""
    config = AGFConfig(
        agents={
            "agent1": AgentModelConfig(
                thinking="t1", standard="s1", light="l1"
            ),
            "agent2": AgentModelConfig(
                thinking="t2", standard="s2", light="l2"
            ),
        }
    )

    assert len(config.agents) == 2
    assert config.agents["agent1"].standard == "s1"
    assert config.agents["agent2"].light == "l2"


def test_agent_model_config_all_fields_required():
    """Test that AgentModelConfig requires all fields."""
    # This should work
    config = AgentModelConfig(thinking="t", standard="s", light="l")
    assert config.thinking == "t"

    # Missing field should raise error
    with pytest.raises(ValidationError):
        AgentModelConfig(thinking="t", standard="s")


def test_agf_config_empty_agents_dict():
    """Test AGFConfig with empty agents dictionary."""
    config = AGFConfig(agents={})

    assert config.agents == {}
    assert config.worktrees == ".worktrees"  # other defaults still work


def test_agf_config_branch_prefix_default():
    """Test that branch_prefix defaults to None."""
    config = AGFConfig.default()

    assert config.branch_prefix is None


def test_agf_config_branch_prefix_hyphen_alias():
    """Test that YAML hyphen alias works for branch_prefix."""
    # Simulating YAML parsing which would use hyphen names
    config = AGFConfig(**{"branch-prefix": "my-team"})

    assert config.branch_prefix == "my-team"


def test_agf_config_branch_prefix_custom_value():
    """Test that custom branch_prefix value is preserved."""
    config = AGFConfig(branch_prefix="team/project")

    assert config.branch_prefix == "team/project"
