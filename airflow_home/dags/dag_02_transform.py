"""
Kharōn DAG - Sales Data Transformation

This DAG executes the transform_sales script to transform and clean sales data
from Client Beta for ETL processing.

Author: Kharōn Orchestration Platform
Version: 1.0
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.kharon_operator import KharonOperator

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
    dag_id='kharon_transform',
    default_args=default_args,
    description='Transform and clean sales data from Client Beta',
    schedule_interval='0 7 * * *',  # Daily at 7 AM UTC
    max_active_runs=1,
    tags=['kharon-auto', 'etl', 'transform', 'sales', 'client_beta'],
    catchup=False,
)

# Create task using KharonOperator for script execution
transform_sales_task = KharonOperator(
    task_id='transform_sales',
    script_id='transform_sales',  # Reference from scripts_registry.yaml
    dag=dag,
)