"""Models for agent prompt templates and execution."""

from typing import Any

from pydantic import BaseModel

from .base import ModelType


class PromptTemplate(BaseModel):
    """Template for structuring agent prompts with metadata and configuration.

    PromptTemplate provides a unified interface for passing prompts to agents,
    encapsulating both the prompt content and execution parameters in a single
    structured object.

    Fields:
        namespace: Organizational namespace for the prompt (default: "agf").
                   Used for categorizing prompts by source or purpose.
        prompt: The actual prompt text to send to the agent (required).
        params: Optional list of parameters for template variable substitution.
                Reserved for future use in prompt templating.
        json_output: Flag indicating whether to extract JSON output from the
                     agent's response (default: False).
        model: Optional model type override (thinking/standard/light).
               If specified, overrides the default model in AgentConfig.

    Example:
        ```python
        from agf.agent.models import PromptTemplate
        from agf.agent.base import ModelType

        # Simple prompt
        template = PromptTemplate(prompt="Explain this code")

        # Prompt with JSON output and specific model
        template = PromptTemplate(
            prompt="Analyze this bug and return JSON",
            json_output=True,
            model=ModelType.THINKING
        )

        # Prompt with namespace and params
        template = PromptTemplate(
            namespace="custom",
            prompt="Process file: {filename}",
            params=["example.py"]
        )
        ```
    """

    namespace: str = "agf"
    prompt: str
    params: list[Any] | None = None
    json_output: bool = False
    model: ModelType | None = None
