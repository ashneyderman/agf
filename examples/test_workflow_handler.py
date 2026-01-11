#!/usr/bin/env python3
"""Manual test script for WorkflowTaskHandler.

This script demonstrates and tests the WorkflowTaskHandler by:
1. Creating a temporary git repository
2. Setting up a sample tasks.md file
3. Initializing the configuration and task manager
4. Executing a task using the handler
5. Verifying worktree creation and task execution

Usage:
    uv run python examples/test_workflow_handler.py
"""

import os
import tempfile
from pathlib import Path

from git import Repo

from agf.config.models import AGFConfig, AgentModelConfig, CLIConfig
from agf.config import merge_configs
from agf.task_manager import TaskManager
from agf.task_manager.markdown_source import MarkdownTaskSource
from agf.workflow import WorkflowTaskHandler


def main():
    """Run manual test of WorkflowTaskHandler."""
    print("=" * 70)
    print("WorkflowTaskHandler Manual Test")
    print("=" * 70)

    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nTest directory: {tmpdir}")

        # Initialize git repository
        print("\n1. Initializing git repository...")
        repo = Repo.init(tmpdir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # Create initial commit
        readme_path = os.path.join(tmpdir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Test Project\n")
        repo.index.add([readme_path])
        repo.index.commit("Initial commit")
        print("   Git repository initialized")

        # Create tasks.md file
        print("\n2. Creating tasks.md file...")
        tasks_file = os.path.join(tmpdir, "tasks.md")
        with open(tasks_file, "w") as f:
            f.write("""# Tasks

## Git Worktree test-feature

- [] Sample test task for workflow handler
  task_id: test01
""")
        print(f"   Created: {tasks_file}")

        # Create configuration
        print("\n3. Setting up configuration...")
        agf_config = AGFConfig(
            worktrees=".worktrees",
            concurrent_tasks=1,
            agent="claude-code",
            model_type="standard",
            agents={
                "claude-code": AgentModelConfig(
                    thinking="opus", standard="sonnet", light="haiku"
                )
            },
        )
        cli_config = CLIConfig(
            tasks_file=Path(tasks_file),
            project_dir=Path(tmpdir),
        )
        effective_config = merge_configs(agf_config, cli_config)
        print(f"   Project dir: {effective_config.project_dir}")
        print(f"   Worktrees dir: {effective_config.worktrees}")
        print(f"   Agent: {effective_config.agent}")
        print(f"   Model type: {effective_config.model_type}")

        # Initialize TaskManager
        print("\n4. Initializing TaskManager...")
        markdown_source = MarkdownTaskSource(file_path=tasks_file)
        task_manager = TaskManager(task_source=markdown_source)
        worktrees = task_manager.list_worktrees()
        print(f"   Found {len(worktrees)} worktree(s)")
        for wt in worktrees:
            print(f"   - {wt.worktree_name}: {len(wt.tasks)} task(s)")

        # Create WorkflowTaskHandler
        print("\n5. Creating WorkflowTaskHandler...")
        handler = WorkflowTaskHandler(effective_config, task_manager)
        print("   Handler created")

        # Fetch next available task
        print("\n6. Fetching next available task...")
        available_tasks = task_manager.fetch_next_available_tasks(count=1)
        if not available_tasks:
            print("   No tasks available for processing")
            return

        worktree, task = available_tasks[0]
        print(f"   Task ID: {task.task_id}")
        print(f"   Description: {task.description}")
        print(f"   Status: {task.status}")
        print(f"   Worktree: {worktree.worktree_name}")

        # Execute task (this will fail because agent isn't actually available in temp dir)
        print("\n7. Executing task with handler...")
        print("   Note: This will fail because claude-code isn't available")
        print("   in the test environment, but it demonstrates the workflow.")

        try:
            success = handler.handle_task(worktree, task)
            print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        except Exception as e:
            print(f"   Expected error (agent not available): {e}")

        # Verify worktree was created
        print("\n8. Verifying worktree creation...")
        worktree_path = os.path.join(tmpdir, ".worktrees", worktree.worktree_name)
        if os.path.exists(worktree_path):
            print(f"   ✓ Worktree created at: {worktree_path}")

            # Check branch
            wt_repo = Repo(worktree_path)
            branch_name = wt_repo.active_branch.name
            username = os.getenv("USER", "unknown")
            expected_branch = f"{username}/{worktree.worktree_name}"
            print(f"   ✓ Branch: {branch_name}")
            if branch_name == expected_branch:
                print(f"   ✓ Branch name matches expected: {expected_branch}")
            else:
                print(f"   ✗ Branch name mismatch. Expected: {expected_branch}")
        else:
            print(f"   ✗ Worktree not created at: {worktree_path}")

        # List all worktrees
        print("\n9. Listing git worktrees...")
        worktree_list = repo.git.execute(["git", "worktree", "list"])
        print(worktree_list)

    print("\n" + "=" * 70)
    print("Test completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
