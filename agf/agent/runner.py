"""AgentRunner for managing and executing agents."""

from typing import Type

from .base import Agent, AgentConfig, AgentResult
from .claude_code import ClaudeCodeAgent
from .exceptions import AgentError
from .opencode import OpenCodeAgent


class AgentRunner:
    """Factory and facade for creating and running agents."""

    _registry: dict[str, Type[Agent]] = {}

    @classmethod
    def register_agent(cls, agent_class: Type[Agent]) -> None:
        """Register an agent class in the registry."""
        # Create a temporary instance to get the name
        instance = agent_class()
        cls._registry[instance.name] = agent_class

    @classmethod
    def get_agent(cls, name: str) -> Agent:
        """Get an agent instance by name."""
        if name not in cls._registry:
            available = ", ".join(cls._registry.keys()) or "none"
            raise AgentError(
                f"Unknown agent '{name}'. Available agents: {available}"
            )
        return cls._registry[name]()

    @classmethod
    def list_agents(cls) -> list[str]:
        """List all registered agent names."""
        return list(cls._registry.keys())

    @classmethod
    def run(
        cls,
        agent_name: str,
        prompt: str,
        config: AgentConfig | None = None,
    ) -> AgentResult:
        """Run an agent by name with the given prompt."""
        agent = cls.get_agent(agent_name)
        return agent.run(prompt, config)


# Pre-register built-in agents
AgentRunner.register_agent(ClaudeCodeAgent)
AgentRunner.register_agent(OpenCodeAgent)
