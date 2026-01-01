"""Base abstractions for the agent package."""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Result from an agent run."""

    success: bool
    output: str
    exit_code: int
    duration_seconds: float
    agent_name: str
    parsed_output: dict | list | None = None
    error: str | None = None


class AgentConfig(BaseModel):
    """Configuration for agent execution."""

    model: str | None = None
    timeout_seconds: int = 300
    working_dir: str | None = None
    output_format: str = "json"
    extra_args: list[str] = Field(default_factory=list)

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
        """Execute the agent with the given prompt and configuration."""
        ...
