# Create Git Commit

# Purpose

Create git commit for all the uncommitted changes in the repository.

# Instructions

- make sure you refresh your context to see all the changed files.
- generate <commit_message> that summirzes changes to be committed.
- commit the changes with that <commit_message>.
- save short commit sha in <commit_sha>.
- **DO NOT** indicate co-authoring attributions in the commit.

## Output Format

IMPORTANT: Return a JSON array with this structure:

```json
{
  "commit_sha": "<commit_sha>",
  "commit_message": "<commit_message>"
}
```
