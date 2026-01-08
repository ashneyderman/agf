# SDLC Prompt Wrappers

## Purpose

Create wrapper function for each of the SDLC-related prompts that AGF project provides.

## Worklfow

- for each of the SDLC related prompts: @agf_commands/{plan.md,chore.md,feature.md,implement.md} create a wrapper function that calls the prompt.
- make sure that each wrapper function takes on all the arguments/variables that the prompt requires.
- make sure that each wrapper function returns the parsed json response from the prompt if it has one.

## Instructions

- place all the wrapper functions in agf/workflow/task_handler.py
- make all wrappers are protected functions
- make sure to cover all wrappers with tests
- each prompt will have `## Variables` section that lists all the variables for the prompt, in the wrapper make sure we have all the variables declared in the function signature in addition to the worktree, and task.
- return values will be declared as either JSON in which case return the jsonvalue that we will parse, or sometimes in `## Report` section return value is said to be some variation of string value, so make sure to return the string.
