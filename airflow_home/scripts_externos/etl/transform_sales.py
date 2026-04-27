"""
Client Beta Sales Data Transformation Script

This script simulates data transformation for Client Beta sales data.
It processes extracted data, applies business rules, and prepares
data for loading into the data warehouse.

Author: Kharōn Orchestration Platform
Client: Client Beta
Purpose: ETL Data Transformation
Version: 1.0
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal


def log_progress(message: str):
    """Log progress message with Kharōn prefix."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[Kharōn] {timestamp} - {message}")


def load_extracted_data():
    """Load mock extracted data from Client Beta."""
    log_progress("Loading extracted data for transformation...")
    time.sleep(1)
    
    # Mock extracted data structure
    mock_data = {
        "customers": [
            {
                "id": "cust_001",
                "name": "Acme Corporation",
                "email": "acme@example.com",
                "registration_date": "2023-01-15",
                "status": "active",
                "segment": "enterprise"
            } for _ in range(100)
        ],
        "orders": [
            {
                "id": f"ord_{i:06d}",
                "customer_id": f"cust_{(i % 10) + 1:03d}",
                "order_date": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                "total_amount": round(random.uniform(100, 5000), 2),
                "status": random.choice(["completed", "pending", "cancelled"]),
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"])
            } for i in range(500)
        ],
        "products": [
            {
                "id": f"prod_{i:04d}",
                "name": f"Product {i+1}",
                "category": random.choice(["electronics", "clothing", "books", "home"]),
                "price": round(random.uniform(10, 1000), 2),
                "sku": f"SKU-{i:06d}",
                "inventory_count": random.randint(0, 1000)
            } for i in range(50)
        ]
    }
    
    log_progress(f"Loaded {len(mock_data['customers'])} customers")
    log_progress(f"Loaded {len(mock_data['orders'])} orders")
    log_progress(f"Loaded {len(mock_data['products'])} products")
    
    return mock_data


def apply_business_rules(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply business transformation rules to the data."""
    log_progress("Applying business transformation rules...")
    time.sleep(2)
    
    transformed_data = {
        "customers": [],
        "orders": [],
        "order_items": [],
        "aggregates": {}
    }
    
    # Transform customers
    log_progress("Transforming customer data...")
    for customer in data["customers"]:
        transformed_customer = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "email_address": customer["email"].lower(),
            "registration_date": customer["registration_date"],
            "customer_status": customer["status"],
            "customer_segment": customer["segment"],
            "processing_timestamp": datetime.now().isoformat(),
            "data_quality_score": 95  # Mock quality score
        }
        transformed_data["customers"].append(transformed_customer)
    
    # Transform orders and create order items
    log_progress("Transforming order data...")
    order_items_counter = 0
    
    for order in data["orders"]:
        # Transform order
        transformed_order = {
            "order_id": order["id"],
            "customer_id": order["customer_id"],
            "order_date": order["order_date"],
            "order_total": Decimal(str(order["total_amount"])),
            "order_status": order["status"],
            "payment_method": order["payment_method"],
            "order_processing_timestamp": datetime.now().isoformat(),
            "currency": "USD"
        }
        transformed_data["orders"].append(transformed_order)
        
        # Generate order items (simulate multiple items per order)
        num_items = random.randint(1, 5)
        for item_num in range(num_items):
            product_id = f"prod_{(order_items_counter % 50) + 1:04d}"
            
            order_item = {
                "order_id": order["id"],
                "item_id": f"item_{order_items_counter + 1:08d}",
                "product_id": product_id,
                "quantity": random.randint(1, 10),
                "unit_price": Decimal(str(random.uniform(10, 100))),
                "item_total": Decimal(str(random.uniform(10, 1000))),
                "discount_amount": Decimal("0.00"),  # Mock discount
                "processing_timestamp": datetime.now().isoformat()
            }
            transformed_data["order_items"].append(order_item)
            order_items_counter += 1
    
    # Generate aggregates
    log_progress("Generating business aggregates...")
    total_orders = len(transformed_data["orders"])
    total_revenue = sum(float(order["order_total"]) for order in transformed_data["orders"])
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    transformed_data["aggregates"] = {
        "total_orders_processed": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(avg_order_value, 2),
        "active_customers": len(transformed_data["customers"]),
        "total_order_items": len(transformed_data["order_items"]),
        "processing_date": datetime.now().strftime('%Y-%m-%d')
    }
    
    log_progress(f"Transformed {len(transformed_data['customers'])} customers")
    log_progress(f"Transformed {len(transformed_data['orders'])} orders")
    log_progress(f"Generated {len(transformed_data['order_items'])} order items")
    
    return transformed_data


def apply_data_quality_checks(transformed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply data quality validation and generate quality metrics."""
    log_progress("Applying data quality checks...")
    time.sleep(1)
    
    quality_results = {
        "customer_quality": {
            "total_records": len(transformed_data["customers"]),
            "valid_records": len(transformed_data["customers"]),
            "invalid_records": 0,
            "completeness_score": 100,
            "consistency_score": 100
        },
        "order_quality": {
            "total_records": len(transformed_data["orders"]),
            "valid_records": len(transformed_data["orders"]),
            "invalid_records": 0,
            "completeness_score": 100,
            "consistency_score": 100
        },
        "order_item_quality": {
            "total_records": len(transformed_data["order_items"]),
            "valid_records": len(transformed_data["order_items"]),
            "invalid_records": 0,
            "completeness_score": 100,
            "consistency_score": 100
        }
    }
    
    # Add some mock quality issues for demonstration
    if random.random() > 0.8:  # 20% chance of quality issues
        log_progress("WARNING: Detected minor data quality issues")
        quality_results["order_quality"]["invalid_records"] = random.randint(1, 5)
        quality_results["order_quality"]["completeness_score"] = 98
    
    overall_quality = sum([
        q["completeness_score"] + q["consistency_score"]
        for q in quality_results.values()
    ]) / (len(quality_results) * 2)
    
    quality_results["overall_quality_score"] = round(overall_quality, 2)
    quality_results["validation_timestamp"] = datetime.now().isoformat()
    
    log_progress(f"Overall data quality score: {overall_quality:.1f}%")
    
    return quality_results


def create_transformed_output(transformed_data: Dict[str, Any], 
                             quality_results: Dict[str, Any]) -> List[str]:
    """Create output files with transformed data."""
    log_progress("Creating transformed output files...")
    time.sleep(1)
    
    output_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create customer output file
    customer_file = f"client_beta_customers_{timestamp}.json"
    with open(customer_file, 'w') as f:
        json.dump({
            "metadata": {
                "file_type": "customer_data",
                "client_id": "client_beta",
                "generation_timestamp": datetime.now().isoformat(),
                "record_count": len(transformed_data["customers"])
            },
            "data": transformed_data["customers"]
        }, f, indent=2, default=str)
    output_files.append(customer_file)
    
    # Create order output file
    order_file = f"client_beta_orders_{timestamp}.json"
    with open(order_file, 'w') as f:
        json.dump({
            "metadata": {
                "file_type": "order_data",
                "client_id": "client_beta",
                "generation_timestamp": datetime.now().isoformat(),
                "record_count": len(transformed_data["orders"])
            },
            "data": transformed_data["orders"]
        }, f, indent=2, default=str)
    output_files.append(order_file)
    
    # Create order items output file
    order_items_file = f"client_beta_order_items_{timestamp}.json"
    with open(order_items_file, 'w') as f:
        json.dump({
            "metadata": {
                "file_type": "order_item_data",
                "client_id": "client_beta",
                "generation_timestamp": datetime.now().isoformat(),
                "record_count": len(transformed_data["order_items"])
            },
            "data": transformed_data["order_items"]
        }, f, indent=2, default=str)
    output_files.append(order_items_file)
    
    # Create aggregates output file
    aggregates_file = f"client_beta_sales_aggregates_{timestamp}.json"
    with open(aggregates_file, 'w') as f:
        json.dump({
            "metadata": {
                "file_type": "business_aggregates",
                "client_id": "client_beta",
                "generation_timestamp": datetime.now().isoformat()
            },
            "data": transformed_data["aggregates"]
        }, f, indent=2, default=str)
    output_files.append(aggregates_file)
    
    # Create quality report file
    quality_file = f"client_beta_data_quality_{timestamp}.json"
    with open(quality_file, 'w') as f:
        json.dump({
            "metadata": {
                "file_type": "data_quality_report",
                "client_id": "client_beta",
                "generation_timestamp": datetime.now().isoformat()
            },
            "data": quality_results
        }, f, indent=2, default=str)
    output_files.append(quality_file)
    
    log_progress(f"Created {len(output_files)} output files")
    return output_files


def generate_transformation_result(transformed_data: Dict[str, Any], 
                                   quality_results: Dict[str, Any],
                                   output_files: List[str]) -> Dict[str, Any]:
    """Generate final transformation result."""
    duration = time.time() - start_time
    
    result = {
        "task_name": "transform_sales",
        "client_id": "client_beta",
        "description": "Transform sales data for Client Beta ETL pipeline",
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "transformation_metrics": {
            "customers_processed": len(transformed_data["customers"]),
            "orders_processed": len(transformed_data["orders"]),
            "order_items_processed": len(transformed_data["order_items"]),
            "business_aggregates_generated": len(transformed_data["aggregates"]),
            "processing_rate_records_per_second": round(
                (len(transformed_data["customers"]) + 
                 len(transformed_data["orders"]) + 
                 len(transformed_data["order_items"])) / duration, 2
            )
        },
        "data_quality": quality_results,
        "output_files": output_files,
        "performance_metrics": {
            "transformation_time_seconds": round(duration, 2),
            "memory_usage_mb": 256,  # Mock memory usage
            "cpu_utilization_percent": 45  # Mock CPU usage
        },
        "business_rules_applied": [
            "Customer data standardization",
            "Order status normalization", 
            "Order item generation",
            "Revenue calculation",
            "Data validation"
        ],
        "warnings": [],
        "errors": [],
        "next_steps": [
            "Load data to warehouse (load_warehouse)",
            "Generate sales reports",
            "Update business dashboards"
        ],
        "execution_details": {
            "python_version": "3.9.0",
            "start_time": start_time_iso,
            "completion_time": datetime.now().isoformat(),
            "operator": "arkh-ur"
        }
    }
    
    return result


if __name__ == "__main__":
    # Record start time
    start_time = time.time()
    start_time_iso = datetime.fromtimestamp(start_time).isoformat()
    
    try:
        log_progress("Starting Client Beta sales data transformation")
        log_progress(f"Task ID: transform_sales")
        log_progress(f"Client: Client Beta")
        log_progress(f"Start time: {start_time_iso}")
        
        # Step 1: Load extracted data
        extracted_data = load_extracted_data()
        
        # Step 2: Apply business transformation rules
        transformed_data = apply_business_rules(extracted_data)
        
        # Step 3: Apply data quality checks
        quality_results = apply_data_quality_checks(transformed_data)
        
        # Step 4: Create transformed output files
        output_files = create_transformed_output(transformed_data, quality_results)
        
        # Step 5: Generate final result
        result = generate_transformation_result(transformed_data, quality_results, output_files)
        
        # Log completion
        log_progress("Client Beta sales data transformation completed successfully")
        log_progress(f"Customers processed: {result['transformation_metrics']['customers_processed']}")
        log_progress(f"Orders processed: {result['transformation_metrics']['orders_processed']}")
        log_progress(f"Output files created: {len(output_files)}")
        log_progress(f"Execution time: {result['duration_seconds']} seconds")
        log_progress(f"Data quality score: {result['data_quality']['overall_quality_score']}%")
        
        # Output result in Kharōn format
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit successfully
        exit(0)
        
    except Exception as e:
        log_progress(f"ERROR: Client Beta sales data transformation failed: {str(e)}")
        
        # Generate error result
        error_result = {
            "task_name": "transform_sales",
            "client_id": "client_beta",
            "description": "Transform sales data for Client Beta ETL pipeline",
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(time.time() - start_time, 2),
            "error": str(e),
            "errors": [str(e)],
            "output_files": [],
            "next_steps": ["Investigate transformation issues", "Retry with data validation"]
        }
        
        result_json = json.dumps(error_result, indent=2, ensure_ascii=False)
        print(f"[Kharōn] RESULT: {result_json}")
        
        # Exit with error
        exit(1)