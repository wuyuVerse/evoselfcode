#!/bin/bash
# Script to generate function names using L2R (Left-to-Right) completion mode
# Runs in background and logs to file

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs/datagen/l2r"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/datagen/l2r/generation_${TIMESTAMP}.log"
PID_FILE="$PROJECT_ROOT/logs/datagen/l2r/generation.pid"

# Run in background and redirect output to log file
echo "🚀 Starting L2R generation in background..."
echo "📝 Log file: $LOG_FILE"

nohup python scripts/generate_funcnames.py --mode l2r "$@" > "$LOG_FILE" 2>&1 &

# Get PID
PID=$!
echo "✅ Process started with PID: $PID"
echo "📊 Monitor progress: tail -f $LOG_FILE"
echo "$PID" > "$PID_FILE"
echo "🛑 To stop: kill $(cat $PID_FILE)"

