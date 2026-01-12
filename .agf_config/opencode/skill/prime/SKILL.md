---
name: prime
description: Understand the codebase structure and setup the project
params: []
---

# Prime

Execute the following steps to understand the codebase structure, then summarize your understanding.

## Instructions

This skill takes no parameters. It primes the agent with knowledge about the project.

1. **List Project Files**: Run `git ls-files` to see all tracked files in the project
2. **Read README**: Read the `README.md` file in the root of the project
   - If `README.md` is not found, report "README.md not found"
3. **Validate Prerequisites**: 
   - If section `## pre-requisites` or `## prerequisites` exists in README.md:
     - Execute all commands in that section to validate the prerequisites are satisfied
   - Else: Report "section ## pre-requisites not found"
4. **Run Installation**:
   - If section `## installation` exists in README.md:
     - Execute all commands in that section
   - Else: Report "section ## installation not found"
5. **Build Project**:
   - If section `## build` exists in README.md:
     - Execute all commands in that section
   - Else: Report "section ## build not found"

## Summary Format

After completing all steps, provide a summary that includes:

- Project name and description
- Programming language(s) and frameworks used
- Key directories and their purposes
- Build system and tools
- Prerequisites status (all met or issues found)
- Installation status (successful or issues)
- Build status (successful or issues)
- Any important patterns or conventions observed

## Example Output

```
Project: MyApp
Language: Python 3.11
Framework: FastAPI
Structure:
  - src/ - Application source code
  - tests/ - Test files
  - docs/ - Documentation

Prerequisites: ✓ All satisfied (Python 3.11, uv installed)
Installation: ✓ Completed successfully
Build: ✓ No build step required

Key Conventions:
- Uses uv for dependency management
- Tests use pytest framework
- API routes in src/routes/
```
