"""
Git Worktree Management APIs

This module provides high-level APIs for managing git worktrees programmatically.
Worktrees allow you to have multiple working directories associated with a single
repository, enabling parallel work on different branches.

Example Usage:
    from git_repo import mk_worktree, rm_worktree

    # Create a new worktree at .worktrees/feature-123 with branch 'feature-123'
    mk_worktree(
        project_dir="/path/to/repo",
        target_dir="/path/to/repo/.worktrees/feature-123",
        branch_name="feature-123"
    )

    # Remove the worktree (keeps the branch)
    rm_worktree(
        project_dir="/path/to/repo",
        target_dir="/path/to/repo/.worktrees/feature-123",
        remove_branch=False
    )

    # Remove the worktree and delete its branch
    rm_worktree(
        project_dir="/path/to/repo",
        target_dir="/path/to/repo/.worktrees/feature-123",
        remove_branch=True
    )

References:
    - GitPython Tutorial: https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
    - GitPython API Reference: https://gitpython.readthedocs.io/en/stable/reference.html#api-reference-toplevel
"""

import os
import os.path
from git import Repo


def mk_worktree(project_dir: str, target_dir: str, branch_name: str) -> None:
    """
    Create a new git worktree at the specified target directory with the given branch.

    This function creates a new worktree in two steps:
    1. Creates the worktree without checking out files (--no-checkout)
    2. Explicitly checks out the branch content

    If the branch doesn't exist, it will be created automatically.
    If the parent directory of target_dir doesn't exist, it will be created.

    Args:
        project_dir: Path to the main git repository
        target_dir: Path where the new worktree should be created
        branch_name: Name of the branch to use (created if it doesn't exist)

    Raises:
        ValueError: If project_dir doesn't exist, or if target_dir already exists
        Exception: If git commands fail during worktree creation

    Example:
        >>> mk_worktree(
        ...     project_dir="/path/to/repo",
        ...     target_dir="/path/to/repo/.worktrees/feature",
        ...     branch_name="feature-branch"
        ... )
    """
    # Validate inputs
    if not os.path.exists(project_dir):
        raise ValueError(f"Project directory does not exist: {project_dir}")

    if os.path.exists(target_dir):
        raise ValueError(f"Target directory already exists: {target_dir}")

    # Create parent directory if it doesn't exist
    parent_dir = os.path.dirname(target_dir)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    # Initialize repo and create worktree
    repo = Repo(project_dir)

    # Check if branch exists
    branch_exists = branch_name in [b.name for b in repo.branches]

    # Create worktree without checkout
    if branch_exists:
        # Use existing branch
        repo.git.execute(["git", "worktree", "add", "--no-checkout", target_dir, branch_name])
    else:
        # Create new branch
        repo.git.execute(["git", "worktree", "add", "--no-checkout", "-b", branch_name, target_dir])

    # Initialize repo at worktree location and checkout
    repo1 = Repo(target_dir)
    repo1.git.checkout()


def _get_worktree_branch(project_dir: str, target_dir: str) -> str | None:
    """
    Helper function to extract the branch name associated with a worktree.

    Uses 'git worktree list --porcelain' to get structured worktree information
    and parses it to find the branch associated with the target directory.

    Args:
        project_dir: Path to the main git repository
        target_dir: Path to the worktree

    Returns:
        The branch name associated with the worktree, or None if not found

    Raises:
        Exception: If git commands fail
    """
    repo = Repo(project_dir)
    output = repo.git.execute(["git", "worktree", "list", "--porcelain"])

    # Parse porcelain output
    # Format:
    # worktree /path/to/worktree
    # HEAD abc123...
    # branch refs/heads/branch-name
    # (blank line between worktrees)

    lines = output.strip().split('\n')
    current_worktree = None
    current_branch = None

    # Normalize paths for comparison (use realpath to resolve symlinks)
    target_dir_normalized = os.path.normpath(os.path.realpath(target_dir))

    for line in lines:
        line = line.strip()
        if line.startswith('worktree '):
            # Check if previous worktree matched before moving to next
            if current_worktree == target_dir_normalized and current_branch:
                return current_branch

            worktree_path = line[len('worktree '):].strip()
            current_worktree = os.path.normpath(os.path.realpath(worktree_path))
            current_branch = None
        elif line.startswith('branch '):
            branch_ref = line[len('branch '):].strip()
            # Extract branch name from refs/heads/branch-name
            if branch_ref.startswith('refs/heads/'):
                current_branch = branch_ref[len('refs/heads/'):]

    # Check if the last entry matches
    if current_worktree == target_dir_normalized and current_branch:
        return current_branch

    return None


def rm_worktree(project_dir: str, target_dir: str, remove_branch: bool = False) -> None:
    """
    Remove an existing git worktree and optionally delete its associated branch.

    This function removes the worktree using --force to handle any uncommitted changes.
    If remove_branch is True, it will also delete the branch that was associated with
    the worktree using -D to force deletion regardless of merge status.

    Args:
        project_dir: Path to the main git repository
        target_dir: Path to the worktree to remove
        remove_branch: If True, also delete the branch associated with this worktree (default: False)

    Raises:
        ValueError: If target_dir doesn't exist
        Exception: If git commands fail during worktree removal

    Example:
        >>> # Remove worktree but keep the branch
        >>> rm_worktree(
        ...     project_dir="/path/to/repo",
        ...     target_dir="/path/to/repo/.worktrees/feature"
        ... )
        >>>
        >>> # Remove worktree and delete the branch
        >>> rm_worktree(
        ...     project_dir="/path/to/repo",
        ...     target_dir="/path/to/repo/.worktrees/feature",
        ...     remove_branch=True
        ... )
    """
    # Validate inputs
    if not os.path.exists(target_dir):
        raise ValueError(f"Target directory does not exist: {target_dir}")

    # Extract branch name before removing worktree if we need to delete it
    branch_name = None
    if remove_branch:
        branch_name = _get_worktree_branch(project_dir, target_dir)

    # Initialize repo and remove worktree
    repo = Repo(project_dir)

    # Remove worktree with force to handle uncommitted changes
    repo.git.execute(["git", "worktree", "remove", "--force", target_dir])

    # Remove branch if requested and found
    if remove_branch and branch_name:
        repo.git.execute(["git", "branch", "-D", branch_name])
