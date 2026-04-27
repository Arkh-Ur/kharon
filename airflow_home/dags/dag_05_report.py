"""
Kharōn DAG - Daily Report Generation

This DAG executes the generate_daily_report script to generate daily business
reports for Client Beta.

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
    dag_id='kharon_report',
    default_args=default_args,
    description='Generate daily business reports for Client Beta',
    schedule='0 9 * * *',  # Daily at 9 AM UTC
    max_active_runs=1,
    tags=['kharon-auto', 'client_beta', 'reports', 'daily'],
    catchup=False,
)

# Create task using KharonOperator for script execution
generate_daily_report_task = KharonOperator(
    task_id='generate_daily_report',
    script_path='/opt/kharon/scripts_externos/reports/daily_report.py',
    script_id='generate_daily_report',
    dag=dag,
)