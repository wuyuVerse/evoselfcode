#!/bin/bash
# Convert L2R rated data to ChatML format (background)

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
mkdir -p "$PROJECT_ROOT/logs/datagen/convert_l2r"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PID_FILE="$PROJECT_ROOT/logs/datagen/convert_l2r/conversion.pid"

# Run in background (output handled by Python logger)
echo "🔄 Starting L2R data conversion to ChatML in background..."

nohup python scripts/datagen/convert_to_chatml.py --mode l2r "$@" > /dev/null 2>&1 &

# Get PID
PID=$!
echo $PID > "$PID_FILE"
echo "✅ Process started with PID: $PID"
echo "📁 Logs will be in: $PROJECT_ROOT/logs/datagen/convert_l2r/"
echo "📊 Monitor: tail -f $PROJECT_ROOT/logs/datagen/convert_l2r/*.log"
echo "🛑 To stop: kill $PID"

