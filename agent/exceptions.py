"""Custom exceptions for the agent package."""


class AgentError(Exception):
    """Base exception for all agent errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when the agent CLI is not installed or not found."""

    def __init__(self, agent_name: str, message: str | None = None):
        self.agent_name = agent_name
        msg = message or f"Agent CLI '{agent_name}' not found. Is it installed and in PATH?"
        super().__init__(msg)


class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds the timeout."""

    def __init__(self, agent_name: str, timeout_seconds: int):
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Agent '{agent_name}' execution timed out after {timeout_seconds} seconds"
        )


class AgentExecutionError(AgentError):
    """Raised when the agent returns a non-zero exit code."""

    def __init__(self, agent_name: str, exit_code: int, stderr: str | None = None):
        self.agent_name = agent_name
        self.exit_code = exit_code
        self.stderr = stderr
        msg = f"Agent '{agent_name}' failed with exit code {exit_code}"
        if stderr:
            msg += f": {stderr}"
        super().__init__(msg)


class AgentOutputParseError(AgentError):
    """Raised when agent output cannot be parsed."""

    def __init__(self, agent_name: str, output: str, reason: str | None = None):
        self.agent_name = agent_name
        self.output = output
        self.reason = reason
        msg = f"Failed to parse output from agent '{agent_name}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
