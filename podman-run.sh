#!/bin/bash
# ─── Kharōn All-in-One — Podman launcher ─────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE="${KHARON_IMAGE:-kharon:latest}"
AUTO_UPDATE="${AUTO_UPDATE:-false}"

# Build image if it doesn't exist yet
if ! podman image exists "$IMAGE" 2>/dev/null; then
    echo "Building $IMAGE (first run, this takes ~3 min)..."
    podman build -t "$IMAGE" "$SCRIPT_DIR"
fi

# Build env args array (safe with spaces/special chars)
ENV_ARGS=(
    -e "AIRFLOW_HOME=/opt/airflow"
    -e "AUTO_UPDATE=${AUTO_UPDATE}"
    -e "KHARON_AIRFLOW_PASSWORD=${KHARON_AIRFLOW_PASSWORD:-}"
)

podman run -it --rm \
    --name kharon \
    -p "${KHARON_AIRFLOW_PORT:-8080}:8080" \
    -p "${KHARON_PORT:-8501}:8501" \
    -v "${SCRIPT_DIR}/airflow_home:/opt/airflow:Z" \
    "${ENV_ARGS[@]}" \
    "$IMAGE"
