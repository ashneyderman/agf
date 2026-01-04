# Initialize Worktree with Sparse Checkout

Create a new git worktree for an agent to work in isolation.

## Variables

branch: $1

## Instructions

0. Set <worktree_dir> to the value of <branch> where symbols / and \ are replaced with symbol -
1. Create a new git worktree in the `.worktrees/<worktree_dir>` directory with sparse checkout
2. Base the worktree on the current branch
3. Copy the `.env` file from the root directory to the worktree (if it exists)
4. Report the successful creation of the worktree

## Git Worktree Setup with Sparse Checkout

Execute these steps in order:

1. **Create the trees directory** if it doesn't exist:

   ```bash
   mkdir -p .worktrees
   ```

2. **Check if worktree already exists**:
   - If `.worktrees/<worktree_dir>` already exists, report that it exists and stop
   - Otherwise, proceed with creation

3. **Create the git worktree without checkout**:

   ```bash
   git worktree add --no-checkout .worktrees/<worktree_dir> -b <branch>
   ```

4. **Change directory to the worktree**:

   ```bash
   cd .worktrees/<worktree_dir>
   ```

5. **Checkout files**

   ```bash
   # Now checkout the files
   git checkout
   ```

6. **Copy environment file** (if exists):
   Copy the .env from the root directory into `.worktrees/<worktree_dir>/.env`

## Error Handling

- If the worktree already exists, report this and exit gracefully
- If git worktree creation fails, report the error
- If .env doesn't exist in root or target directory, continue without error (it's optional)

## Verification

After setup, verify the checkout is working:

```bash
ls -la  # Should contain project's files (plus .git)
```

## Report

Report one of the following:

- Success: "Worktree '<branch>' created successfully at .worktrees/<worktree_dir>"
- Already exists: "Worktree '<branch>' already exists at .worktrees/<worktree_dir>"
- Error: "Failed to create worktree: <error message>"

## Notes

- Git worktrees with sparse checkout provide double isolation:
  - **Worktree isolation**: Separate branch and working directory
- This reduces clutter and prevents accidental modifications to other apps
- The agent only sees and works with `.worktrees/<worktree_dir>`
- Full repository history is still available but only the specified directory is in the working tree
- Each worktree maintains its own sparse-checkout configuration
