Create worktree objects wtih worktree_id. It will be provided on the line that creates the worktree.

For example:

```markdown
## Git Worktree feature-auth {SCHIP-7899}
```

indicates worktree_id inside `{}`, so in the example abobe worktree_id="SCHIP-7899"

When worktree id is not provided, we will use default value of None.

Make sure to adjust all the existing tests that deal with worktree models.
