FROM apache/airflow:3.0.0-python3.11

ARG KHARON_REPO=https://github.com/Arkh-Ur/kharon.git
ARG KHARON_BRANCH=main

USER root

RUN apt-get update && apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${KHARON_BRANCH}" "${KHARON_REPO}" /opt/kharon && \
    chown -R airflow:root /opt/kharon

COPY --chown=airflow:root docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER airflow

RUN pip install --no-cache-dir \
    "streamlit>=1.37.0" \
    "streamlit-autorefresh>=1.0.1" \
    "plotly>=6.0.0" \
    "Pillow>=10.0" \
    "numpy>=1.24" \
    "pandas>=3.0.0" \
    "pyyaml>=6.0" \
    "requests>=2.31.0" \
    "psycopg2-binary>=2.9.0"

ENV AIRFLOW_HOME=/opt/airflow
ENV KHARON_HOME=/opt/kharon
ENV KHARON_AIRFLOW_HOST=localhost
ENV KHARON_AIRFLOW_PORT=8080
ENV KHARON_AIRFLOW_USER=admin
ENV KHARON_PORT=8501
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AUTO_UPDATE=false

EXPOSE 8080 8501

ENTRYPOINT ["/entrypoint.sh"]
