#!/bin/bash
# Script to generate function implementations from L2R skeletons in background

# Get script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
source .venv/bin/activate

# Create log directory
LOG_DIR="logs/datagen/codegen_l2r"
mkdir -p "$LOG_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/generation_${TIMESTAMP}.log"
PID_FILE="$LOG_DIR/generation.pid"

# Run in background (output handled by Python logger)
nohup python scripts/datagen/generate_code.py --source l2r "$@" > /dev/null 2>&1 &

# Save PID
PID=$!
echo $PID > "$PID_FILE"
echo "Started code generation (L2R mode) in background"
echo "PID: $PID"
echo "Logs will be in: $LOG_DIR/"
echo "Monitor: ls -lht $LOG_DIR/ | head"

