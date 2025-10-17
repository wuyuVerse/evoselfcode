#!/bin/bash
# Script to generate function names using FIM (Fill-in-Middle) mode
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
mkdir -p "$PROJECT_ROOT/logs/datagen/problems_fim"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/datagen/problems_fim/generation_${TIMESTAMP}.log"
PID_FILE="$PROJECT_ROOT/logs/datagen/problems_fim/generation.pid"

# Run in background (output handled by Python logger)
echo "🚀 Starting FIM generation in background..."

nohup python scripts/datagen/generate_funcnames.py --mode fim "$@" > /dev/null 2>&1 &

# Get PID
PID=$!
echo $PID > "$PID_FILE"
echo "✅ Process started with PID: $PID"
echo "📁 Logs will be in: $PROJECT_ROOT/logs/datagen/problems_fim/"
echo "📊 Monitor: ls -lht $PROJECT_ROOT/logs/datagen/problems_fim/ | head"
echo "🛑 To stop: kill $PID"

