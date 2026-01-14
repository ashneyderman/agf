# Create Github PR

# Purpose

Custom command that creates a PR description and calls github CLI to create the PR on github.

# Variables

agf_id: $1

# Workflow

- Generate <pr_title> prefixed with "<agf_id> - "
- IF project contains `.github/PULL_REQUEST_TEMPLATE.md`:
  - generate <pr_body>: using `.github/PULL_REQUEST_TEMPLATE.md` as a template.
  - take into consideration all the commits on the current branch that are not in main/master branch.

  ELSE:
  - generate <pr_body>: brief but precise description.
  - take into consideration all the commits on the current branch that are not in main/master branch.

- verify no uncommitted changes are pending on current branch. Use `git status --porcelain` command, if you find any uncommitted changes exit with error.

- push all changes to remote branch: `git push --set-upstream origin $(git_current_branch)`
- IF PR already exists (check using `gh pr view`): print "PR already exists"
  ELSE: create draft PR using `gh pr create --draft --title <pr_title> --body <pr_body>`.

# Report

Print the result of `gh pr view` command.
