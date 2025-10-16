#!/bin/bash
# Script to generate function skeletons from FIM problem descriptions in background

# Change to project root
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
source .venv/bin/activate

# Create log directory
LOG_DIR="logs/datagen/skeleton/fim"
mkdir -p "$LOG_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/${TIMESTAMP}.log"
PID_FILE="$LOG_DIR/generation.pid"

# Run in background with nohup
nohup python scripts/generate_skeletons.py --source fim > "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"
echo "Started skeleton generation (FIM mode) in background"
echo "PID: $(cat $PID_FILE)"
echo "Log: $LOG_FILE"

