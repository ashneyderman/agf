"""
Comprehensive tests for git_repo module.

Tests cover both normal operations and edge cases for worktree management.
"""

import os
import shutil
import tempfile
import pytest
from git import Repo

from git_repo import mk_worktree, rm_worktree, _get_worktree_branch


@pytest.fixture
def temp_git_repo():
    """
    Create a temporary git repository for testing.

    Yields the path to the temporary repository and cleans up after the test.
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, "test_repo")
    os.makedirs(repo_path)

    # Initialize git repo
    repo = Repo.init(repo_path)

    # Create initial commit (required for worktrees)
    test_file = os.path.join(repo_path, "README.md")
    with open(test_file, "w") as f:
        f.write("# Test Repository\n")

    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    yield repo_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def worktrees_dir(temp_git_repo):
    """
    Create a .worktrees directory in the test repository.
    """
    worktrees_path = os.path.join(temp_git_repo, ".worktrees")
    os.makedirs(worktrees_path, exist_ok=True)
    return worktrees_path


class TestMkWorktree:
    """Tests for mk_worktree function"""

    def test_create_worktree_with_new_branch(self, temp_git_repo, worktrees_dir):
        """Test successful worktree creation with a new branch"""
        target_dir = os.path.join(worktrees_dir, "feature-1")
        branch_name = "feature-1"

        mk_worktree(temp_git_repo, target_dir, branch_name)

        # Verify worktree directory exists
        assert os.path.exists(target_dir)

        # Verify files are checked out
        assert os.path.exists(os.path.join(target_dir, "README.md"))

        # Verify worktree is registered
        repo = Repo(temp_git_repo)
        worktree_list = repo.git.execute(["git", "worktree", "list"])
        assert target_dir in worktree_list

        # Verify branch exists
        branches = [b.name for b in repo.branches]
        assert branch_name in branches

    def test_create_worktree_with_existing_branch(self, temp_git_repo, worktrees_dir):
        """Test successful worktree creation with an existing branch"""
        # Create a branch first
        repo = Repo(temp_git_repo)
        branch_name = "existing-branch"
        repo.create_head(branch_name)

        target_dir = os.path.join(worktrees_dir, "existing")
        mk_worktree(temp_git_repo, target_dir, branch_name)

        # Verify worktree was created successfully
        assert os.path.exists(target_dir)
        assert os.path.exists(os.path.join(target_dir, "README.md"))

    def test_create_worktree_creates_parent_directory(self, temp_git_repo):
        """Test that parent directories are created if they don't exist"""
        target_dir = os.path.join(temp_git_repo, "deeply", "nested", "worktree")
        branch_name = "nested-branch"

        # Verify parent doesn't exist
        assert not os.path.exists(os.path.dirname(target_dir))

        mk_worktree(temp_git_repo, target_dir, branch_name)

        # Verify worktree and parents were created
        assert os.path.exists(target_dir)
        assert os.path.exists(os.path.join(target_dir, "README.md"))

    def test_error_when_project_dir_doesnt_exist(self, worktrees_dir):
        """Test that ValueError is raised when project_dir doesn't exist"""
        fake_project_dir = "/nonexistent/path/to/repo"
        target_dir = os.path.join(worktrees_dir, "test")

        with pytest.raises(ValueError, match="Project directory does not exist"):
            mk_worktree(fake_project_dir, target_dir, "test-branch")

    def test_error_when_target_dir_already_exists(self, temp_git_repo, worktrees_dir):
        """Test that ValueError is raised when target_dir already exists"""
        target_dir = os.path.join(worktrees_dir, "existing")
        os.makedirs(target_dir)

        with pytest.raises(ValueError, match="Target directory already exists"):
            mk_worktree(temp_git_repo, target_dir, "test-branch")

    def test_files_are_checked_out_after_creation(self, temp_git_repo, worktrees_dir):
        """Test that files are properly checked out in the worktree"""
        # Add more files to the repo
        repo = Repo(temp_git_repo)
        for filename in ["file1.txt", "file2.txt", "file3.txt"]:
            filepath = os.path.join(temp_git_repo, filename)
            with open(filepath, "w") as f:
                f.write(f"Content of {filename}\n")
            repo.index.add([filename])
        repo.index.commit("Add test files")

        # Create worktree
        target_dir = os.path.join(worktrees_dir, "test")
        mk_worktree(temp_git_repo, target_dir, "test-branch")

        # Verify all files are checked out
        for filename in ["README.md", "file1.txt", "file2.txt", "file3.txt"]:
            assert os.path.exists(os.path.join(target_dir, filename))


class TestRmWorktree:
    """Tests for rm_worktree function"""

    def test_remove_worktree_without_branch_removal(self, temp_git_repo, worktrees_dir):
        """Test successful worktree removal while keeping the branch"""
        target_dir = os.path.join(worktrees_dir, "temp-worktree")
        branch_name = "temp-branch"

        # Create worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)
        assert os.path.exists(target_dir)

        # Remove worktree
        rm_worktree(temp_git_repo, target_dir, remove_branch=False)

        # Verify worktree is removed
        assert not os.path.exists(target_dir)

        # Verify branch still exists
        repo = Repo(temp_git_repo)
        branches = [b.name for b in repo.branches]
        assert branch_name in branches

    def test_remove_worktree_with_branch_removal(self, temp_git_repo, worktrees_dir):
        """Test successful worktree and branch removal"""
        target_dir = os.path.join(worktrees_dir, "temp-worktree")
        branch_name = "temp-branch-to-delete"

        # Create worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)
        assert os.path.exists(target_dir)

        # Verify branch exists
        repo = Repo(temp_git_repo)
        branches_before = [b.name for b in repo.branches]
        assert branch_name in branches_before

        # Remove worktree and branch
        rm_worktree(temp_git_repo, target_dir, remove_branch=True)

        # Verify worktree is removed
        assert not os.path.exists(target_dir)

        # Verify branch is removed
        branches_after = [b.name for b in repo.branches]
        assert branch_name not in branches_after

    def test_error_when_target_dir_doesnt_exist(self, temp_git_repo):
        """Test that ValueError is raised when target_dir doesn't exist"""
        fake_target_dir = os.path.join(temp_git_repo, ".worktrees", "nonexistent")

        with pytest.raises(ValueError, match="Target directory does not exist"):
            rm_worktree(temp_git_repo, fake_target_dir)

    def test_remove_worktree_with_uncommitted_changes(self, temp_git_repo, worktrees_dir):
        """Test that worktree is removed even with uncommitted changes (--force)"""
        target_dir = os.path.join(worktrees_dir, "dirty-worktree")
        branch_name = "dirty-branch"

        # Create worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)

        # Make uncommitted changes
        test_file = os.path.join(target_dir, "uncommitted.txt")
        with open(test_file, "w") as f:
            f.write("Uncommitted changes\n")

        # Remove worktree (should succeed due to --force)
        rm_worktree(temp_git_repo, target_dir)

        # Verify worktree is removed
        assert not os.path.exists(target_dir)

    def test_branch_preserved_by_default(self, temp_git_repo, worktrees_dir):
        """Test that branch is preserved when remove_branch is not specified"""
        target_dir = os.path.join(worktrees_dir, "test")
        branch_name = "preserve-me"

        # Create and remove worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)
        rm_worktree(temp_git_repo, target_dir)  # remove_branch defaults to False

        # Verify branch still exists
        repo = Repo(temp_git_repo)
        branches = [b.name for b in repo.branches]
        assert branch_name in branches


class TestGetWorktreeBranch:
    """Tests for _get_worktree_branch helper function"""

    def test_get_branch_name_for_existing_worktree(self, temp_git_repo, worktrees_dir):
        """Test extracting branch name from an existing worktree"""
        target_dir = os.path.join(worktrees_dir, "test")
        branch_name = "test-branch"

        # Create worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)

        # Get branch name
        result = _get_worktree_branch(temp_git_repo, target_dir)

        assert result == branch_name

    def test_get_branch_returns_none_for_nonexistent_worktree(self, temp_git_repo):
        """Test that None is returned for a non-existent worktree"""
        fake_target_dir = os.path.join(temp_git_repo, ".worktrees", "nonexistent")

        result = _get_worktree_branch(temp_git_repo, fake_target_dir)

        assert result is None

    def test_get_branch_with_multiple_worktrees(self, temp_git_repo, worktrees_dir):
        """Test extracting branch name when multiple worktrees exist"""
        # Create multiple worktrees
        worktrees = [
            (os.path.join(worktrees_dir, "wt1"), "branch1"),
            (os.path.join(worktrees_dir, "wt2"), "branch2"),
            (os.path.join(worktrees_dir, "wt3"), "branch3"),
        ]

        for target_dir, branch_name in worktrees:
            mk_worktree(temp_git_repo, target_dir, branch_name)

        # Verify we can get the correct branch for each worktree
        for target_dir, expected_branch in worktrees:
            result = _get_worktree_branch(temp_git_repo, target_dir)
            assert result == expected_branch


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_workflow_create_and_remove(self, temp_git_repo, worktrees_dir):
        """Test complete workflow: create worktree, work in it, remove it"""
        target_dir = os.path.join(worktrees_dir, "workflow-test")
        branch_name = "workflow-branch"

        # Create worktree
        mk_worktree(temp_git_repo, target_dir, branch_name)
        assert os.path.exists(target_dir)

        # Simulate work in the worktree
        work_file = os.path.join(target_dir, "work.txt")
        with open(work_file, "w") as f:
            f.write("Work done in worktree\n")

        worktree_repo = Repo(target_dir)
        worktree_repo.index.add(["work.txt"])
        worktree_repo.index.commit("Work commit")

        # Remove worktree but keep branch
        rm_worktree(temp_git_repo, target_dir, remove_branch=False)
        assert not os.path.exists(target_dir)

        # Verify branch still exists and has the commit
        repo = Repo(temp_git_repo)
        branch = repo.branches[branch_name]
        assert branch is not None
        commits = list(repo.iter_commits(branch_name, max_count=1))
        assert len(commits) > 0
        assert "Work commit" in commits[0].message

    def test_multiple_worktrees_independent_operations(self, temp_git_repo, worktrees_dir):
        """Test that multiple worktrees can be created and removed independently"""
        worktrees = [
            (os.path.join(worktrees_dir, f"wt{i}"), f"branch{i}")
            for i in range(3)
        ]

        # Create all worktrees
        for target_dir, branch_name in worktrees:
            mk_worktree(temp_git_repo, target_dir, branch_name)
            assert os.path.exists(target_dir)

        # Remove middle worktree
        rm_worktree(temp_git_repo, worktrees[1][0])
        assert not os.path.exists(worktrees[1][0])

        # Verify others still exist
        assert os.path.exists(worktrees[0][0])
        assert os.path.exists(worktrees[2][0])

        # Clean up remaining
        rm_worktree(temp_git_repo, worktrees[0][0], remove_branch=True)
        rm_worktree(temp_git_repo, worktrees[2][0], remove_branch=True)
