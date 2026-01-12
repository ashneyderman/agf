---
name: build
description: Implement a task directly without creating a plan first
params:
  - name: prompt
    description: The task description to implement
    required: true
---

# Build Task

Implement a task directly without creating a plan first.

## Instructions

Extract the task description from the `prompt` parameter.

1. **Prime with Context**: First, use the prime skill to understand the codebase structure and conventions
2. **Analyze Task**: Carefully read and understand the task description from `prompt`
3. **Implement Solution**: Think hard and then directly implement the solution for the task
4. **Validate Work**: Ensure the implementation is complete and working
5. **Report Results**: Summarize what was done
6. **DO NOT**: Commit your changes (unless explicitly requested in the prompt)

## Setup Phase

Before implementing the task:

- Execute the prime skill to understand the codebase structure
- Read relevant documentation files (README.md, etc.)
- Understand the existing patterns and conventions

## Implementation Guidelines

- Follow existing code patterns and conventions
- Use the libraries and frameworks already in the codebase
- Write clean, maintainable code
- Add appropriate error handling
- Follow security best practices

## Expected Actions

1. **Research**: Understand the codebase and task requirements
2. **Implement**: Make the necessary changes to complete the task
3. **Test**: Verify the implementation works as expected
4. **Report**: Summarize the work completed

## Report Format

After completing the implementation:

- Summarize the work done in clear bullet points
- List all files created or modified
- Report the total lines changed with `git diff --stat`
- Note any important decisions or trade-offs made
- Highlight any follow-up tasks that may be needed
