# Agentic Flow

## Overview

The project contains the **Agentic Flow** - the highest level of abstraction in the agentic layer. These are executable Python scripts that orchestrate coding agents to perform SDLC activities that are typical for most software development projects.

The project provides a set of prompts, meta-prompts, skills and abstraction layer over a concrete coding agent invocations (claude code, codex, opencode, etc.). It also provides a set of scripts that trigger these workflow invocations.

The goal of this project is to externalize all the common AI workflow artifacts and activities while leaving the specifics of how target project organizes itself while providing access to various agents.

## Installation

Requires Python 3.10+ and Atros's uv package. Please make sure both are installed prior to running the project.

## Pre-requisites

```
❯ python --version
Python 3.12.0
```

```
❯ uv --version
uv 0.7.
```

## Build

```
❯ uv sync
Resolved 1 package in 12ms
Audited in 0.01ms
```

## Running

```
❯ bin/start.sh
```

## Architecture

```
README.md                          # This file
  bin/*.sh                         # Scripts for starting, stopping, and managing the project
```
