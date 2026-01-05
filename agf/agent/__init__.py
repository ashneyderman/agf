"""Agent package for unified AI coding agent invocation."""

__version__ = "0.1.0"

from .base import Agent, AgentConfig, AgentResult
from .claude_code import ClaudeCodeAgent
from .exceptions import (
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentOutputParseError,
    AgentTimeoutError,
)
from .opencode import OpenCodeAgent
from .runner import AgentRunner

__all__ = [
    # Version
    "__version__",
    # Base classes
    "Agent",
    "AgentConfig",
    "AgentResult",
    # Agent implementations
    "ClaudeCodeAgent",
    "OpenCodeAgent",
    # Runner
    "AgentRunner",
    # Exceptions
    "AgentError",
    "AgentExecutionError",
    "AgentNotFoundError",
    "AgentOutputParseError",
    "AgentTimeoutError",
]
