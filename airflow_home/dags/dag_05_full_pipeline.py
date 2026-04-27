"""
Kharōn DAG - Full ETL Pipeline

This DAG orchestrates the complete ETL pipeline by chaining together
extract >> transform >> load operations for Client Alpha.

Pipeline Flow:
1. extract_client_alpha: Extract data from source systems
2. transform_sales: Transform and clean the extracted data
3. load_warehouse: Load processed data into data warehouse

Author: Kharōn Orchestration Platform
Version: 1.0
"""

from datetime import datetime, timedelta
from airflow import DAG
from operators.kharon_operator import KharonOperator

# Default arguments for all Kharōn DAGs
default_args = {
    'owner': 'arkh-ur',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG instance
dag = DAG(
    dag_id='kharon_full_pipeline',
    default_args=default_args,
    description='Complete ETL pipeline: extract >> transform >> load for Client Alpha',
    schedule='0 6 * * *',  # Daily at 6 AM UTC (follows extract schedule)
    max_active_runs=1,
    tags=['kharon-auto', 'etl', 'pipeline', 'client_alpha'],
    catchup=False,
)

# Create pipeline tasks using KharonOperator
extract_client_alpha_task = KharonOperator(
    task_id='extract_client_alpha',
    script_path='/opt/kharon/scripts_externos/etl/extract_alpha.py',
    script_id='extract_client_alpha',
    dag=dag,
)

transform_sales_task = KharonOperator(
    task_id='transform_sales',
    script_path='/opt/kharon/scripts_externos/etl/transform_sales.py',
    script_id='transform_sales',
    dag=dag,
)

load_warehouse_task = KharonOperator(
    task_id='load_warehouse',
    script_path='/opt/kharon/scripts_externos/etl/load_warehouse.py',
    script_id='load_warehouse',
    dag=dag,
)

# Define task dependencies: extract -> transform -> load
extract_client_alpha_task >> transform_sales_task >> load_warehouse_task