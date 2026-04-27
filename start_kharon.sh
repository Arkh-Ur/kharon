#!/bin/bash
# ============================================================================
# Kharōn — Startup Script
# Plataforma de Orquestación y Monitoreo de Scripts
# Arkh-Ur — Data Engineering Division
# ============================================================================

set -e

# Colors for output
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

KHARON_ICON="⚓"

echo -e "${PURPLE}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     $KHARON_ICON  Kharōn — Arkh-Ur               ║"
echo "  ║   Plataforma de Orquestación y          ║"
echo "  ║   Monitoreo de Scripts                  ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export KHARON_HOME="${KHARON_HOME:-$SCRIPT_DIR}"
export AIRFLOW_HOME="${KHARON_HOME}/airflow_home"

# Airflow configuration
export KHARON_AIRFLOW_HOST="${KHARON_AIRFLOW_HOST:-localhost}"
export KHARON_AIRFLOW_PORT="${KHARON_AIRFLOW_PORT:-8080}"
export KHARON_AIRFLOW_USER="${KHARON_AIRFLOW_USER:-admin}"

Pw_FILE="${AIRFLOW_HOME}/simple_auth_manager_passwords.json.generated"
if [ -f "$Pw_FILE" ]; then
    export KHARON_AIRFLOW_PASSWORD="${KHARON_AIRFLOW_PASSWORD:-$(python3 -c "import json; print(json.load(open('$Pw_FILE'))['admin'])" 2>/dev/null || echo 'admin')}"
else
    export KHARON_AIRFLOW_PASSWORD="${KHARON_AIRFLOW_PASSWORD:-admin}"
fi

# Kharōn webapp port
export KHARON_PORT="${KHARON_PORT:-8501}"

# Virtual environment
VENV_DIR="${KHARON_HOME}/airflow_venv"

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.10+"
        exit 1
    fi
    log_info "Python: $(python3 --version)"
    
    # Check virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log_warn "Virtual environment not found at $VENV_DIR"
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log_info "Virtual environment created"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_info "Virtual environment activated"
    
    # Check Airflow
    if ! command -v airflow &> /dev/null; then
        log_warn "Airflow not found. Installing dependencies..."
        pip install -r "${KHARON_HOME}/requirements.txt" 2>/dev/null
        log_info "Dependencies installed"
    fi
    
    log_info "Airflow: $(airflow version 2>/dev/null || echo 'not installed')"
}

init_airflow() {
    log_info "Initializing Airflow..."
    
    mkdir -p "$AIRFLOW_HOME/dags"
    mkdir -p "$AIRFLOW_HOME/logs"
    mkdir -p "$AIRFLOW_HOME/logs/kharon_monitoring"
    mkdir -p "$AIRFLOW_HOME/data"
    
    airflow db migrate 2>&1 | tail -1 || log_warn "Airflow DB migration issue"
    
    log_info "Airflow initialized"
}

start_airflow() {
    log_info "Starting Airflow services..."
    
    # Airflow 3.x requires a separate dag-processor daemon
    # (standalone_dag_processor defaults to True in 3.x)
    AIRFLOW_BIN="${VENV_DIR}/bin/airflow"
    
    # Start DAG processor in background (parses DAG files into the DB)
    "$AIRFLOW_BIN" dag-processor &> "${AIRFLOW_HOME}/logs/dag-processor.log" &
    DAGPROC_PID=$!
    log_info "Airflow DAG Processor started (PID: $DAGPROC_PID)"
    
    # Start scheduler in background
    "$AIRFLOW_BIN" scheduler &> "${AIRFLOW_HOME}/logs/scheduler.log" &
    SCHEDULER_PID=$!
    log_info "Airflow Scheduler started (PID: $SCHEDULER_PID)"
    
    # Start API server
    "$AIRFLOW_BIN" api-server --port "$KHARON_AIRFLOW_PORT" &> "${AIRFLOW_HOME}/logs/api-server.log" &
    API_PID=$!
    log_info "Airflow API Server started (PID: $API_PID, port: $KHARON_AIRFLOW_PORT)"
    
    # Wait for DAG processor to parse DAGs (~30s on first run)
    log_info "Waiting for DAG processor to parse DAG files..."
    sleep 10
    
    # Wait for Airflow API to be ready
    log_info "Waiting for Airflow API to be ready..."
    MAX_WAIT=90
    WAITED=0
    while ! curl -s "http://${KHARON_AIRFLOW_HOST}:${KHARON_AIRFLOW_PORT}/api/v2/monitor/health" > /dev/null 2>&1; do
        sleep 2
        WAITED=$((WAITED + 2))
        if [ $WAITED -ge $MAX_WAIT ]; then
            log_error "Airflow API did not start within ${MAX_WAIT}s"
            log_error "Check logs: ${AIRFLOW_HOME}/logs/api-server.log"
            exit 1
        fi
        echo -n "."
    done
    echo ""
    log_info "Airflow is ready"
}

start_webapp() {
    log_info "Starting Kharōn webapp..."
    
    # Install webapp dependencies if needed
    pip install -r "${KHARON_HOME}/webapp/requirements.txt" 2>/dev/null
    
    # Start Streamlit
    cd "${KHARON_HOME}/webapp"
    streamlit run app.py \
        --server.port "$KHARON_PORT" \
        --server.address "0.0.0.0" \
        --browser.gatherUsageStats false \
        --theme.primaryColor "#4a1a8a" \
        --theme.backgroundColor "#ffffff" \
        --theme.secondaryBackgroundColor "#f8f9fa" \
        --theme.textColor "#212529" \
        &
    WEBAPP_PID=$!
    cd "$KHARON_HOME"
    log_info "Kharōn Webapp started (PID: $WEBAPP_PID, port: $KHARON_PORT)"
}

cleanup() {
    log_info "Shutting down Kharōn..."
    
    if [ -n "$WEBAPP_PID" ]; then
        kill $WEBAPP_PID 2>/dev/null || true
        log_info "Webapp stopped"
    fi
    
    if [ -n "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        log_info "Airflow API Server stopped"
    fi
    
    if [ -n "$DAGPROC_PID" ]; then
        kill $DAGPROC_PID 2>/dev/null || true
        log_info "Airflow DAG Processor stopped"
    fi
    
    if [ -n "$SCHEDULER_PID" ]; then
        kill $SCHEDULER_PID 2>/dev/null || true
        log_info "Airflow Scheduler stopped"
    fi
    
    pkill -f "airflow dag-processor" 2>/dev/null || true
    pkill -f "airflow scheduler" 2>/dev/null || true
    pkill -f "airflow api-server" 2>/dev/null || true
    
    log_info "Kharōn shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================================
# Main
# ============================================================================

log_info "KHARON_HOME: $KHARON_HOME"
log_info "AIRFLOW_HOME: $AIRFLOW_HOME"

check_prerequisites
init_airflow
start_airflow
start_webapp

echo ""
echo -e "${PURPLE}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  $KHARON_ICON Kharōn is running!${NC}"
echo ""
echo -e "  Airflow UI:   ${GREEN}http://${KHARON_AIRFLOW_HOST}:${KHARON_AIRFLOW_PORT}${NC}"
echo -e "  Kharōn App:   ${GREEN}http://localhost:${KHARON_PORT}${NC}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop"
echo -e "${PURPLE}══════════════════════════════════════════════${NC}"

# Wait for shutdown
wait
