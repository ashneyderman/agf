# Clean Worktree

Remove a git worktree and its associated branch.

## Variables

worktree_name: $ARGUMENT

## Instructions

1. Check if the worktree exists
2. Remove the worktree if it exists
3. Prune worktree references
4. Report the results

## Cleanup Steps

Execute these steps in order:

0. Set <worktree_dir> to the value of <worktree_name> where symbols / and \ are replaced with symbol -

1. **Check worktree status**:

   ```bash
   git worktree list
   ```

2. **Remove the worktree** (if exists):

   ```bash
   git worktree remove .worktrees/<worktree_dir> --force
   ```

   - Use `--force` to remove even if there are uncommitted changes
   - This removes the worktree directory and its contents

3. **Prune worktree references**:

   ```bash
   git worktree prune
   ```

   - Cleans up any stale worktree references

4. **Verify cleanup**:

   ```bash
   # Verify worktree is gone
   git worktree list | grep <worktree_name>
   ```

## Error Handling

- If worktree doesn't exist, report and continue with branch cleanup
- If removal fails due to permissions, report the error
- Always run `git worktree prune` regardless of other steps

## Expected Output

Report one of the following:

- Success: "Worktree '<worktree_name>' cleaned up successfully"
- Already clean: "Worktree '<worktree_name>' does not exist"
- Error: "Failed to clean worktree: <error message>"

## Safety Checks

Before removing:

- List any uncommitted changes in the worktree
- Show any unpushed commits on the branch
- Confirm the worktree path is correct (.worktrees/<worktree_name>)

## Notes

- This operation is destructive and cannot be undone
- All uncommitted work in the worktree will be lost
- Use this after tasks are completed or to clean up failed attempts
