---
name: create-github-pr
description: Create a GitHub pull request with generated description
params:
  - name: agf_id
    description: The unique identifier for this task (e.g., agf-001)
    required: true
---

# Create GitHub PR

Create a GitHub pull request with an auto-generated description based on branch commits.

## Instructions

Extract the `agf_id` parameter to use as a prefix for the PR title.

1. **Generate PR Title**: Create a PR title prefixed with `<agf_id> - ` followed by a descriptive title based on the changes
2. **Generate PR Body**:
   - IF the project contains `.github/PULL_REQUEST_TEMPLATE.md`:
     - Use the template to structure the PR body
     - Fill in sections based on all commits on the current branch that are not in main/master branch
   - ELSE:
     - Generate a brief but precise description
     - Include summary of all commits on the current branch that are not in main/master branch
3. **Verify Clean State**: Use `git status --porcelain` to check for uncommitted changes
   - If any uncommitted changes exist, exit with an error message
4. **Push Changes**: Push all changes to remote branch using `git push --set-upstream origin $(git branch --show-current)`
5. **Create or Display PR**:
   - Check if PR already exists using `gh pr view`
   - IF PR exists: Print "PR already exists"
   - ELSE: Create draft PR using `gh pr create --draft --title "<pr_title>" --body "<pr_body>"`

## Report

Print the result of the `gh pr view` command to display the PR URL and details.

## Example

```
agf_id: agf-001
PR Title: agf-001 - Add user authentication feature
PR URL: https://github.com/owner/repo/pull/123
```
