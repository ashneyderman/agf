# Prime

> Execute the following sections to understand the codebase then summarize your understanding.

## Run

git ls-files

## Read

Read README.md file in the root of the project

- if: README.md is not found
  then: report "README.md not found"

- if: section `## pre-requisites` exist
  then: execute all commands in that section that validate the pre-requisites are satisfied
  else: report "section ## pre-requisites not found"

- if: section `## installation` exists
  then: execute all commands in the section
  else: report "section ## installation not found"

- if: section `## build` exists
  then: execute all commands in the section
  else: report "section ## build not found"
