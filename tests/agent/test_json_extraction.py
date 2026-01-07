"""Tests for JSON extraction functionality in agents."""

import json
from pathlib import Path

import pytest

from agf.agent.base import AgentConfig, AgentResult
from agf.agent.claude_code import ClaudeCodeAgent
from agf.agent.opencode import OpenCodeAgent


class TestClaudeCodeJSONExtraction:
    """Tests for ClaudeCodeAgent JSON extraction."""

    def test_extract_json_from_result_field(self):
        """Test extracting JSON from Claude Code result field."""
        agent = ClaudeCodeAgent()

        # Sample parsed output with JSON block in result field
        parsed_output = {
            "result": """Based on my analysis, here are the results:

```json
{
  "summary": "Test summary",
  "count": 42,
  "items": ["a", "b", "c"]
}
```

This shows the data.""",
            "session_id": "test-123",
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert extracted["summary"] == "Test summary"
        assert extracted["count"] == 42
        assert extracted["items"] == ["a", "b", "c"]

    def test_extract_json_case_insensitive(self):
        """Test JSON extraction is case insensitive for code fence."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the output:

```JSON
{"value": 123}
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert extracted["value"] == 123

    def test_extract_json_missing_result_field(self):
        """Test extraction returns None when result field is missing."""
        agent = ClaudeCodeAgent()

        parsed_output = {"session_id": "test-123"}

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_no_json_block(self):
        """Test extraction returns None when no JSON block is present."""
        agent = ClaudeCodeAgent()

        parsed_output = {"result": "Just some plain text without JSON blocks"}

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_malformed_json(self):
        """Test extraction returns None for malformed JSON."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the output:

```json
{invalid json: no quotes}
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_none_parsed_output(self):
        """Test extraction returns None when parsed_output is None."""
        agent = ClaudeCodeAgent()

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=None,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_first_block_only(self):
        """Test that only the first JSON block is extracted."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """First result:

```json
{"first": true}
```

Second result:

```json
{"second": true}
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert extracted["first"] is True
        assert "second" not in extracted

    def test_extract_json_array_type(self):
        """Test extracting JSON array."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the array:

```json
[1, 2, 3, "four", true]
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert isinstance(extracted, list)
        assert extracted == [1, 2, 3, "four", True]

    def test_extract_json_string_type(self):
        """Test extracting JSON string."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the string:

```json
"hello world"
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted == "hello world"

    def test_extract_json_number_type(self):
        """Test extracting JSON number."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the number:

```json
42
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted == 42

    def test_extract_json_boolean_type(self):
        """Test extracting JSON boolean."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is the boolean:

```json
true
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is True

    def test_extract_json_null_type(self):
        """Test extracting JSON null."""
        agent = ClaudeCodeAgent()

        parsed_output = {
            "result": """Here is null:

```json
null
```
"""
        }

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None


class TestOpenCodeJSONExtraction:
    """Tests for OpenCodeAgent JSON extraction."""

    def test_extract_json_from_text_event(self):
        """Test extracting JSON from OpenCode text event."""
        agent = OpenCodeAgent()

        # Sample JSONL events with JSON block in text event
        parsed_output = [
            {"type": "step_start", "timestamp": 123},
            {
                "type": "text",
                "part": {
                    "text": """I'll analyze the tasks:

```json
[
  {
    "worktree_name": "feature-auth",
    "tasks_to_start": [{"description": "Add auth", "tags": ["security"]}]
  }
]
```

These are the eligible tasks."""
                },
            },
            {"type": "step_finish", "timestamp": 456},
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert isinstance(extracted, list)
        assert len(extracted) == 1
        assert extracted[0]["worktree_name"] == "feature-auth"

    def test_extract_json_case_insensitive(self):
        """Test JSON extraction is case insensitive for code fence."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Result:

```JSON
{"value": 999}
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert extracted["value"] == 999

    def test_extract_json_no_text_events(self):
        """Test extraction returns None when no text events exist."""
        agent = OpenCodeAgent()

        parsed_output = [
            {"type": "step_start", "timestamp": 123},
            {"type": "step_finish", "timestamp": 456},
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_no_json_block(self):
        """Test extraction returns None when no JSON block in text."""
        agent = OpenCodeAgent()

        parsed_output = [
            {"type": "text", "part": {"text": "Just plain text without JSON"}}
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_malformed_json(self):
        """Test extraction returns None for malformed JSON."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Result:

```json
{bad json here}
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_none_parsed_output(self):
        """Test extraction returns None when parsed_output is None."""
        agent = OpenCodeAgent()

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=None,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None

    def test_extract_json_first_match_only(self):
        """Test that only the first JSON block is extracted."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """First:

```json
{"first": 1}
```
"""
                },
            },
            {
                "type": "text",
                "part": {
                    "text": """Second:

```json
{"second": 2}
```
"""
                },
            },
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert extracted["first"] == 1
        assert "second" not in extracted

    def test_extract_json_array_type(self):
        """Test extracting JSON array."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Array result:

```json
["apple", "banana", "cherry"]
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is not None
        assert isinstance(extracted, list)
        assert extracted == ["apple", "banana", "cherry"]

    def test_extract_json_string_type(self):
        """Test extracting JSON string."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """String result:

```json
"test string"
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted == "test string"

    def test_extract_json_number_type(self):
        """Test extracting JSON number."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Number result:

```json
3.14
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted == 3.14

    def test_extract_json_boolean_type(self):
        """Test extracting JSON boolean."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Boolean result:

```json
false
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is False

    def test_extract_json_null_type(self):
        """Test extracting JSON null."""
        agent = OpenCodeAgent()

        parsed_output = [
            {
                "type": "text",
                "part": {
                    "text": """Null result:

```json
null
```
"""
                },
            }
        ]

        result = AgentResult(
            success=True,
            output="raw output",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
            parsed_output=parsed_output,
        )

        extracted = agent.extract_json_output(result)

        assert extracted is None


class TestAgentConfigJSONOutput:
    """Tests for AgentConfig json_output field."""

    def test_json_output_defaults_to_false(self):
        """Test that json_output defaults to False."""
        config = AgentConfig()
        assert config.json_output is False

    def test_json_output_can_be_set(self):
        """Test that json_output can be set to True."""
        config = AgentConfig(json_output=True)
        assert config.json_output is True


class TestAgentResultJSONOutput:
    """Tests for AgentResult json_output field."""

    def test_json_output_defaults_to_none(self):
        """Test that json_output defaults to None."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
        )
        assert result.json_output is None

    def test_json_output_can_be_dict(self):
        """Test that json_output can hold a dict."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
            json_output={"key": "value"},
        )
        assert result.json_output == {"key": "value"}

    def test_json_output_can_be_list(self):
        """Test that json_output can hold a list."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
            json_output=[1, 2, 3],
        )
        assert result.json_output == [1, 2, 3]

    def test_json_output_can_be_string(self):
        """Test that json_output can hold a string."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
            json_output="test string",
        )
        assert result.json_output == "test string"

    def test_json_output_can_be_number(self):
        """Test that json_output can hold a number."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
            json_output=42,
        )
        assert result.json_output == 42

    def test_json_output_can_be_boolean(self):
        """Test that json_output can hold a boolean."""
        result = AgentResult(
            success=True,
            output="test",
            exit_code=0,
            duration_seconds=1.0,
            agent_name="test",
            json_output=True,
        )
        assert result.json_output is True
