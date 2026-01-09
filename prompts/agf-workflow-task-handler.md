# Workflow Task Handler

Create workflow task handler to be able to process a given task in a uniform way.

## Purpose

The purpose of this workflow task handler is to provide a standardized way to process tasks within the workflow system. It ensures consistency and efficiency in handling tasks across different workflows and logging for traceability.

## Workflow

0. handler recieves config: EffectiveConfig, task_manager: TaskManager, worktree: Worktree, task: Task as parameters
1. use `git_repo.py` functions to initialize worktree for the handler.
   - if: worktree target directory does not exist create it with mk_worktree and checkout branch named {`whoami`}/{worktree.worktree_name}.
   - if: worktree target directory exists make sure the branch {`whoami`}/{worktree.worktree_name} is checked out and no uncommitted changes exist. Mark task failed if any uncommitted changes exist.
2. mark task status as IN_PROGRESS.
3. run agentic prompt with the agent wrapper AgentRunner.run_command(config.agent, "/agf:test-prompt {task.task_id} {task.description}", AgentConfig(model=config.model, workdir=absoulte directory to(worktree.worktree_path))).
4. mark task status as SUCCESS or FAILURE based on the outcome of the task execution.

## Implementation

- create all the handling logic inside `agf/workflow` folder
