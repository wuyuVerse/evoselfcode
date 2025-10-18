#!/bin/bash
# Convert FIM rated data to ChatML format (background)

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
mkdir -p "$PROJECT_ROOT/logs/datagen/convert_fim"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PID_FILE="$PROJECT_ROOT/logs/datagen/convert_fim/conversion.pid"

# Run in background (output handled by Python logger)
echo "🔄 Starting FIM data conversion to ChatML in background..."

nohup python scripts/datagen/convert_to_chatml.py --mode fim "$@" > /dev/null 2>&1 &

# Get PID
PID=$!
echo $PID > "$PID_FILE"
echo "✅ Process started with PID: $PID"
echo "📁 Logs will be in: $PROJECT_ROOT/logs/datagen/convert_fim/"
echo "📊 Monitor: tail -f $PROJECT_ROOT/logs/datagen/convert_fim/*.log"
echo "🛑 To stop: kill $PID"

