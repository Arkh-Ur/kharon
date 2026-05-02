#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE="${KHARON_IMAGE:-kharon:latest}"
AUTO_UPDATE="${AUTO_UPDATE:-false}"

if ! podman image exists "$IMAGE" 2>/dev/null; then
    echo "Building $IMAGE..."
    podman build -t "$IMAGE" "$SCRIPT_DIR"
fi

PG_ENV=""
if [ -n "${POSTGRES_HOST:-}" ]; then
    PG_ENV="-e POSTGRES_HOST=${POSTGRES_HOST} \
            -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
            -e POSTGRES_USER=${POSTGRES_USER:-airflow} \
            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
            -e POSTGRES_DB=${POSTGRES_DB:-airflow}"
    echo "📦 Using PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-airflow}"
fi

podman run -it --rm \
  --name kharon \
  -p 8080:8080 \
  -p 8501:8501 \
  -v "${SCRIPT_DIR}/airflow_home:/opt/airflow:Z" \
  -e AIRFLOW_HOME=/opt/airflow \
  -e AUTO_UPDATE="${AUTO_UPDATE}" \
  -e KHARON_AIRFLOW_PASSWORD="${KHARON_AIRFLOW_PASSWORD:-}" \
  ${PG_ENV} \
  "$IMAGE"
