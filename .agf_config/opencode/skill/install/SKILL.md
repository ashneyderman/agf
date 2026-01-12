---
name: install
description: Install and prime the project environment
params: []
---

# Install & Prime

Install project dependencies and prime the environment by understanding the codebase.

## Instructions

This skill takes no parameters. It sets up the project environment and primes the agent with codebase knowledge.

1. **Execute Prime Skill**: Use the `prime` skill to understand the codebase structure
2. **Execute Start Skill**: Use the `start` skill to start any necessary services or processes
3. **Report**: Output the work completed in a concise bullet point list

## Workflow

1. Run the `prime` skill to:
   - List all files in the project
   - Read README.md
   - Execute prerequisites validation
   - Run installation commands
   - Execute build commands (if applicable)

2. Run the `start` skill to:
   - Start any required services
   - Verify services are running

## Report Format

After completing the setup:

- List all commands executed
- Note any issues encountered during installation
- Confirm services that were started
- Report any warnings or errors that need attention
