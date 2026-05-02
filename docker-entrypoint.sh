#!/bin/bash
set -e

AIRFLOW_HOME="${AIRFLOW_HOME:-/opt/airflow}"
KHARON_HOME="${KHARON_HOME:-/opt/kharon}"
KHARON_PORT="${KHARON_PORT:-8501}"
KHARON_AIRFLOW_PORT="${KHARON_AIRFLOW_PORT:-8080}"
AUTO_UPDATE="${AUTO_UPDATE:-false}"

echo "⚓ Kharōn — Starting up..."

if [ "$AUTO_UPDATE" = "true" ]; then
    echo "🔄 AUTO_UPDATE=true — pulling latest from git..."
    cd "$KHARON_HOME"
    git pull --ff-only origin main 2>&1 || echo "⚠️  git pull failed — using existing code"
    pip install --quiet --no-cache-dir \
        "streamlit>=1.37.0" "streamlit-autorefresh>=1.0.1" \
        "plotly>=6.0.0" "Pillow>=10.0" "numpy>=1.24" \
        "pandas>=3.0.0" "pyyaml>=6.0" "requests>=2.31.0" 2>/dev/null || true
fi

echo "📌 Version: $(cd $KHARON_HOME && git describe --tags --always 2>/dev/null || echo 'unknown')"

export AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW_HOME}/dags"
export AIRFLOW__CORE__PLUGINS_FOLDER="${AIRFLOW_HOME}/plugins"
export AIRFLOW__CORE__LOAD_EXAMPLES="false"
export AIRFLOW__CORE__EXECUTOR="LocalExecutor"
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:///${AIRFLOW_HOME}/airflow.db"
export AIRFLOW__LOGGING__BASE_LOG_FOLDER="${AIRFLOW_HOME}/logs"

mkdir -p "${AIRFLOW_HOME}/dags" "${AIRFLOW_HOME}/logs" \
         "${AIRFLOW_HOME}/logs/kharon_monitoring" \
         "${AIRFLOW_HOME}/data" "${AIRFLOW_HOME}/plugins"

echo "🗄️  Initializing Airflow DB..."
airflow db migrate 2>&1 | tail -2

airflow users create \
    --username "${KHARON_AIRFLOW_USER:-admin}" \
    --firstname Kharōn --lastname Admin --role Admin \
    --email admin@arkh-ur.com \
    --password "${KHARON_AIRFLOW_PASSWORD:-admin}" 2>/dev/null || true

PW_FILE="${AIRFLOW_HOME}/simple_auth_manager_passwords.json.generated"
if [ -f "$PW_FILE" ]; then
    export KHARON_AIRFLOW_PASSWORD=$(python3 -c \
        "import json; print(json.load(open('$PW_FILE'))['admin'])" 2>/dev/null \
        || echo "${KHARON_AIRFLOW_PASSWORD:-admin}")
fi

cleanup() {
    echo "🛑 Shutting down Kharōn..."
    kill $(jobs -p) 2>/dev/null || true
    wait
}
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Airflow services..."
airflow dag-processor >> "${AIRFLOW_HOME}/logs/dag-processor.log" 2>&1 &
airflow scheduler >> "${AIRFLOW_HOME}/logs/scheduler.log" 2>&1 &
airflow api-server --port "$KHARON_AIRFLOW_PORT" >> "${AIRFLOW_HOME}/logs/api-server.log" 2>&1 &

echo "⏳ Waiting for Airflow API (this takes ~30s on first run)..."
for i in $(seq 1 45); do
    curl -s "http://localhost:${KHARON_AIRFLOW_PORT}/api/v2/monitor/health" > /dev/null 2>&1 && break
    sleep 2
    [ $i -eq 45 ] && echo "⚠️  Airflow API timeout — check /opt/airflow/logs/api-server.log"
done
echo "✅ Airflow ready"

echo "🌐 Starting Kharōn webapp..."
cd "${KHARON_HOME}/webapp"
streamlit run app.py \
    --server.port "$KHARON_PORT" \
    --server.address "0.0.0.0" \
    --browser.gatherUsageStats false \
    --theme.primaryColor "#374151" \
    --theme.backgroundColor "#0A0F18" \
    --theme.secondaryBackgroundColor "#131923" \
    --theme.textColor "#e5e7eb" \
    >> "${AIRFLOW_HOME}/logs/streamlit.log" 2>&1 &

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     ⚓ Kharōn is running!               ║"
echo "║                                          ║"
echo "║  Kharōn App:  http://localhost:${KHARON_PORT}   ║"
echo "║  Airflow UI:  http://localhost:${KHARON_AIRFLOW_PORT}   ║"
echo "║                                          ║"
echo "║  Ctrl+C to stop                         ║"
echo "╚══════════════════════════════════════════╝"

wait
