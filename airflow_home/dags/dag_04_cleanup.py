"""
Kharōn DAG - Log File Cleanup

This DAG executes the cleanup_logs script to clean up old log files and
temporary files for Client Gamma.

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
    dag_id='kharon_cleanup',
    default_args=default_args,
    description='Clean up old log files and temporary files for Client Gamma',
    schedule='0 2 * * 0',  # Weekly at 2 AM UTC on Sunday
    max_active_runs=1,
    tags=['kharon-auto', 'client_gamma', 'maintenance', 'cleanup'],
    catchup=False,
)

# Create task using KharonOperator for script execution
cleanup_logs_task = KharonOperator(
    task_id='cleanup_logs',
    script_path='/opt/kharon/scripts_externos/maintenance/cleanup_logs.sh',
    script_id='cleanup_logs',
    dag=dag,
)