---
name: tools
description: List all core built-in development tools available
params: []
---

# List Built-in Tools

List all core, built-in non-MCP development tools available to the agent.

## Instructions

This skill takes no parameters. It displays information about available tools.

1. **List Core Tools**: Display all built-in tools available to the agent
2. **Format**: Use bullet format with TypeScript function syntax showing parameters
3. **Categorize**: Group tools by category (File Operations, Search, Code Operations, Git, etc.)
4. **Include Details**: For each tool, show:
   - Tool name
   - Function signature with parameters
   - Brief description of what it does

## Output Format

Display tools in the following format:

```
## File Operations
- read(filePath: string, offset?: number, limit?: number): Read file contents
- write(filePath: string, content: string): Write or overwrite a file
- edit(filePath: string, oldString: string, newString: string, replaceAll?: boolean): Edit file with replacements

## Search Operations
- glob(pattern: string, path?: string): Find files matching pattern
- grep(pattern: string, include?: string, path?: string): Search file contents

## Code Operations
- bash(command: string, description: string, timeout?: number, workdir?: string): Execute shell command

## Task Management
- task(prompt: string, subagent_type: string, description: string, session_id?: string): Launch specialized agent
- todowrite(todos: Todo[]): Update todo list
- todoread(): Read current todo list

## Skills
- skill(name: string): Load a skill with detailed instructions
```

## Example Output

```
Available Built-in Tools:

## File Operations
- read(filePath: string, offset?: number, limit?: number)
  Read file contents with optional offset and limit for large files

- write(filePath: string, content: string)
  Write or overwrite a file (must read first for existing files)

- edit(filePath: string, oldString: string, newString: string, replaceAll?: boolean)
  Perform exact string replacements in files

[Continue with other categories...]
```
