#!/bin/bash
# Script to generate function names using FIM (Fill-in-Middle) mode
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
mkdir -p "$PROJECT_ROOT/logs/scripts"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/scripts/fim_generation_${TIMESTAMP}.log"

# Run in background and redirect output to log file
echo "🚀 Starting FIM generation in background..."
echo "📝 Log file: $LOG_FILE"

nohup python scripts/generate_funcnames.py --mode fim "$@" > "$LOG_FILE" 2>&1 &

# Get PID
PID=$!
echo "✅ Process started with PID: $PID"
echo "📊 Monitor progress: tail -f $LOG_FILE"
echo "$PID" > "$PROJECT_ROOT/logs/scripts/fim_generation.pid"
echo "🛑 To stop: kill $(cat $PROJECT_ROOT/logs/scripts/fim_generation.pid)"

