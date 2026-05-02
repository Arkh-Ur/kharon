#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE="${KHARON_IMAGE:-kharon:latest}"
AUTO_UPDATE="${AUTO_UPDATE:-false}"

if ! podman image exists "$IMAGE" 2>/dev/null; then
    echo "Building $IMAGE..."
    podman build -t "$IMAGE" "$SCRIPT_DIR"
fi

podman run -it --rm \
  --name kharon \
  -p 8080:8080 \
  -p 8501:8501 \
  -v "${SCRIPT_DIR}/airflow_home:/opt/airflow:Z" \
  -e AIRFLOW_HOME=/opt/airflow \
  -e AUTO_UPDATE="${AUTO_UPDATE}" \
  -e KHARON_AIRFLOW_PASSWORD="${KHARON_AIRFLOW_PASSWORD:-}" \
  "$IMAGE"
