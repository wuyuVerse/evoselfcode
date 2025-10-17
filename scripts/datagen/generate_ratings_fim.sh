#!/bin/bash
# Generate Quality Ratings for FIM Implementations
# Run in background with nohup

# Determine project root (two levels up from scripts/datagen/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Create log directory
LOG_DIR="$PROJECT_ROOT/logs/datagen/rating_fim"
mkdir -p "$LOG_DIR"

# PID file for process management
PID_FILE="$LOG_DIR/generation.pid"

echo "========================================" 
echo "Starting FIM Rating Generation"
echo "========================================" 
echo "Project Root: $PROJECT_ROOT"
echo "Logs will be in: $LOG_DIR/"
echo "Monitor: ls -lht $LOG_DIR/ | head"
echo ""

cd "$PROJECT_ROOT"

# Run generation in background
nohup python scripts/datagen/generate_ratings.py --source fim > /dev/null 2>&1 &

# Save PID
echo $! > "$PID_FILE"
echo "Process ID: $(cat $PID_FILE)"
echo ""
echo "To stop: kill \$(cat $PID_FILE)"
echo "To monitor: tail -f $LOG_DIR/\$(ls -t $LOG_DIR/*.log | head -1)"

