# Return JSON Result from Prompt

## Purpose

When we run agent prompt we often would ask the agent to return a JSON output. We already ask the agents to format their output as JSON. But when we want particular details returned as the result of the prompt we want to extract those details from the text output contained within the JSON aoutput.

Each agent (claude-code or opencode) returns json formatted output differently. We want a unified interface to extract JSON block.

## Workflow

- add an extra field to AgentConfig called `json_output` which is a boolean indicating whether the agent should return JSON output.
- add method to Agent protocol def extract_json_output(self, result: AgentResult) -> Optional[Dict[str, Any]]
- implement extract_json_output for claude-code and opencode agents.
- if AgentResult.success and AgentConfig.json_output:
  - extract the JSON block from the AgentResult.parsed_output.
  - create extra field to AgentResult `json_output` of type Dict[str, Any] and set it with the extracted value.

## Example Outputs by Agent

### Opencode output sample

- read: @agf/agent/sample_sessions/opencode_output.jsonl

the ```json block is contained in one of the jsonl lines. We want our code to handle this particular format.

### Claude Code output sampel

- read: @agf/agent/sample_sessions/claude_code_output.jsonl

the ```json block is contained in result field of the json output.
