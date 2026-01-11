"""Base abstractions for the agent package."""

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .models import CommandTemplate

# Type alias for JSON values - any valid JSON type
JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class AgentType(str, Enum):
    """Enumeration of available agent types."""

    CLAUDE_CODE = "claude-code"
    OPENCODE = "opencode"

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all agent type values."""
        return [member.value for member in cls]

    @classmethod
    def default(cls) -> str:
        """Return the default agent type value."""
        return cls.CLAUDE_CODE.value


class ModelType(str, Enum):
    """Enumeration of available model types."""

    THINKING = "thinking"
    STANDARD = "standard"
    LIGHT = "light"

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all model type values."""
        return [member.value for member in cls]

    @classmethod
    def default(cls) -> str:
        """Return the default model type value."""
        return cls.STANDARD.value


class ModelMapping:
    """Maps abstract model types to concrete model names for each agent.

    This class provides a centralized way to map model types (thinking, standard, light)
    to the actual model identifiers expected by each agent CLI.

    Example:
        >>> ModelMapping.get_model("claude-code", "thinking")
        "opus-4.5"
        >>> ModelMapping.get_model("opencode", "standard")
        "github-copilot/claude-sonnet-4.5"
    """

    _mappings: dict[str, dict[str, str]] = {
        "claude-code": {
            "thinking": "opus",
            "standard": "sonnet",
            "light": "haiku",
        },
        "opencode": {
            "thinking": "github-copilot/claude-opus-4.5",
            "standard": "github-copilot/claude-sonnet-4.5",
            "light": "github-copilot/claude-haiku-4.5",
        },
    }

    @classmethod
    def get_model(cls, agent_name: str, model_type: str) -> str | None:
        """Get the concrete model name for an agent and model type.

        Args:
            agent_name: The agent identifier (e.g., "claude-code", "opencode")
            model_type: The abstract model type (e.g., "thinking", "standard", "light")

        Returns:
            The concrete model name, or None if no mapping exists.
        """
        agent_models = cls._mappings.get(agent_name)
        if agent_models is None:
            return None
        return agent_models.get(model_type)

    @classmethod
    def register_agent(cls, agent_name: str, models: dict[str, str]) -> None:
        """Register model mappings for a new agent.

        Args:
            agent_name: The agent identifier
            models: A dict mapping model types to concrete model names
        """
        cls._mappings[agent_name] = models

    @classmethod
    def update_model(cls, agent_name: str, model_type: str, model_name: str) -> None:
        """Update a specific model mapping for an agent.

        Args:
            agent_name: The agent identifier
            model_type: The abstract model type
            model_name: The new concrete model name
        """
        if agent_name not in cls._mappings:
            cls._mappings[agent_name] = {}
        cls._mappings[agent_name][model_type] = model_name

    @classmethod
    def list_agents(cls) -> list[str]:
        """List all agents with registered model mappings."""
        return list(cls._mappings.keys())

    @classmethod
    def list_models(cls, agent_name: str) -> dict[str, str] | None:
        """List all model mappings for an agent."""
        return cls._mappings.get(agent_name)

    @classmethod
    def from_agf_config(cls, config: "AGFConfig") -> None:
        """Register agents from AGFConfig.

        Updates the global ModelMapping registry with agent configurations
        from the provided AGFConfig. This allows dynamic agent registration
        from configuration files.

        Args:
            config: AGFConfig instance containing agent model mappings

        Example:
            >>> from agf.config import AGFConfig
            >>> config = AGFConfig.default()
            >>> ModelMapping.from_agf_config(config)
            >>> ModelMapping.list_agents()
            ['claude-code', 'opencode']
        """

        for agent_name, agent_config in config.agents.items():
            cls.register_agent(
                agent_name,
                {
                    "thinking": agent_config.thinking,
                    "standard": agent_config.standard,
                    "light": agent_config.light,
                },
            )


class AgentResult(BaseModel):
    """Result from an agent run."""

    success: bool
    output: str
    exit_code: int
    duration_seconds: float
    agent_name: str
    parsed_output: dict | list | None = None
    error: str | None = None
    json_output: JSONValue = None


class AgentConfig(BaseModel):
    """Configuration for agent execution."""

    model: str | None = None
    timeout_seconds: int = 3600
    working_dir: str | None = None
    output_format: str = "json"
    extra_args: list[str] = Field(default_factory=list)
    json_output: bool = False

    # Logger function to log the CLI command before execution.
    # If None, no logging is performed. The logger receives the fully
    # assembled CLI command as a string for debugging/auditing purposes.
    logger: Callable[[str], None] | None = None

    # Claude Code specific options
    skip_permissions: bool = False
    max_turns: int | None = None
    tools: list[str] | None = None
    append_system_prompt: str | None = None

    # OpenCode specific options
    opencode_agent: str | None = None
    files: list[str] | None = None


@runtime_checkable
class Agent(Protocol):
    """Protocol defining the interface for all agents."""

    @property
    def name(self) -> str:
        """Return the agent identifier."""
        ...

    def run(self, prompt: str, config: AgentConfig | None = None) -> AgentResult:
        """Execute the agent with the given prompt and configuration.

        Deprecated: Use run_command() instead for structured prompt execution.
        """
        ...

    def run_command(
        self, command_template: "CommandTemplate", config: AgentConfig | None = None
    ) -> AgentResult:
        """Execute the agent with a structured command template.

        This method provides a unified interface for command execution, supporting
        namespace organization, parameter templating, JSON output extraction,
        and per-prompt model selection.

        Args:
            command_template: Structured command with metadata and configuration
            config: Optional execution configuration (timeout, working dir, etc.)

        Returns:
            AgentResult containing the execution outcome and any extracted data
        """
        ...

    def extract_json_output(self, result: AgentResult) -> JSONValue:
        """Extract JSON output from agent result.

        Args:
            result: The agent result containing output to parse

        Returns:
            Extracted JSON value (can be dict, list, str, int, float, bool, or None)
        """
        ...
