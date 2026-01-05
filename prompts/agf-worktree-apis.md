Create worktree APIs that our orhcestartion script/s can use to manage worktrees.

## Implementation

Create `git_repo.py` module.

Create `def mk_worktree(project_dir, target_dir, branch_name)` method in `git_repo.py`:

- check if project directory exists: if not raise error.
- check if target directory exists, if not create it.
- create worktree with the target directory and if branch does not exist use -b option for branch name when creating worktree. Create worktree with --no-checkout option.
- run checkout command in the new worktree to make repo content availble.

Create `def rm_worktree(project_dir, target_dir, remove_branch=False)` method in `git_repo.py`:

- check if target directory exists: if not raise error.
- use `git worktree remove --force` to remove the worktree.
- if remove_branch = True: remove branch as well.

## Dependencies

Use GitPython library to create these APIs. For documentation see

intro: https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
api reference: https://gitpython.readthedocs.io/en/stable/reference.html#api-reference-toplevel

Here is some relevant python code:

### Example that creates a worktree

```python
    repo = Repo.init(os.path.dirname(project_dir))

    # add new worktree into <worktree_target_dir> and creates new <branch_name> branch
    repo.git.execute(["git", "worktree", "add", "--no-checkout", worktree_target_dir, branch_name])

    # checkout <branch_name> in the new worktree
    repo1 = Repo.init(worktree_target_dir)
    repo1.git.checkout()

    # remove worktree
    repo.git.execute(["git", "worktree", "remove", "--force", worktree_target_dir])
```

### Example: remove a worktree

```python
    repo = Repo.init(os.path.dirname(project_dir))
    repo.git.execute(["git", "worktree", "remove", "--force", worktree_target_dir])
```

### Example: list worktrees

```python
    repo = Repo.init(os.path.dirname(project_dir))
    print(repo.git.execute(["git", "worktree", "list"]))
```
