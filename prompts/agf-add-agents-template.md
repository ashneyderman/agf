# Agents Prompt Template

# Purpose

Unify prompt processing across all the available command prompts so we have a single finction that can run any prompts in agf namspace.

# Workflow

- create `CommandTemplate` model in `agf/agent/models.py`. Add the following fields:
  - namespace: str default value "agf",
  - prompt: str required field,
  - params: list default value None,
  - json_output: boolean default False,
  - model: ModelType default None
- rename `run` to `run_prompt` protocol function in `Agent` and replace prompt parameter with prompt_template: CommandTemplate
- change opencode implementation of `run` to `run_prompt`
- add claude code implementation of `run` to `run_prompt`
