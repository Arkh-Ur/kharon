# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Kharōn

Script orchestration platform for Arkh-Ur. It wraps existing external scripts (never modified) in Airflow DAGs and exposes a Streamlit web UI for monitoring, on-demand execution, and client management.

## Stack

| Layer | Tech |
|---|---|
| Orchestrator | Apache Airflow 3.x |
| Webapp | Streamlit |
| Language | Python 3.10+ |
| Config | YAML |
| DB | SQLite (dev) / PostgreSQL (prod) |

## Commands

```bash
# Start everything (recommended)
./start_kharon.sh

# Webapp only (Airflow must already be running)
source airflow_venv/bin/activate
cd webapp && streamlit run app.py --server.port 8501

# Airflow services manually (each in separate terminal, venv active)
airflow dag-processor
airflow scheduler
airflow api-server --port 8080

# E2E tests (requires running services on ports 8501 and 8080)
source airflow_venv/bin/activate
pytest tests/e2e/ -v
pytest tests/e2e/test_webapp.py::test_name -v   # single test
```

Config via env vars (all have defaults):
- `KHARON_AIRFLOW_HOST` / `KHARON_AIRFLOW_PORT` / `KHARON_AIRFLOW_USER` / `KHARON_AIRFLOW_PASSWORD`
- `KHARON_PORT` (Streamlit port, default 8501)
- `AIRFLOW_HOME` (default `./airflow_home`)

## Architecture

### Webapp (`webapp/`)

Entry point is `webapp/app.py`. Navigation is a dict `_PAGE_HANDLERS` mapping page names to handler functions. Pages: Tablero (dashboard), Procesos (processes), Nuevo Script, Configuración.

- `airflow_client.py` — REST client for Airflow 3.x API (`/api/v2`). Auth is JWT cookie-based: a GET to `/api/v2/auth/login` with BasicAuth sets the `_token` cookie; all subsequent requests use that session. Re-authenticates automatically on 401.
- `client_manager.py` — CRUD for `clients_registry.yaml`. Supports both list format (`clients: [...]`) and dict format for backward compatibility.
- `dag_generator.py` — generates `.py` DAG files into `airflow_home/dags/` from web form input and appends the entry to `scripts_registry.yaml`.
- `config.py` — all paths and settings; runs `ensure_directories()` at import time.

### Airflow DAGs (`airflow_home/dags/`)

- `operators/kharon_operator.py` — `KharonOperator(BaseOperator)` orchestrates `ScriptRunner` + `ScriptMonitor`. Import from `airflow.sdk.bases.operator` (Airflow 3.x), NOT `airflow.models`.
- `utils/script_runner.py` — runs `.py`/`.sh` scripts via `subprocess.Popen`. Detects interpreter from extension. Parses `RESULT:{json}` lines from stdout into structured output.
- `utils/script_monitor.py` — tracks per-script health (consecutive failures, success rate). Results written to `airflow_home/logs/kharon_monitoring/`.
- `config/scripts_registry.yaml` — config manual de scripts Airflow (formato `scripts: [...]`). **No modificar desde el webapp.**
- `config/generated_scripts.yaml` — registry de scripts creados desde la webapp (formato dict `{script_id: {metadata}}`). Manejado exclusivamente por `DAGGenerator`.
- `config/clients_registry.yaml` — client definitions.

### External scripts (`airflow_home/scripts_externos/`)

Scripts placed here are NEVER modified by Kharōn. They are executed as-is by `ScriptRunner`. Scripts can optionally write `RESULT:{json}` to stdout for structured output.

## DAG conventions

Generated DAGs:
- DAG ID: `{script_id}` (sanitized: lowercase, only `[a-z0-9_]`)
- Tags always include `kharon-auto` and `client_{client_id}`
- Identified as Kharōn DAGs by: tag `kharon-auto` OR `dag_id.startswith("kharon_")`

Execution modes:
- `on_demand` → `schedule=None`
- `continuous` → `schedule="@continuous"` + `max_active_runs=1`
- `scheduled` → cron string passed directly

## Airflow 3.x gotchas

- Requires a separate `dag-processor` daemon (not included in `standalone`).
- API prefix is `/api/v2` (not `/api/v1`).
- Health check endpoint: `GET /api/v2/monitor/health`.
- `BaseOperator` lives in `airflow.sdk.bases.operator`, not `airflow.models`.
- DAG `schedule_interval` is now `schedule`; the API returns it as `{"value": "..."}` dict.
- Airflow auto-generates an admin password on first run, stored in `airflow_home/simple_auth_manager_passwords.json.generated`.

## E2E tests

Playwright-based (`tests/e2e/`). Require both services running. Screenshots on failure saved to `tests/e2e/screenshots/`. The `conftest.py` fixture reads the Airflow password from `KHARON_AIRFLOW_PASSWORD` env var or the generated passwords file.
