---
name: plan
description: Create a general plan for any type of task
params:
  - name: agf_id
    description: The unique identifier for this task (e.g., agf-001)
    required: true
  - name: prompt
    description: The task description to plan
    required: true
---

# General Planning

Create a plan to complete the task using the specified markdown Plan Format. Research the codebase and create a thorough plan appropriate to the task's complexity.

## Instructions

Extract parameters:
- `agf_id` - The unique task identifier
- `prompt` - The task description

1. If `agf_id` or `prompt` is not provided, stop and ask the user to provide them
2. IMPORTANT: Create a plan to complete the task described in the `prompt`
3. The plan should be appropriately detailed based on the task complexity:
   - Simple tasks (chores, fixes): Focus on specific changes and validation
   - Complex tasks (features, refactors): Include design, phases, and testing strategy
4. Create the plan in the `specs/` directory with filename: `<agf_id>-plan-<descriptive_name>.md`
   - Replace `<descriptive_name>` with a short, descriptive name based on the `prompt` itself (e.g., "update-readme", "add-logging", "implement-api", "refactor-agent")
5. Research the codebase starting with `README.md`
6. IMPORTANT: Replace every `<placeholder>` in the Plan Format with the requested value
7. Use your reasoning model: THINK HARD about the task requirements and appropriate level of planning needed
8. Follow existing patterns and conventions in the codebase

## Codebase Structure

- Read: `README.md` for project overview and instructions (start here) to understand the project structure and guidelines

## Plan Format

```md
# Plan: <task name>

## Metadata

agf_id: `<agf_id>`
prompt: `<prompt>`
task_type: <chore|feature|refactor|fix|enhancement>
complexity: <simple|medium|complex>

## Task Description

<describe the task in detail based on the prompt>

## Objective

<clearly state what will be accomplished when this plan is complete>

<if task_type is feature or complexity is medium/complex, include these sections:>

## Problem Statement

<clearly define the specific problem or opportunity this task addresses>

## Solution Approach

<describe the proposed solution approach and how it addresses the objective>
</if>

## Relevant Files

Use these files to complete the task:

<list files relevant to the task with bullet points explaining why. Include new files to be created under an h3 'New Files' section if needed>

<if complexity is medium/complex, include this section:>

## Implementation Phases

### Phase 1: Foundation

<describe any foundational work needed>

### Phase 2: Core Implementation

<describe the main implementation work>

### Phase 3: Integration & Polish

<describe integration, testing, and final touches>
</if>

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers with bullet points. Start with foundational changes then move to specific changes. Last step should validate the work>

### 1. <First Task Name>

- <specific action>
- <specific action>

### 2. <Second Task Name>

- <specific action>
- <specific action>

<continue with additional tasks as needed>

<if task_type is feature or complexity is medium/complex, include this section:>

## Testing Strategy

<describe testing approach, including unit tests and edge cases as applicable>
</if>

## Acceptance Criteria

<list specific, measurable criteria that must be met for the task to be considered complete>

## Validation Commands

Execute these commands to validate the task is complete:

<list specific commands to validate the work. Be precise about what to run. Include command that runs all the tests.>
- Example: `uv run python -m py_compile apps/*.py` - Test to ensure the code compiles

## Notes

<optional additional context, considerations, or dependencies. If new libraries are needed, specify using `uv add`>
```

## Output Format

IMPORTANT: Return a JSON object with this structure:

```json
{
  "path": "specs/<agf_id>-plan-<descriptive_name>.md"
}
```

### Example Output

```json
{
  "path": "specs/agf-001-plan-refactor-api.md"
}
```
