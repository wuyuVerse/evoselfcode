#!/bin/bash
# Convert rated data to ChatML format (wrapper script)

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
  echo "Usage: $0 <fim|l2r> [--config <path>]"
  echo ""
  echo "Examples:"
  echo "  $0 fim                    # Convert FIM data using config paths"
  echo "  $0 l2r                    # Convert L2R data using config paths"
  exit 1
fi

shift || true

echo "🔄 Converting $MODE data to ChatML format..."
python scripts/datagen/convert_to_chatml.py --mode "$MODE" "$@"

