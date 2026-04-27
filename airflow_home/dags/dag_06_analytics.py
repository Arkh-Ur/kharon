"""
Kharōn DAG - Analytics Pipeline

This DAG executes the analytics_pipeline script to run analytics for
Client Gamma data in continuous mode.

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
    dag_id='kharon_analytics',
    default_args=default_args,
    description='Run analytics pipeline for Client Gamma data in continuous mode',
    schedule='@continuous',  # Continuous execution mode
    max_active_runs=1,
    tags=['kharon-auto', 'client_gamma', 'analytics', 'pipeline'],
    catchup=False,
)

# Create task using KharonOperator for script execution
analytics_pipeline_task = KharonOperator(
    task_id='analytics_pipeline',
    script_path='/opt/kharon/scripts_externos/analytics/analytics_pipeline.py',
    script_id='analytics_pipeline',
    dag=dag,
)