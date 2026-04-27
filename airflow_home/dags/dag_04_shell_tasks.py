"""
Kharōn DAG - Shell Script Maintenance Tasks

This DAG executes the cleanup_logs shell script to perform maintenance
operations for Client Gamma, including log cleanup and file management.

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
    dag_id='kharon_shell_maintenance',
    default_args=default_args,
    description='Execute shell script maintenance tasks for Client Gamma',
    schedule='0 2 * * 0',  # Weekly on Sunday at 2 AM UTC
    max_active_runs=1,
    tags=['kharon-auto', 'maintenance', 'shell', 'cleanup', 'client_gamma'],
    catchup=False,
)

# Create task using KharonOperator for shell script execution
cleanup_logs_task = KharonOperator(
    task_id='cleanup_logs',
    script_path='/opt/kharon/scripts_externos/maintenance/cleanup_logs.sh',
    script_id='cleanup_logs',
    dag=dag,
)