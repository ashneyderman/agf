---
name: implement
description: Implement a plan from a specification file
params:
  - name: plan
    description: The plan content or path to plan file to implement
    required: true
---

# Implement Plan

Follow the instructions to implement the plan, then report the completed work.

## Instructions

Extract the `plan` parameter which contains either the plan content or path to a plan file.

1. **Read the Plan**: If `plan` is a file path, read the plan file. Otherwise, use the provided plan content
2. **Understand the Plan**: Think hard about the plan requirements, design, and implementation approach
3. **Implement the Plan**: Execute each step in the plan in order
   - Follow the step-by-step tasks outlined in the plan
   - Adhere to existing code patterns and conventions
   - Create or modify files as specified
   - Run validation commands as specified in the plan
4. **Report the Work**: After implementation is complete, provide a summary

## Report Format

After completing the implementation:

- Summarize the work you've just done in a concise bullet point list
- Report the files and total lines changed with `git diff --stat`
- Note any deviations from the plan or important decisions made
- Highlight any issues encountered and how they were resolved

## Example

```
Plan file: specs/agf-001-feature-user-auth.md

Implementation Summary:
- Created user authentication module with login/logout functions
- Added password hashing using bcrypt
- Implemented JWT token generation and validation
- Created unit tests for all auth functions

Files changed:
 src/auth.py        | 145 +++++++++++++++++++++++++++++++
 src/middleware.py  |  32 +++++++
 tests/test_auth.py |  87 ++++++++++++++++++
 3 files changed, 264 insertions(+)
```
