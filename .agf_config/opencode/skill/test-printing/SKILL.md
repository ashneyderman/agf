---
name: test-printing
description: Simple skill that prints a templated message with agf_id and prompt
license: MIT
compatibility: opencode
---

## What I do

- Accept two parameters: agf_id and prompt
- Format them into a JSON message
- Return the formatted output

## Instructions

When this skill is loaded, follow these steps:

1. Extract the agf_id parameter (first argument)
2. Extract the prompt parameter (second argument)
3. Create an output message with format: "test printing: {agf_id} - {prompt}"
4. Return a JSON object with this exact structure:

```json
{
  "message": "test printing: {agf_id} - {prompt}"
}
```

## Example Usage

If called with agf_id="agf-001" and prompt="test prompt", return:

```json
{
  "message": "test printing: agf-001 - test prompt"
}
```
