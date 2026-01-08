#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PARENT_DIR:$PYTHONPATH" uv run "$PARENT_DIR/agf/triggers/process_tasks.py" "$@"
