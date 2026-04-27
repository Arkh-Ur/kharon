#!/bin/bash

"""
Client Gamma Log Cleanup Script

This script simulates log cleanup operations for Client Gamma systems.
It removes old log files, temporary files, and manages disk space.

Author: Kharōn Orchestration Platform
Client: Client Gamma
Purpose: Maintenance Log Cleanup
Version: 1.0
"""

# Set error handling
set -e

# Function to log progress with Kharōn prefix
log_progress() {
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[Kharōn] $timestamp - $1"
}

# Function to log step completion
log_step() {
    step_number=$1
    step_name=$2
    echo "[Kharōn] Step $step_number: $step_name"
}

# Function to cleanup old log files
cleanup_old_logs() {
    log_step 1 "Cleaning up old log files"
    
    # Define log directories
    log_directories=(
        "/var/log/kharon"
        "/tmp/kharon_logs"
        "/home/kharon/logs"
        "/var/log/applications"
    )
    
    total_files_removed=0
    total_space_freed=0
    
    for log_dir in "${log_directories[@]}"; do
        if [ -d "$log_dir" ]; then
            log_progress "Checking log directory: $log_dir"
            
            # Find and remove log files older than 30 days
            if find "$log_dir" -name "*.log" -type f -mtime +30 -print -delete | grep -q .; then
                files_removed=$(find "$log_dir" -name "*.log" -type f -mtime +30 | wc -l)
                space_freed=$(du -sh "$log_dir" 2>/dev/null | cut -f1 || echo "unknown")
                
                total_files_removed=$((total_files_removed + files_removed))
                log_progress "Removed $files_removed log files from $log_dir"
                
                if [ "$space_freed" != "unknown" ]; then
                    total_space_freed=$((total_space_freed + $(echo $space_freed | sed 's/[A-Z]//')))
                fi
            else
                log_progress "No old log files found in $log_dir"
            fi
        else
            log_progress "Log directory does not exist: $log_dir"
        fi
    done
    
    log_progress "Log cleanup completed. Removed $total_files_removed files."
}

# Function to cleanup temporary files
cleanup_temp_files() {
    log_step 2 "Cleaning up temporary files"
    
    # Define temporary directories
    temp_directories=(
        "/tmp"
        "/var/tmp"
        "/tmp/kharon_work"
        "/tmp/*kharon*"
    )
    
    temp_files_found=0
    
    for temp_dir in "${temp_directories[@]}"; do
        if [ -d "$temp_dir" ]; then
            log_progress "Checking temporary directory: $temp_dir"
            
            # Find and remove temporary files older than 7 days
            if find "$temp_dir" -name "*.tmp" -o -name "*.temp" -o -name "*kharon*" -type f -mtime +7 -print -delete | grep -q .; then
                files_removed=$(find "$temp_dir" \( -name "*.tmp" -o -name "*.temp" -o -name "*kharon*" \) -type f -mtime +7 | wc -l)
                temp_files_found=$((temp_files_found + files_removed))
                log_progress "Removed $files_removed temporary files from $temp_dir"
            else
                log_progress "No temporary files found in $temp_dir"
            fi
        fi
    done
    
    log_progress "Temporary files cleanup completed. Removed $temp_files_found files."
}

# Function to rotate log files
rotate_logs() {
    log_step 3 "Rotating log files"
    
    log_directories=(
        "/var/log/kharon"
        "/home/kharon/logs"
    )
    
    for log_dir in "${log_directories[@]}"; do
        if [ -d "$log_dir" ]; then
            log_progress "Rotating logs in: $log_dir"
            
            # Create archive directory
            archive_dir="$log_dir/archive/$(date +%Y%m)"
            mkdir -p "$archive_dir"
            
            # Move large log files to archive
            find "$log_dir" -name "*.log" -size +10M -exec mv {} "$archive_dir/" \;
            
            # Compress archived logs
            if [ -n "$(find "$archive_dir" -name "*.log" -print -quit)" ]; then
                log_progress "Compressing archived logs"
                find "$archive_dir" -name "*.log" -exec gzip {} \;
            fi
            
            # Count archived files
            archived_count=$(find "$archive_dir" -name "*.log.gz" | wc -l)
            log_progress "Archived $archived_count log files"
        else
            log_progress "Log directory does not exist: $log_dir"
        fi
    done
}

# Function to check disk space
check_disk_space() {
    log_step 4 "Checking disk space"
    
    # Check disk usage on mounted filesystems
    df -h | grep -E '^/dev/' | while read filesystem size used avail use_mount point; do
        usage_percent=$(echo $use_mount | tr -d '%')
        
        if [ "$usage_percent" -gt 80 ]; then
            log_progress "WARNING: High disk usage on $filesystem: ${use_mount}%"
        else
            log_progress "Disk usage OK on $filesystem: ${use_mount}%"
        fi
    done
    
    # Clean up if disk usage is very high
    if df -h | grep -E '^/dev/' | awk '{print $5}' | tr -d '%' | grep -q '[8-9][0-9]'; then
        log_progress "Disk usage critical, performing emergency cleanup"
        
        find /tmp -type f -mtime +1 -delete
        find /var/tmp -type f -mtime +1 -delete
        
        log_progress "Emergency cleanup completed"
    fi
}

# Function to generate cleanup report
generate_report() {
    log_step 5 "Generating cleanup report"
    
    # Generate JSON report
    report=$(cat <<EOF
{
    "cleanup_id": "gamma_cleanup_$(date +%Y%m%d_%H%M%S)",
    "client_id": "client_gamma",
    "cleanup_timestamp": "$(date -Iseconds)",
    "operations_performed": [
        "old_log_files_removal",
        "temporary_files_cleanup", 
        "log_rotation",
        "disk_space_check"
    ],
    "files_removed": $total_files_removed,
    "directories_processed": 4,
    "disk_space_checked": true,
    "cleanup_status": "success",
    "next_maintenance": "$(date -d '+7 days' -Iseconds)"
}
EOF
)
    
    # Save report to file
    report_file="/tmp/kharon_cleanup_report_$(date +%Y%m%d_%H%M%S).json"
    echo "$report" > "$report_file"
    log_progress "Cleanup report saved to: $report_file"
    
    echo "$report"
}

# Main execution
main() {
    # Record start time
    start_time=$(date +%s)
    
    log_progress "Starting Client Gamma log cleanup task"
    log_progress "Task ID: cleanup_logs"
    log_progress "Client: Client Gamma"
    log_progress "Start time: $(date -Iseconds)"
    
    try {
        # Step 1: Cleanup old log files
        cleanup_old_logs
        
        # Step 2: Cleanup temporary files
        cleanup_temp_files
        
        # Step 3: Rotate logs
        rotate_logs
        
        # Step 4: Check disk space
        check_disk_space
        
        # Step 5: Generate report
        cleanup_report=$(generate_report)
        
        # Calculate duration
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        # Generate final result
        result=$(cat <<EOF
{
    "task_name": "cleanup_logs",
    "client_id": "client_gamma",
    "description": "Cleanup log files and temporary files for Client Gamma",
    "status": "success",
    "timestamp": "$(date -Iseconds)",
    "duration_seconds": $duration,
    "cleanup_summary": $cleanup_report,
    "performance_metrics": {
        "total_files_removed": $total_files_removed,
        "cleanup_rate_files_per_second": $(echo "scale=2; $total_files_removed / $duration" | bc),
        "processing_time_seconds": $duration
    },
    "maintenance_actions": [
        "Old log file removal",
        "Temporary file cleanup",
        "Log rotation",
        "Disk space management"
    ],
    "warnings": [],
    "errors": [],
    "output_files": ["$report_file"],
    "next_steps": [
        "Schedule next maintenance run",
        "Monitor disk space trends",
        "Update retention policies"
    ],
    "execution_details": {
        "script_type": "shell",
        "bash_version": "$BASH_VERSION",
        "start_time": "$(date -d "@$start_time" -Iseconds)",
        "completion_time": "$(date -Iseconds)",
        "operator": "arkh-ur"
    }
}
EOF
)
        
        # Log completion
        log_progress "Client Gamma log cleanup completed successfully"
        log_progress "Total files removed: $total_files_removed"
        log_progress "Execution time: $duration seconds"
        
        # Output result in Kharōn format
        echo "[Kharōn] RESULT: $result"
        
        # Exit successfully
        exit 0
        
    } catch {
        log_progress "ERROR: Client Gamma log cleanup failed"
        
        # Generate error result
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        error_result=$(cat <<EOF
{
    "task_name": "cleanup_logs",
    "client_id": "client_gamma", 
    "description": "Cleanup log files and temporary files for Client Gamma",
    "status": "failed",
    "timestamp": "$(date -Iseconds)",
    "duration_seconds": $duration,
    "error": "$1",
    "errors": ["$1"],
    "output_files": [],
    "next_steps": ["Investigate filesystem issues", "Retry cleanup with elevated privileges"]
}
EOF
)
        
        echo "[Kharōn] RESULT: $error_result"
        
        # Exit with error
        exit 1
    }
}

# Execute main function
main "$@"