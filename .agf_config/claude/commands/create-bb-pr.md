# Create Bitbucket PR

# Purpose

Custom command that creates a PR description and calls bitbucket CLI to create the PR on bitbucket. 

# Variables

agf_id: $1

# Workflow

- Generate <pr_title> prefixed with "<agf_id> - "
- IF project contains `.bitbucket/PULL_REQUEST_TEMPLATE.md`:
  - generate <pr_body>: using `.bitbucket/PULL_REQUEST_TEMPLATE.md` as a template.
  - take into consideration all the commits on the current branch that are not in main/master branch.

  ELSE:
  - generate <pr_body>: brief but precise description.
  - take into consideration all the commits on the current branch that are not in main/master branch.

- verify no uncommitted changes are pending on current branch. Use `git status --porcelain` command, if you find any uncommitted changes exit with error.

- push all changes to remote branch: `git push --set-upstream origin $(git_current_branch)`
- create PR using `bkt pr create --title <pr_title> --body <pr_body> --format json`.

# Report

Print the result of `bkt pr create` command.
