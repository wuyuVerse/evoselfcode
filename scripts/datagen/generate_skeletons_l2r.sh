#!/bin/bash
# Script to generate function skeletons from L2R problem descriptions in background

# Get script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
source .venv/bin/activate

# Create log directory
LOG_DIR="logs/datagen/skeleton_l2r"
mkdir -p "$LOG_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/generation_${TIMESTAMP}.log"
PID_FILE="$LOG_DIR/generation.pid"

# Run in background with nohup
nohup python scripts/datagen/generate_skeletons.py --source l2r > "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"
echo "Started skeleton generation (L2R mode) in background"
echo "PID: $(cat $PID_FILE)"
echo "Log: $LOG_FILE"

