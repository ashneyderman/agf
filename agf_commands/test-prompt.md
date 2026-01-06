# Test Prompt

Create a test commit.

## Variables

agf_id: $1
prompt: $2

## Instructions

- If the <agf_id> or <prompt> is not provided, stop and ask the user to provide them.
- Create a single empty commit with <prompt> as commit message: `git commit --allow-empty -m "$prompt"`
