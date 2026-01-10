# Create Git Commit

# Purpose

Create git commit for all the uncommitted changes in the repository.

# Instructions

- make sure you refresh your context to see all the changed files.
- generate <commit_message> that summirzes changes to be committed.
- commit the changes with that <commit_message>.
- **DO NOT** indicate co-authoring attributions in the commit.
- Use `git status --porcelain` command to check if there are any uncommitted changes. If there are still changes uncommitted use `git add . ; git commit --amend` command to add those changes.
- save short commit sha in <commit_sha>.

## Output Format

IMPORTANT: Return a JSON array with this structure:

```json
{
  "commit_sha": "<commit_sha>",
  "commit_message": "<commit_message>"
}
```
