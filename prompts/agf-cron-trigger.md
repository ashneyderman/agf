## Task description

Create tasks triggerring mechanism that spins up the workflows. Create a script in `triggers` package. The script should be able to take the following arguments:

- tasks-file: location of the tasks file; could be an absolute or a relative path. This is required attribute that has to point to an existing .md file that lists the tasks.
- project-dir: root directory of the project for which the workflows are started; could be an absolute or relative path. This is required attribute that has to point to an existing directory.
- sync-interval: interval in seconds that indicates how often the trigger runs to put together a set of ready to run tasks. This value defaults to 30 seconds.
- dry-run: a boolean flag indicating if trigger is in read only mode or executes operations that can cause changes to the project. This flag defaults to False.
- single-run: a boolean flag that indicates if trigger is run continuosly until termination signal or script runs only once and exits. This flag defaults to False.

Example invocations:

```bash

> uv run triggers/find_and_start_tasks.py --task-file ./tasks.md --project-dir . --dry-run --single-running
> uv run triggers/find_and_start_tasks.py --task-file /home/my_tasks.md --project-dir /home/alex/projects/my_project --sync-interval 15
```

## Dependencies

use click package to create command line interface with the script.
use schedule package to create cron like runs when running in non single-run mode.

## Implementation

The script's main function is responsible for parsing command line arguments and initializing the trigger loop.
A single iteration of the loop has to determine a list of tasks that are ready to run. It does that by calling
`/agf:process_tasks <tasks-file>` prompt.

The result of the prompt's execution should be a list of tasks that are ready to run.

At this stage we only need to parse the list of tasks and print what could find.

Scheduler's sync-interval indicates the time interval after last finished iteration of the loop. So stagger the loop executions **do not** overlap.
