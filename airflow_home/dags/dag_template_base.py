"""
DAG Template Base for Kharōn Orchestration Platform

This is a REFERENCE template showing the standard pattern for creating Kharōn DAGs.
DO NOT create an actual DAG from this file - use it as a reference pattern.

Standard Kharōn DAG Pattern:
1. Import required modules
2. Define default_args (owner, retries, etc.)
3. Create DAG instance with proper configuration
4. Define task(s) using KharonOperator for external scripts
5. Set task dependencies (if any)

Example of actual DAG creation (DO NOT UNCOMMENT THIS):
"""
# from datetime import datetime
# from airflow import DAG
# from airflow.operators.kharon_operator import KharonOperator
# 
# # Standard default arguments for all Kharōn DAGs
# default_args = {
#     'owner': 'arkh-ur',
#     'depends_on_past': False,
#     'start_date': datetime(2026, 1, 1),
#     'email_on_failure': True,
#     'email_on_retry': False,
#     'retries': 2,
#     'retry_delay': timedelta(minutes=5),
# }
# 
# # Create DAG instance
# dag = DAG(
#     dag_id='kharon_example_dag',
#     default_args=default_args,
#     description='Kharōn orchestration DAG',
#     schedule_interval='0 6 * * *',  # From scripts_registry.yaml
#     max_active_runs=1,
#     tags=['kharon-auto'],
#     catchup=False,
# )
# 
# # Create task using KharonOperator
# example_task = KharonOperator(
#     task_id='execute_script',
#     script_id='extract_client_alpha',  # From scripts_registry.yaml
#     dag=dag,
# )

"""
KHARON DAG BEST PRACTICES:
=========================

1. SCRIPT REGISTRY INTEGRATION:
   - Always pull schedule_interval from scripts_registry.yaml
   - Use script_id from registry to reference scripts
   - Configure task parameters based on registry settings

2. TASK CONFIGURATION:
   - Use KharonOperator for all script executions
   - Set appropriate timeout based on script expectations
   - Include retry logic as specified in registry

3. DEPENDENCY MANAGEMENT:
   - Define task dependencies explicitly
   - Use task_id references for downstream dependencies
   - Consider criticality levels when ordering tasks

4. MONITORING & ALERTING:
   - Include tags for automatic monitoring
   - Ensure failure handling triggers monitoring rules
   - Log appropriate status messages

5. BRANDING & ORGANIZATION:
   - Use consistent naming: kharon_{script_type}_{client}
   - Include descriptive docstrings
   - Use start_date of 2026-01-01 for all DAGs
   - Always include 'kharon-auto' tag

6. SCHEDULING:
   - Use catchup=False to prevent historical runs
   - Match schedule_interval with script requirements
   - Consider business hours for critical scripts

EXAMPLE DAG STRUCTURE:
=====================

For a simple script execution:
- Define single KharonOperator with script_id
- No dependencies required

For chained pipelines:
- Define KharonOperator for each script in sequence
- Use >> operator to define dependencies: task1 >> task2 >> task3
- Ensure scripts are executed in logical order

For monitoring DAGs:
- Use PythonOperator for health checks
- Query script execution status from Kharōn system
- Include conditional logic based on performance metrics
"""

# Quick reference for common imports:
# from datetime import datetime, timedelta
# from airflow import DAG
# from airflow.operators.kharon_operator import KharonOperator
# from airflow.operators.python import PythonOperator