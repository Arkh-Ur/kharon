"""
Kharōn DAG - Data Warehouse Loading

This DAG executes the load_warehouse script to load transformed data into the
data warehouse for Client Alpha ETL operations.

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
    dag_id='kharon_load',
    default_args=default_args,
    description='Load transformed data into data warehouse',
    schedule='0 8 * * *',  # Daily at 8 AM UTC
    max_active_runs=1,
    tags=['kharon-auto', 'etl', 'load', 'warehouse', 'client_alpha'],
    catchup=False,
)

# Create task using KharonOperator for script execution
load_warehouse_task = KharonOperator(
    task_id='load_warehouse',
    script_path='/opt/kharon/scripts_externos/etl/load_warehouse.py',
    script_id='load_warehouse',
    dag=dag,
)