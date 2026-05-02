FROM apache/airflow:3.0.0-python3.11

USER root

# Runtime dependencies for KharonOperator
RUN pip install --no-cache-dir \
    pyyaml>=6.0 \
    requests>=2.31.0 \
    pandas>=3.0.0 \
    numpy>=1.24

USER airflow

# Airflow home is mounted at runtime via -v ./airflow_home:/opt/airflow
ENV AIRFLOW_HOME=/opt/airflow

# Run all services in standalone mode (dag-processor + scheduler + api-server)
ENTRYPOINT ["bash", "-c", "\
    airflow db migrate && \
    airflow users create \
        --username admin \
        --firstname Kharōn \
        --lastname Admin \
        --role Admin \
        --email admin@arkh-ur.com \
        --password \"${AIRFLOW_ADMIN_PASSWORD:-admin}\" 2>/dev/null || true && \
    exec airflow standalone \
"]
