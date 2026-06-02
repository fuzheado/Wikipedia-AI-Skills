#!/bin/bash
# Wrapper for 04-generate-taskgraph.py
DIR="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$DIR/scripts/04-generate-taskgraph.py" "$@"
