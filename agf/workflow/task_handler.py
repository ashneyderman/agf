"""Workflow task handler for processing tasks in isolated git worktrees.

This module provides the WorkflowTaskHandler class that orchestrates task
execution by managing git worktrees, executing agents, and tracking task status.
"""

import os
import os.path
from datetime import datetime
from imaplib import Commands

from git import Repo

from agf.agent import AgentRunner
from agf.agent.base import AgentConfig, AgentResult, ModelType
from agf.agent.models import CommandTemplate
from agf.config.models import EffectiveConfig
from agf.git_repo import mk_worktree
from agf.task_manager import TaskManager
from agf.task_manager.models import Task, TaskStatus, Worktree


class WorkflowTaskHandler:
    """Handler for executing tasks in isolated git worktrees.

    This handler orchestrates the complete task execution workflow:
    1. Initialize or validate git worktree
    2. Update task status to IN_PROGRESS
    3. Execute agent with configured model and prompt
    4. Update task status to COMPLETED or FAILED based on result
    5. Record errors for failed tasks

    The handler ensures tasks are executed in clean worktrees with proper
    branch naming and validates worktree state before execution.

    Example:
        >>> config = EffectiveConfig(...)
        >>> task_manager = TaskManager(...)
        >>> handler = WorkflowTaskHandler(config, task_manager)
        >>> success = handler.handle_task(worktree, task)
    """

    def __init__(self, config: EffectiveConfig, task_manager: TaskManager) -> None:
        """Initialize the workflow task handler.

        Args:
            config: Effective configuration with execution parameters
            task_manager: Task manager for status updates and task lookup
        """
        self.config = config
        self.task_manager = task_manager

    def _log(self, message: str) -> None:
        """Log a message with timestamp.

        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def _get_username(self) -> str:
        """Get the current username for branch naming.

        Returns:
            Username from USER environment variable, or "unknown" if not set
        """
        return os.getenv("USER", "unknown")

    def _get_worktree_path(self, worktree: Worktree) -> str:
        """Construct the absolute path to the worktree directory.

        Args:
            worktree: Worktree object containing the worktree name

        Returns:
            Absolute path to the worktree directory
        """
        return os.path.abspath(
            os.path.join(
                str(self.config.project_dir),
                self.config.worktrees,
                worktree.worktree_name,
            )
        )

    def _get_branch_name(self, worktree: Worktree) -> str:
        """Construct the branch name for the worktree.

        Uses the convention:
        - {username}/{worktree_id}-{worktree_name} when worktree_id is not None
        - {username}/{worktree_name} when worktree_id is None

        Args:
            worktree: Worktree object containing the worktree name and optional worktree_id

        Returns:
            Branch name in the format: {username}/{worktree_id}-{worktree_name}
            or {username}/{worktree_name} if worktree_id is None
        """
        username = self._get_username()
        if worktree.worktree_id is not None:
            return f"{username}/{worktree.worktree_id}-{worktree.worktree_name}"
        return f"{username}/{worktree.worktree_name}"

    def _has_uncommitted_changes(self, worktree_path: str) -> bool:
        """Check if the worktree has uncommitted changes.

        Args:
            worktree_path: Path to the worktree directory

        Returns:
            True if there are uncommitted changes (modified or untracked files),
            False otherwise

        Raises:
            Exception: If git operations fail
        """
        try:
            repo = Repo(worktree_path)
            # Check for modified/staged files
            if repo.is_dirty():
                return True
            # Check for untracked files
            if repo.untracked_files:
                return True
            return False
        except Exception as e:
            self._log(f"Error checking uncommitted changes: {e}")
            raise

    def _validate_branch_checkout(
        self, worktree_path: str, expected_branch: str
    ) -> bool:
        """Validate that the worktree has the expected branch checked out.

        Args:
            worktree_path: Path to the worktree directory
            expected_branch: Expected branch name

        Returns:
            True if the current branch matches expected_branch, False otherwise

        Raises:
            Exception: If git operations fail or HEAD is detached
        """
        try:
            repo = Repo(worktree_path)
            current_branch = repo.active_branch.name
            return current_branch == expected_branch
        except Exception as e:
            self._log(f"Error validating branch checkout: {e}")
            raise

    def _initialize_worktree(self, worktree: Worktree) -> str:
        """Initialize or validate the worktree for task execution.

        If the worktree directory doesn't exist, it will be created with the
        appropriate branch. If it exists, it will be validated to ensure it has
        the correct branch checked out and no uncommitted changes.

        Args:
            worktree: Worktree object containing worktree metadata

        Returns:
            Absolute path to the initialized worktree directory

        Raises:
            ValueError: If worktree exists but has wrong branch or uncommitted changes
            Exception: If worktree creation fails
        """
        worktree_path = self._get_worktree_path(worktree)
        branch_name = self._get_branch_name(worktree)

        try:
            if not os.path.exists(worktree_path):
                # Create new worktree
                self._log(
                    f"Creating worktree at {worktree_path} with branch {branch_name}"
                )
                mk_worktree(
                    project_dir=str(self.config.project_dir),
                    target_dir=worktree_path,
                    branch_name=branch_name,
                )
                self._log("Worktree created successfully")
            else:
                # Validate existing worktree
                self._log("Worktree directory exists, validating state")

                # Check branch
                if not self._validate_branch_checkout(worktree_path, branch_name):
                    repo = Repo(worktree_path)
                    actual_branch = repo.active_branch.name
                    raise ValueError(
                        f"Expected branch {branch_name} but found {actual_branch}"
                    )

                # Check for uncommitted changes
                if self._has_uncommitted_changes(worktree_path):
                    raise ValueError("Worktree has uncommitted changes")

                self._log("Worktree validation passed")

            return worktree_path
        except Exception as e:
            self._log(f"Error initializing worktree: {e}")
            raise

    def _execute_command(
        self, worktree_path: str, command_template: CommandTemplate
    ) -> AgentResult:
        """Execute the command with the agent in the specified worktree.

        Args:
            worktree_path: Path to the worktree directory
            command_template: CommandTemplate object containing command metadata

        Returns:
            AgentResult containing execution status and output
        """
        # Resolve model from configuration
        agent_config = self.config.agents[self.config.agent]
        model = getattr(agent_config, command_template.model or self.config.model_type)

        # Create agent configuration
        agent_cfg = AgentConfig(
            working_dir=worktree_path,
            skip_permissions=True,
        )

        # Execute agent
        self._log(f"Running agent command {self.config.agent} with model {model}")
        result = AgentRunner.run_command(
            agent_name=self.config.agent,
            prompt_template=command_template,
            config=agent_cfg,
        )
        self._log(
            f"Agent execution completed: success={result.success}, exit_code={result.exit_code}"
        )
        self._log(f"output={result.output}")
        self._log(f"json_output={result.json_output}")

        return result

    def _run_plan(self, worktree: Worktree, task: Task) -> str:
        """Execute the plan prompt and return the plan file path.

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata

        Returns:
            Path to the created plan file

        Raises:
            Exception: If agent execution fails or JSON parsing fails
        """
        worktree_path = self._get_worktree_path(worktree)
        command_template = CommandTemplate(
            prompt="plan",
            params=[worktree.worktree_id or task.task_id, task.description],
            model=ModelType.THINKING,
            json_output=True,
        )
        result = self._execute_command(worktree_path, command_template)
        return result.json_output["path"]

    def _run_chore(self, worktree: Worktree, task: Task) -> str:
        """Execute the chore prompt and return the chore plan file path.

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata

        Returns:
            Path to the created chore plan file

        Raises:
            Exception: If agent execution fails or JSON parsing fails
        """
        worktree_path = self._get_worktree_path(worktree)
        command_template = CommandTemplate(
            prompt="chore",
            params=[worktree.worktree_id or task.task_id, task.description],
            model=ModelType.STANDARD,
            json_output=True,
        )
        result = self._execute_command(worktree_path, command_template)
        return result.json_output["path"]

    def _run_feature(self, worktree: Worktree, task: Task) -> str:
        """Execute the feature prompt and return the feature plan file path.

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata

        Returns:
            Path to the created feature plan file

        Raises:
            Exception: If agent execution fails or JSON parsing fails
        """
        worktree_path = self._get_worktree_path(worktree)
        command_template = CommandTemplate(
            prompt="feature",
            params=[worktree.worktree_id or task.task_id, task.description],
            model=ModelType.THINKING,
            json_output=True,
        )
        result = self._execute_command(worktree_path, command_template)
        return result.json_output["path"]

    def _run_implement(self, worktree: Worktree, task: Task, spec_path: str) -> str:
        """Execute the implement prompt and return the implementation summary.

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata
            spec_path: Path to the specification/plan file to implement

        Returns:
            Summary of the implementation work completed

        Raises:
            Exception: If agent execution fails
        """
        worktree_path = self._get_worktree_path(worktree)
        command_template = CommandTemplate(
            prompt="implement",
            params=[f"@{spec_path}"],
            model=ModelType.STANDARD,
            json_output=False,
        )
        result = self._execute_command(worktree_path, command_template)
        return result.output.strip()

    def _create_commit(self, worktree: Worktree, task: Task) -> dict:
        """Execute the create-commit prompt and return commit information.

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata

        Returns:
            Dictionary containing commit_sha and commit_message

        Raises:
            Exception: If agent execution fails or JSON parsing fails
        """
        worktree_path = self._get_worktree_path(worktree)
        command_template = CommandTemplate(
            prompt="create-commit",
            params=[],
            model=ModelType.STANDARD,
            json_output=True,
        )
        result = self._execute_command(worktree_path, command_template)
        return result.json_output

    def _get_task_type(self, task: Task) -> str | None:
        """Detect the task type from task tags.

        Args:
            task: Task object containing tags

        Returns:
            Task type string ("chore", "feature", or "plan") or None if not found
        """
        valid_types = ["chore", "feature", "plan"]
        for tag in task.tags:
            if tag in valid_types:
                return tag
        return None

    def handle_task(self, worktree: Worktree, task: Task) -> bool:
        """Handle complete task execution workflow with SDLC phases.

        This method orchestrates the entire task execution process:
        1. Initialize or validate worktree
        2. Update task status to IN_PROGRESS
        3. Detect task type and run planning phase (plan/chore/feature)
        4. Run implementation phase
        5. Run commit phase
        6. Update task status to COMPLETED with commit SHA

        Args:
            worktree: Worktree object containing worktree metadata
            task: Task object containing task metadata

        Returns:
            True if task completed successfully, False if it failed
        """
        self._log(
            f"Starting task handler for task {task.task_id} in worktree {worktree.worktree_name}"
        )

        try:
            # Initialize worktree
            worktree_path = self._initialize_worktree(worktree)

            # Update task status to IN_PROGRESS
            self.task_manager.update_task_status(
                worktree.worktree_name, task.task_id, TaskStatus.IN_PROGRESS
            )

            # Detect task type
            task_type = self._get_task_type(task)
            if not task_type:
                error_msg = "Task type not found in tags. Valid task types: chore, feature, plan"
                self._log(f"Task {task.task_id} failed: {error_msg}")
                self.task_manager.update_task_status(
                    worktree.worktree_name, task.task_id, TaskStatus.FAILED
                )
                self.task_manager.mark_task_error(
                    worktree.worktree_name, task.task_id, error_msg
                )
                return False

            # Phase 1: Planning (run appropriate planning method based on task type)
            try:
                if task_type == "plan":
                    spec_path = self._run_plan(worktree, task)
                elif task_type == "chore":
                    spec_path = self._run_chore(worktree, task)
                elif task_type == "feature":
                    spec_path = self._run_feature(worktree, task)
                else:
                    raise ValueError(f"Unknown task type: {task_type}")
            except Exception as e:
                raise Exception(f"Planning phase failed: {str(e)}") from e

            # Phase 2: Implementation
            try:
                implementation_summary = self._run_implement(worktree, task, spec_path)
            except Exception as e:
                raise Exception(f"Implementation phase failed: {str(e)}") from e

            # Phase 3: Commit
            try:
                commit_info = self._create_commit(worktree, task)
                commit_sha = commit_info.get("commit_sha")
            except Exception as e:
                raise Exception(f"Commit phase failed: {str(e)}") from e

            # Update task status to COMPLETED
            self.task_manager.update_task_status(
                worktree.worktree_name,
                task.task_id,
                TaskStatus.COMPLETED,
                commit_sha=commit_sha,
            )
            self._log(f"Task {task.task_id} completed successfully")
            return True

        except Exception as e:
            # Handle any unexpected errors
            error_msg = str(e)
            self._log(f"Error handling task {task.task_id}: {error_msg}")
            self.task_manager.update_task_status(
                worktree.worktree_name, task.task_id, TaskStatus.FAILED
            )
            self.task_manager.mark_task_error(
                worktree.worktree_name, task.task_id, error_msg
            )
            return False
