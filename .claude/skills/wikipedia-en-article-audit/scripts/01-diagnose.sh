#!/bin/bash
# Wrapper for 01-diagnose.py
DIR="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$DIR/scripts/01-diagnose.py" "$@"
