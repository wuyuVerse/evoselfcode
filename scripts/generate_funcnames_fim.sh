#!/bin/bash
# Script to generate function names using FIM (Fill-in-Middle) mode

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Use Python script instead of CLI
python scripts/generate_funcnames.py --mode fim "$@"

