#!/bin/bash
# Script to generate algorithm problem descriptions (wrapper)

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

MODE="$1"
if [ -z "$MODE" ]; then
  echo "Usage: $0 <fim|l2r> [--config <path>] [--num-samples <N>]"
  exit 1
fi

shift || true

python scripts/datagen/generate_problems.py --mode "$MODE" "$@"

