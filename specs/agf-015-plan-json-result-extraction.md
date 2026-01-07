# Plan: JSON Result Extraction from Agent Prompts

## Metadata

agf_id: `agf-015`
prompt: `@prompts/agf-return-json-result-from-prompt.md`
task_type: enhancement
complexity: medium

## Task Description

When running agent prompts, we often ask agents to return JSON output. While agents already format their output as JSON, we need to extract specific JSON blocks from the text content within the structured output. Each agent (claude-code and opencode) returns JSON formatted output differently, and we need a unified interface to extract JSON blocks from their responses.

## Objective

Create a unified interface for extracting JSON blocks from agent outputs by:
1. Adding a `json_output` boolean flag to AgentConfig to indicate when JSON extraction is needed
2. Adding an `extract_json_output` method to the Agent protocol for parsing JSON from results
3. Implementing JSON extraction for both claude-code and opencode agents, handling their different output formats
4. Adding a `json_output` field to AgentResult to store the extracted JSON data

## Problem Statement

Currently, when agents return JSON output, it is embedded within their structured responses (JSONL for opencode, JSON for claude-code). There is no standardized way to extract the actual JSON data that the agent produces in response to prompts. This makes it difficult to programmatically consume agent-generated JSON data.

## Solution Approach

Implement a protocol-based extraction system where:
- Each agent implementation knows how to parse its own output format
- ClaudeCodeAgent extracts JSON blocks from the "result" field
- OpenCodeAgent extracts JSON blocks from text events in JSONL output
- The extraction happens automatically when `AgentConfig.json_output=True`
- Extracted JSON is stored in `AgentResult.json_output` for easy access

## Relevant Files

- **agf/agent/base.py** - Contains AgentConfig, AgentResult, and Agent protocol. Need to add json_output field to AgentConfig and AgentResult, and extract_json_output method to Agent protocol.
- **agf/agent/claude_code.py** - ClaudeCodeAgent implementation. Need to implement extract_json_output method to parse JSON from the "result" field.
- **agf/agent/opencode.py** - OpenCodeAgent implementation. Need to implement extract_json_output method to parse JSON from JSONL text events.
- **agf/agent/runner.py** - AgentRunner that executes agents. May need to update to call extract_json_output when json_output=True.
- **agf/agent/sample_sessions/opencode_output.jsonl** - Sample opencode output showing JSONL format with JSON blocks in text events.
- **agf/agent/sample_sessions/claude_code_output.json** - Sample claude-code output showing JSON format with result field containing JSON blocks.

### New Files

- **tests/agent/test_json_extraction.py** - Unit tests for JSON extraction functionality across both agent types.

## Implementation Phases

### Phase 1: Foundation

Update the base agent models and protocol to support JSON extraction:
- Add JSONValue type alias to represent any valid JSON value (dict, list, str, int, float, bool, or None)
- Add `json_output: bool = False` field to AgentConfig
- Add `json_output: JSONValue = None` field to AgentResult to support all JSON types
- Add `extract_json_output(self, result: AgentResult) -> JSONValue` method to Agent protocol

### Phase 2: Core Implementation

Implement JSON extraction for each agent type:
- Implement extract_json_output in ClaudeCodeAgent to parse JSON from result field
- Implement extract_json_output in OpenCodeAgent to parse JSON from JSONL text events
- Update agent run methods to call extract_json_output when config.json_output=True

### Phase 3: Integration & Testing

Integrate JSON extraction into the execution flow and validate:
- Add comprehensive unit tests for both agent implementations
- Test with sample session outputs
- Validate error handling for malformed JSON
- Document the new functionality

## Step by Step Tasks

### 1. Add JSONValue type alias and update models

- Add JSONValue type alias to agf/agent/base.py to represent any valid JSON value
- Add `json_output: bool = False` field to AgentConfig class in agf/agent/base.py:162-180
- Add `json_output: JSONValue = None` field to AgentResult class in agf/agent/base.py:150-160

### 2. Update Agent protocol

- Add `extract_json_output(self, result: AgentResult) -> JSONValue` method signature to Agent protocol in agf/agent/base.py:182-193

### 3. Implement JSON extraction for ClaudeCodeAgent

- Add `extract_json_output` method to ClaudeCodeAgent class in agf/agent/claude_code.py
- Extract JSON blocks from the "result" field of parsed_output
- Handle cases where result field doesn't exist or doesn't contain valid JSON
- Look for ```json code blocks and parse the content within them

### 4. Implement JSON extraction for OpenCodeAgent

- Add `extract_json_output` method to OpenCodeAgent class in agf/agent/opencode.py
- Parse JSONL events to find text-type events
- Extract JSON blocks from text content (look for ```json code blocks)
- Handle cases where no JSON blocks are found

### 5. Integrate extraction into agent run methods

- Update ClaudeCodeAgent.run method to call extract_json_output when config.json_output=True and result.success=True
- Update OpenCodeAgent.run method to call extract_json_output when config.json_output=True and result.success=True
- Set the json_output field on AgentResult with extracted data

### 6. Create comprehensive tests

- Create tests/agent/test_json_extraction.py
- Test ClaudeCodeAgent JSON extraction with sample output
- Test OpenCodeAgent JSON extraction with sample output
- Test error handling for missing JSON blocks
- Test error handling for malformed JSON
- Test that extraction only happens when json_output=True

### 7. Validate implementation

- Run all tests to ensure functionality works correctly
- Test with actual agent executions if possible
- Verify that existing functionality is not broken

## Testing Strategy

**Unit Tests:**
- Test AgentConfig with json_output flag
- Test AgentResult with json_output field
- Test ClaudeCodeAgent.extract_json_output with various input formats:
  - Valid JSON in result field
  - Missing result field
  - Result field without JSON blocks
  - Malformed JSON blocks
- Test OpenCodeAgent.extract_json_output with various JSONL formats:
  - Valid JSON in text events
  - No text events
  - Text events without JSON blocks
  - Malformed JSON blocks
- Test integration: verify json_output is set correctly when config.json_output=True

**Edge Cases:**
- Empty or None parsed_output
- Multiple JSON blocks in output (should extract first one)
- JSON blocks with escaped characters
- Very large JSON blocks
- JSON values of different types: objects (dict), arrays (list), strings, numbers, booleans, null

## Acceptance Criteria

1. AgentConfig has a `json_output` boolean field that defaults to False
2. AgentResult has a `json_output` field (JSONValue type) that can hold any valid JSON value
3. Agent protocol defines an `extract_json_output` method returning JSONValue
4. ClaudeCodeAgent successfully extracts JSON of all types from sample outputs
5. OpenCodeAgent successfully extracts JSON of all types from sample outputs
6. JSON extraction only occurs when AgentConfig.json_output=True and AgentResult.success=True
7. All unit tests pass, including tests for different JSON value types
8. Existing agent functionality remains unchanged when json_output=False

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m pytest tests/agent/test_json_extraction.py -v` - Run JSON extraction tests
- `uv run python -m pytest tests/agent/ -v` - Run all agent tests to ensure no regressions
- `uv run python -m py_compile agf/agent/*.py` - Verify all agent files compile without errors
- `uv run python -m mypy agf/agent/base.py agf/agent/claude_code.py agf/agent/opencode.py --strict` - Type check the implementations (if mypy is available)

## Notes

- JSON extraction should use regex to find ```json code blocks in text output
- The pattern should handle both \`\`\`json and \`\`\`JSON (case insensitive)
- Only the first JSON block should be extracted if multiple are present
- Error handling should be graceful - return None if JSON cannot be extracted rather than raising exceptions
- The sample output files should be used as fixtures in tests
- Consider adding a utility function for extracting JSON blocks from markdown-formatted text since both agents may need it
- JSONValue type should support all valid JSON types: objects (dict), arrays (list), strings, numbers (int, float), booleans, and null (None)
