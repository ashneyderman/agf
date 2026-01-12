---
name: chore
description: Create a plan to complete a chore task
params:
  - name: agf_id
    description: The unique identifier for this task (e.g., agf-001)
    required: true
  - name: prompt
    description: The chore description to plan
    required: true
---

# Chore Planning

Create a plan to complete the chore using the specified markdown Plan Format. Research the codebase and create a thorough plan.

## Instructions

Extract parameters:
- `agf_id` - The unique task identifier
- `prompt` - The chore description

1. If the `agf_id` or `prompt` is not provided, stop and ask the user to provide them
2. Create a plan to complete the chore described in the `prompt`
3. The plan should be simple, thorough, and precise
4. Create the plan in the `specs/` directory with filename: `<agf_id>-chore-<descriptive_name>.md`
   - Replace `<descriptive_name>` with a short, descriptive name based on the `prompt` itself (e.g., "update-readme", "add-logging", "refactor-agent")
5. Research the codebase starting with `README.md`
6. Replace every `<placeholder>` in the Plan Format below with the requested value

## Codebase Structure

- Read: `README.md` for project overview and instructions (start here) to understand the project structure and guidelines

## Plan Format

```md
# Chore: <chore name>

## Metadata

agf_id: `<agf_id>`
prompt: `<prompt>`

## Chore Description

<describe the chore in detail based on the prompt>

## Relevant Files

Use these files to complete the chore:

<list files relevant to the chore with bullet points explaining why. Include new files to be created under an h3 'New Files' section if needed>

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers with bullet points. Start with foundational changes then move to specific changes. Last step should validate the work>

### 1. <First Task Name>

- <specific action>
- <specific action>

### 2. <Second Task Name>

- <specific action>
- <specific action>

## Validation Commands

Execute these commands to validate the chore is complete:

<list specific commands to validate the work. Be precise about what to run. Include command that runs all the tests.>
- Example: `uv run python -m py_compile apps/*.py` - Test to ensure the code compiles

## Notes

<optional additional context or considerations>
```

## Output Format

IMPORTANT: Return a JSON object with this structure:

```json
{
  "path": "specs/<agf_id>-chore-<descriptive_name>.md"
}
```

### Example Output

```json
{
  "path": "specs/agf-001-chore-update-readme.md"
}
```
