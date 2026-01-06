## Process tasks trigger

Create tasks triggerring mechanism that spins up the agentic workflows (agf).

## Implementation

- Create a script in `agf/triggers` package. The script should be able to take the same arguments that we handle in `CLIConfig` class. Make sure we create `EffectiveConfig` that we use in the script.
- Use `TaskManager` to collect and select the tasks that need processing. Initialize `TaskManager` with `MarkdownTaskSource(file_path=<tasks-file>)` as the `task_source`.
- IF single-run = True: run a single iteration.
- IF single-run = False: run an iteration of the script on a schedule with interval specified by `sync_interval` in the config. Stagger execution i.e. only schedule new iteration if tasks queue is empty.
- Process the tasks available in parallel in batches of no more than `EffectiveConfig.concurrent_tasks`. An example of this sort of parallelism can be seen in `main.py`.
- Create task processor that will take in effective config, task_manager, (worktree, task) as arguments and prints task information then sleep between 15 and 45 seconds. The following has to be printed (one item per line):
  - worktree.worktree_name
  - task.task_id
  - first 20 characters of task.description
  - sleep interval selected (between 15 and 45 seconds)

### Examples of usage

```bash
> uv run triggers/process_tasks.py --task-file ./tasks.md --project-dir . --dry-run --single-running
> uv run triggers/process_tasks.py --task-file /home/my_tasks.md --project-dir /home/alex/projects/my_project --sync-interval 15
```

## Dependencies

use click package to create command line interface with the script.
use schedule package to create cron like runs when running in non single-run mode.
