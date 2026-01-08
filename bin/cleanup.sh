git worktree list --porcelain | grep -E '^worktree ' | awk '{print $2}' | grep '/.worktrees/' | xargs -I {} git worktree remove --force {}
git branch | grep 'alex/' | sed 's/^[* ]*//' | xargs -r git branch -D
