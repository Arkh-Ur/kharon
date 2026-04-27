"""
Client Alpha Data Extraction Script

This script simulates data extraction from Client Alpha source systems.
It mimics ETL extraction processes and outputs results in Kharōn format.

Author: Kharōn Orchestration Platform
Client: Client Alpha
Purpose: ETL Data Extraction
Version: 1.0
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List


def log_progress(message: str):
    """Log progress message with Kharōn prefix."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[Kharōn] {timestamp} - {message}")


def simulate_database_connection():
    """Simulate connecting to Client Alpha database."""
    log_progress("Connecting to Client Alpha database...")
    time.sleep(2)  # Simulate connection time
    
    # Simulate connection success/failure
    if random.random() > 0.1:  # 90% success rate
        log_progress("Database connection established successfully")
        return True
    else:
        log_progress("ERROR: Failed to connect to database")
        return False


def simulate_data_extraction():
    """Simulate extracting data from various source tables."""
    log_progress("Starting data extraction process...")
    
    # Define Client Alpha source tables
    source_tables = [
        "customers",
        "orders", 
        "products",
        "inventory",
        "transactions"
    ]
    
    extracted_data = {}
    total_records = 0
    
    for table in source_tables:
        log_progress(f"Extracting data from {table} table...")
        time.sleep(1)  # Simulate extraction time
        
        # Simulate record counts
        if table == "customers":
            record_count = 1500
        elif table == "orders":
            record_count = 8500
        elif table == "products":
            record_count = 2500
        elif table == "inventory":
            record_count = 3200
        else:  # transactions
            record_count = 12500
        
        total_records += record_count
        
        # Generate mock data
        mock_records = []
        for i in range(min(record_count, 100)):  # Limit mock data generation
            record = {
                "id": f"{table}_{i:06d}",
                "table_name": table,
                "extracted_at": datetime.now().isoformat(),
                "data_quality": "good" if random.random() > 0.05 else "needs_review"
            }
            mock_records.append(record)
        
        extracted_data[table] = {
            "records_extracted": record_count,
            "sample_records": mock_records[:5],  # Include first 5 records as sample
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        log_progress(f"Extracted {record_count} records from {table}")
    
    return extracted_data, total_records


def simulate_data_validation(extracted_data: Dict[str, Any], total_records: int):
    """Simulate data validation and quality checks."""
    log_progress("Performing data validation...")
    time.sleep(2)
    
    validation_results = {
        "total_records": total_records,
        "valid_records": int(total_records * 0.98),  # 98% validation rate
        "invalid_records": int(total_records * 0.02),
        "tables_validated": len(extracted_data),
        "validation_timestamp": datetime.now().isoformat()
    }
    
    # Add validation warnings for demo
    if validation_results["invalid_records"] > 0:
        log_progress(f"WARNING: Found {validation_results['invalid_records']} invalid records")
    
    log_progress("Data validation completed successfully")
    return validation_results


def create_output_files(extracted_data: Dict[str, Any], validation_results: Dict[str, Any]):
    """Create output files for the extracted data."""
    log_progress("Creating output files...")
    time.sleep(1)
    
    output_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create main extraction file
    extraction_summary = {
        "extraction_id": f"alpha_extraction_{timestamp}",
        "client_id": "client_alpha",
        "extraction_timestamp": datetime.now().isoformat(),
        "source_systems": ["primary_db", "backup_db", "api_endpoints"],
        "tables_extracted": list(extracted_data.keys()),
        "total_records": validation_results["total_records"],
        "validation_results": validation_results,
        "data_files": []
    }
    
    # Create individual table files (mock)
    for table in extracted_data.keys():
        table_file = f"client_alpha_{table}_{timestamp}.json"
        output_files.append(table_file)
        
        # Mock file creation
        table_data = {
            "filename": table_file,
            "table_name": table,
            "records_count": extracted_data[table]["records_extracted"],
            "creation_timestamp": datetime.now().isoformat(),
            "file_size_mb": round(extracted_data[table]["records_extracted"] * 0.001, 2)  # Mock file size
        }
        
        extraction_summary["data_files"].append(table_file)
        log_progress(f"Created output file: {table_file}")
    
    # Create summary file
    summary_file = f"client_alpha_extraction_summary_{timestamp}.json"
    output_files.append(summary_file)
    
    log_progress(f"Created summary file: {summary_file}")
    
    return output_files, extraction_summary


def generate_final_result(extracted_data: Dict[str, Any], validation_results: Dict[str, Any], 
                         output_files: List[str], extraction_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final result in JSON format."""
    duration = time.time() - start_time
    
    result = {
        "task_name": "extract_client_alpha",
        "client_id": "client_alpha",
        "description": "Extract data from Client Alpha source systems",
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "extraction_metadata": {
            "source_systems": ["primary_db", "backup_db", "api_endpoints"],
            "tables_processed": list(extracted_data.keys()),
            "total_records_extracted": validation_results["total_records"],
            "valid_records": validation_results["valid_records"],
            "invalid_records": validation_results["invalid_records"]
        },
        "output_files": output_files,
        "performance_metrics": {
            "extraction_rate_records_per_second": round(validation_results["total_records"] / duration, 2),
            "processing_time_seconds": round(duration, 2),
            "memory_usage_mb": 128  # Mock memory usage
        },
        "warnings": [],
        "errors": [],
        "next_steps": [
            "Data transformation (transform_sales)",
            "Data loading to warehouse (load_warehouse)",
            "Quality assurance review"
        ],
        "execution_details": {
            "python_version": "3.9.0",
            "start_time": start_time_iso,
            "completion_time": datetime.now().isoformat(),
            "operator": "arkh-ur"
        }
    }
    
    # Add warnings if any issues encountered
    if validation_results["invalid_records"] > 100:
        result["warnings"].append(f"High number of invalid records: {validation_results['invalid_records']}")
    
    return result


if __name__ == "__main__":
    # Record start time
    start_time = time.time()
    start_time_iso = datetime.fromtimestamp(start_time).isoformat()
    
    try:
        log_progress("Starting Client Alpha data extraction task")
        log_progress(f"Task ID: extract_client_alpha")
        log_progress(f"Client: Client Alpha")
        log_progress(f"Start time: {start_time_iso}")
        
        # Step 1: Connect to database
        if not simulate_database_connection():
            raise Exception("Failed to connect to Client Alpha database")
        
        # Step 2: Extract data
        extracted_data, total_records = simulate_data_extraction()
        
        # Step 3: Validate data
        validation_results = simulate_data_validation(extracted_data, total_records)
        
        # Step 4: Create output files
        output_files, extraction_summary = create_output_files(extracted_data, validation_results)
        
        # Step 5: Generate final result
        result = generate_final_result(extracted_data, validation_results, output_files, extraction_summary)
        
        # Log completion
        log_progress("Client Alpha data extraction completed successfully")
        log_progress(f"Total records extracted: {total_records}")
        log_progress(f"Output files created: {len(output_files)}")
        log_progress(f"Execution time: {result['duration_seconds']} seconds")
        
        # Output result in Kharōn format
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit successfully
        exit(0)
        
    except Exception as e:
        log_progress(f"ERROR: Client Alpha data extraction failed: {str(e)}")
        
        # Generate error result
        error_result = {
            "task_name": "extract_client_alpha",
            "client_id": "client_alpha",
            "description": "Extract data from Client Alpha source systems",
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(time.time() - start_time, 2),
            "error": str(e),
            "errors": [str(e)],
            "output_files": [],
            "next_steps": ["Investigate connection issues", "Retry extraction"]
        }
        
        result_json = json.dumps(error_result, indent=2, ensure_ascii=False)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit with error
        exit(1)