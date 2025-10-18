#!/bin/bash
# Script to generate algorithm problem descriptions using L2R (Left-to-Right) completion mode
# Runs in background and logs to file

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs/datagen/problems_l2r"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/datagen/problems_l2r/generation_${TIMESTAMP}.log"
PID_FILE="$PROJECT_ROOT/logs/datagen/problems_l2r/generation.pid"

# Run in background (output handled by Python logger)
echo "🚀 Starting L2R problem generation in background..."

nohup python scripts/datagen/generate_problems.py --mode l2r "$@" > /dev/null 2>&1 &

# Get PID
PID=$!
echo $PID > "$PID_FILE"
echo "✅ Process started with PID: $PID"
echo "📁 Logs will be in: $PROJECT_ROOT/logs/datagen/problems_l2r/"
echo "📊 Monitor: ls -lht $PROJECT_ROOT/logs/datagen/problems_l2r/ | head"
echo "🛑 To stop: kill $PID"

