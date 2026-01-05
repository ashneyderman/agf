Create ability to configure the system on multiple levels. System has to have a
system wide deafults for things like agent to use and default model type to use.
We also want to be able to override those defaults either via a config yaml file
or via command line arguments.

## Implementation

- Create `AGFConfig` model that represents system wide config options. Those options
  should reflect content of the following sample yaml:

```yaml
worktrees: .worktrees
concurrent-tasks: 5
agent: claude-code
model-type: standard
agents:
  claude-code:
    thinking: opus
    standard: sonnet
    light: haiku
  opencode:
    thinking: github-copilot/claude-opus-4.5
    standard: github-copilot/claude-sonnet-4.5
    light: github-copilot/claude-haiku-4.5
```

place class in `agf/config` package. Create methods to create config instance from a yaml file. Set default values to those in the sample yaml.

- Create `CLIConfig` model that collects the following options:
  - `tasks-file`: location of the tasks file; could be an absolute or a relative path.
  - `project-dir`: root directory of the project for which the workflows are started; could be an absolute or relative path.
  - `agi-config`: location of the AGF config file; could be an absolute or a relative path.
  - `sync-interval`: interval in seconds that indicates how often the trigger runs to put together a set of ready to run tasks. This value defaults to 30 seconds.
  - `dry-run`: a boolean flag indicating if trigger is in read only mode or executes operations that can cause changes to the project. This flag defaults to False.
  - `single-run`: a boolean flag that indicates if trigger is run continuosly until termination signal or script runs only once and exits. This flag defaults to False.
  - `agent`: string that represents the agent to use for the workflow. This value defaults to None
  - `model-type`: string that represents the model type to use for the workflow. This value defaults to None

We should be able to also collect CLI level options from the command line arguments and create an instance of `CLIConfig` from them.
