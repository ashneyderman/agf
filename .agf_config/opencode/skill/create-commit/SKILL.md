---
name: create-commit
description: Create git commit for all uncommitted changes in the repository
params: []
---

# Create Git Commit

Create a git commit for all the uncommitted changes in the repository.

## Instructions

This skill takes no parameters. It commits all uncommitted changes with an appropriate commit message.

1. **Refresh Context**: Review all the changed files using `git status` and `git diff`
2. **Generate Commit Message**: Create a clear, concise commit message that summarizes the changes to be committed
3. **Commit Changes**: Commit the changes with the generated commit message
   - **DO NOT** indicate co-authoring attributions in the commit
4. **Verify Completion**: Use `git status --porcelain` to check if there are any remaining uncommitted changes
   - If there are still uncommitted changes, use `git add . && git commit --amend --no-edit` to add them to the commit
5. **Save Commit SHA**: Extract the short commit SHA from the created commit

## Output Format

IMPORTANT: Return a JSON object with this structure:

```json
{
  "commit_sha": "<short_commit_sha>",
  "commit_message": "<commit_message>"
}
```

### Example Output

```json
{
  "commit_sha": "0acf3cf",
  "commit_message": "feat: add create_github_pr wrapper method with tests"
}
```
