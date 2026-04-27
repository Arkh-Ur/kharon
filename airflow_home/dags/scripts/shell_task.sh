#!/bin/bash

"""
Kharōn Shell Task Template

This is a template shell script for Kharōn orchestration platform.
It demonstrates proper progress reporting and JSON result output format.

Usage: ./shell_task.sh [task_name] [description]
Example: ./shell_task.sh "data_cleanup" "Cleaning up old log files"

Author: Kharōn Orchestration Platform
Version: 1.0
"""

# Set error handling
set -e

# Get task parameters
TASK_NAME="${1:-unknown_task}"
DESCRIPTION="${2:-No description provided}"

# Print initial status
echo "[Kharōn] Starting task: $TASK_NAME"
echo "[Kharōn] Description: $DESCRIPTION"
echo "[Kharōn] Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Function to log progress
log_progress() {
    echo "[Kharōn] Progress: $1"
}

# Function to log step
log_step() {
    step_number=$1
    step_name=$2
    echo "[Kharōn] Step $step_number: $step_name"
}

# Main task execution
log_progress "Initializing task environment"

# Step 1: Setup
log_step 1 "Setting up environment"
mkdir -p /tmp/kharon_work
cd /tmp/kharon_work
log_progress "Environment setup complete"

# Step 2: Task execution
log_step 2 "Executing main task logic"
log_progress "Processing task-specific operations"

# Simulate some work
for i in {1..5}; do
    log_progress "Processing item $i/5"
    sleep 1  # Simulate work
done

log_progress "Main task logic complete"

# Step 3: Validation
log_step 3 "Validating results"
log_progress "Checking output files and data integrity"

# Check if work was completed successfully
if [ -f "/tmp/kharon_work/completed.flag" ]; then
    log_progress "Validation successful"
else
    log_progress "Validation warning: No completion flag found"
    touch "/tmp/kharon_work/completed.flag"
fi

# Step 4: Cleanup
log_step 4 "Performing cleanup operations"
log_progress "Removing temporary files"

# Clean up temporary files
rm -rf /tmp/kharon_work
log_progress "Cleanup complete"

# Step 5: Generate results
log_step 5 "Generating final results"

# Create JSON result object
RESULT_JSON=$(cat <<EOF
{
    "task_name": "$TASK_NAME",
    "description": "$DESCRIPTION",
    "status": "success",
    "timestamp": "$(date '+%Y-%m-%d %H:%M:%S')",
    "duration_seconds": 5,
    "steps_completed": 5,
    "output_files": [],
    "warnings": [],
    "errors": []
}
EOF
)

# Output the final result
echo "[Kharōn] Task execution completed successfully"
echo "[Kharōn] RESULT: $RESULT_JSON"

# Exit successfully
exit 0