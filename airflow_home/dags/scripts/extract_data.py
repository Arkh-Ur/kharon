"""
Kharōn Python Task Template

This is a template Python script for Kharōn orchestration platform.
It demonstrates proper progress reporting and JSON result output format.

Usage: python extract_data.py [source_type] [output_format]
Example: python extract_data.py "database" "csv"

Author: Kharōn Orchestration Platform
Version: 1.0
"""

import sys
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List


class KharonTask:
    """Base class for Kharōn orchestration tasks."""
    
    def __init__(self, task_name: str, description: str):
        self.task_name = task_name
        self.description = description
        self.start_time = datetime.now()
        self.steps_completed = 0
        self.errors = []
        self.warnings = []
        
    def log_progress(self, message: str):
        """Log progress message with Kharōn prefix."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[Kharōn] {timestamp} - {message}")
        
    def log_step(self, step_number: int, step_name: str):
        """Log task step completion."""
        self.steps_completed += 1
        self.log_progress(f"Step {step_number}: {step_name}")
        
    def add_error(self, error_message: str):
        """Add error to the task."""
        self.errors.append(error_message)
        self.log_progress(f"ERROR: {error_message}")
        
    def add_warning(self, warning_message: str):
        """Add warning to the task."""
        self.warnings.append(warning_message)
        self.log_progress(f"WARNING: {warning_message}")
        
    def generate_result(self) -> Dict[str, Any]:
        """Generate task result in JSON format."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        result = {
            "task_name": self.task_name,
            "description": self.description,
            "status": "success" if not self.errors else "failed",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "warnings": self.warnings,
            "input_parameters": {
                "source_type": getattr(self, 'source_type', 'unknown'),
                "output_format": getattr(self, 'output_format', 'unknown')
            },
            "output_files": getattr(self, 'output_files', []),
            "data_records_processed": getattr(self, 'records_processed', 0),
            "execution_metadata": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "start_time": self.start_time.isoformat()
            }
        }
        
        return result


def main():
    """Main execution function."""
    
    # Get task parameters
    task_name = "data_extraction"
    source_type = sys.argv[1] if len(sys.argv) > 1 else "database"
    output_format = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    # Create task instance
    task = KharonTask(task_name, f"Extract data from {source_type} in {output_format} format")
    task.source_type = source_type
    task.output_format = output_format
    
    try:
        # Initialize task
        task.log_progress(f"Starting data extraction task")
        task.log_progress(f"Source: {source_type}")
        task.log_progress(f"Output format: {output_format}")
        task.log_progress(f"Timestamp: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Connect to source
        task.log_step(1, "Connecting to data source")
        time.sleep(2)  # Simulate connection time
        
        if source_type == "database":
            task.log_progress("Connected to database successfully")
            task.records_processed = 1000  # Mock data
        elif source_type == "file":
            task.log_progress("Connected to file source successfully")
            task.records_processed = 500  # Mock data
        else:
            task.add_warning(f"Unknown source type: {source_type}")
            task.records_processed = 0
        
        # Step 2: Extract data
        task.log_step(2, "Extracting data records")
        
        # Simulate data extraction
        for batch in range(1, 4):  # 3 batches
            task.log_progress(f"Extracting batch {batch}/3")
            time.sleep(1)  # Simulate extraction time
            
            # Add some mock data processing
            if batch == 2 and source_type == "database":
                task.add_warning("Encountered null values in batch 2, applying default values")
        
        task.log_progress(f"Data extraction complete. Total records: {task.records_processed}")
        
        # Step 3: Transform data
        task.log_step(3, "Applying data transformations")
        time.sleep(1)  # Simulate transformation
        
        # Apply basic transformations
        if output_format == "csv":
            task.log_progress("Applied CSV-specific transformations")
        elif output_format == "json":
            task.log_progress("Applied JSON-specific transformations")
        elif output_format == "parquet":
            task.log_progress("Applied Parquet-specific transformations")
        
        # Step 4: Validate data
        task.log_step(4, "Validating extracted data")
        time.sleep(1)  # Simulate validation
        
        # Mock validation results
        validation_passed = True
        if task.records_processed == 0:
            validation_passed = False
            task.add_error("No records extracted")
        
        if validation_passed:
            task.log_progress("Data validation passed")
        else:
            task.add_error("Data validation failed")
        
        # Step 5: Save output
        task.log_step(5, "Saving output files")
        time.sleep(1)  # Simulate file writing
        
        # Create output files
        output_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format in ["json", "csv"]:
            filename = f"extracted_data_{timestamp}.{output_format}"
            output_files.append(filename)
            task.log_progress(f"Created output file: {filename}")
        else:
            task.add_warning(f"Output format {output_format} not supported, using JSON")
            filename = f"extracted_data_{timestamp}.json"
            output_files.append(filename)
            task.log_progress(f"Created output file: {filename}")
        
        task.output_files = output_files
        
        # Step 6: Generate summary
        task.log_step(6, "Generating extraction summary")
        
        summary = {
            "total_records": task.records_processed,
            "valid_records": task.records_processed - len(task.errors),
            "invalid_records": len(task.errors),
            "output_files": len(output_files),
            "processing_time": round((datetime.now() - task.start_time).total_seconds(), 2)
        }
        
        task.log_progress(f"Extraction summary: {json.dumps(summary, indent=2)}")
        
        # Generate final result
        result = task.generate_result()
        
        # Output final result
        task.log_progress("Task execution completed successfully")
        result_json = json.dumps(result, indent=2)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        task.add_error(f"Task failed with exception: {str(e)}")
        result = task.generate_result()
        
        task.log_progress("Task execution failed")
        result_json = json.dumps(result, indent=2)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit with error
        sys.exit(1)


if __name__ == "__main__":
    main()