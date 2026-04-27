"""
Kharōn DAG - Client Alpha Data Extraction

This DAG executes the extract_client_alpha script to extract data from Client Alpha
source systems as part of the ETL pipeline.

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
    dag_id='kharon_extract',
    default_args=default_args,
    description='Extract data from Client Alpha source systems',
    schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
    max_active_runs=1,
    tags=['kharon-auto', 'etl', 'extract', 'client_alpha'],
    catchup=False,
)

# Create task using KharonOperator for script execution
extract_client_alpha_task = KharonOperator(
    task_id='extract_client_alpha',
    script_id='extract_client_alpha',  # Reference from scripts_registry.yaml
    dag=dag,
)