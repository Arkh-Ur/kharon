# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Kharōn

Script orchestration platform for Arkh-Ur. Wraps existing external scripts (never modified) in Airflow DAGs and exposes a Streamlit web UI for monitoring, on-demand execution, and client management.

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
# Start everything
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
pytest tests/e2e/test_webapp.py::test_name -v
```

Config via env vars (all have defaults):
- `KHARON_AIRFLOW_HOST/PORT/USER/PASSWORD`, `KHARON_PORT` (8501), `AIRFLOW_HOME`

## Architecture

### Webapp (`webapp/`)

Entry point `webapp/app.py`. Navigation via `_PAGE_HANDLERS` dict. 7 pages: Tablero, Procesos, Logs, Monitoreo, Salud, Nuevo Script, Configuración.

**Core modules:**
- `airflow_client.py` — REST client for Airflow 3.x (`/api/v2`). Auth: JWT cookie via `GET /api/v2/auth/login` with BasicAuth (⚠️ known issue: should be `POST` with JSON body per Airflow 3.x spec). Auto-reauthenticates on 401. `get_task_log` routes through `_request()` and parses Airflow 3.x JSON log format `{"content": [...]}` via `utils.format_airflow_log`. All requests use `timeout=30`.
- `client_manager.py` — CRUD for `clients_registry.yaml`. `Client` dataclass: required fields are `id`, `name`, `color` only. `load_clients()` handles both list and flat-dict YAML formats — auto-migrates legacy `clients: [...]` format to flat dict on first load. All CRUD writes use flat dict format.
- `dag_generator.py` — Generates `.py` DAG files into `airflow_home/dags/` and writes to `generated_scripts.yaml`. Default uses `GENERATED_SCRIPTS_PATH` (not `SCRIPTS_REGISTRY_PATH`). Has `update_execution_mode()` to regenerate a DAG in place. String values embedded in generated Python code are sanitized via `_safe_script_name`/`_safe_client_id` helpers.
- `config.py` — All paths and theme colors. Runs `ensure_directories()` at import time.
- `utils.py` — Shared: `describe_cron()` (Spanish), `extract_primary_color()` (raster + SVG), `format_airflow_log()` (Airflow 3.x event-dict lists → readable text), `safe_html()` (HTML escaping), `atomic_write()` (write-then-rename for safe file writes).

**Data fetching pattern:**
`_get_kharon_dags()` — central helper that fetches all Kharōn DAGs + their last 15 runs per DAG in one function. Used by most pages to avoid redundant `AirflowClient` instantiations.

**DAG filtering — central system (all pages go through this):**
```
_filter_kharon_dags(all_dags) → filtered list
  ├── _is_kharon_dag(dag)           # prefix "kharon_" OR tag "kharon-auto"
  ├── _load_generated_dag_clients() # reads generated_scripts.yaml (priority 1 — bypasses Airflow stale DB)
  ├── _resolve_dag_client(dag, clients, gen_map)  # resolves client in 4 formats:
  │     1. generated_scripts.yaml (webapp DAGs — bypasses stale Airflow DB)
  │     2. tag "client_{id}" → exact match or "client_" prefix match
  │     3. tag is a registered client NAME (legacy/stale Airflow cache)
  │     4. tag is a registered client ID
  ├── show_unregistered_dags       # session_state toggle (Configuración page)
  └── client_filter                # session_state from sidebar selectbox (display name)
```

**Airflow date compatibility:** `_dag_run_date(run)` → `logical_date` → `execution_date` → `start_date` (Airflow 3.x renamed `execution_date` to `logical_date`).

### Airflow DAGs (`airflow_home/dags/`)

- `operators/kharon_operator.py` — `KharonOperator(BaseOperator)`. Import from `airflow.sdk.bases.operator` (Airflow 3.x), NOT `airflow.models`.
- `utils/script_runner.py` — Runs `.py`/`.sh` via `subprocess.Popen`. Detects interpreter by extension. Parses `RESULT:{json}` from stdout.
- `utils/script_monitor.py` — Per-script health tracking. Writes to `airflow_home/logs/kharon_monitoring/{script_id}_history.json` (NOT a single report file — one file per script).
- `config/scripts_registry.yaml` — Manual Airflow config (`scripts: [...]` list format). **Never write from webapp.**
- `config/generated_scripts.yaml` — Webapp-generated DAG registry (flat dict `{script_id: {metadata}}`). Managed exclusively by `DAGGenerator`.
- `config/clients_registry.yaml` — Client definitions (flat dict format after migration).

### External scripts (`airflow_home/scripts_externos/`)

Never modified by Kharōn. Optional: output `RESULT:{json}` to stdout for structured results.

## DAG conventions

- DAG ID: `{sanitized_script_id}` (lowercase, `[a-z0-9_]` only). No `kharon_` prefix for webapp-generated DAGs.
- Tags always include `kharon-auto` and `client_{client_id}`
- Identified as Kharōn DAGs: tag `kharon-auto` OR `dag_id.startswith("kharon_")`
- Execution modes: `on_demand` (schedule=None) · `continuous` (@continuous + max_active_runs=1) · `scheduled` (cron string)
- `get_registry_status()` globs `kharon_*.py` — always returns 0 for webapp-generated DAGs (known bug: generated DAGs don't have this prefix)

## Airflow 3.x gotchas

- Separate `dag-processor` daemon required (`airflow dag-processor`).
- API prefix: `/api/v2`. Health: `GET /api/v2/monitor/health`.
- `BaseOperator` is in `airflow.sdk.bases.operator`, NOT `airflow.models`.
- `schedule_interval` → `schedule`. API returns it as `{"value": "..."}` dict.
- Log endpoint returns `{"content": [event_dict, ...], "continuation_token": ...}` — NOT plain text. `format_airflow_log()` converts event-dicts to readable lines.
- `execution_date` renamed to `logical_date`. Use `_dag_run_date(run)` helper.
- Task `state` can be `null` (Python `None`) for unstarted tasks. `try_number=0` means never executed — no log available.
- Admin password auto-generated to `airflow_home/simple_auth_manager_passwords.json.generated`.
- Airflow's DB can cache stale DAG tags — `_load_generated_dag_clients()` reads `generated_scripts.yaml` as priority 1 to bypass this.
- `@continuous` schedule: verify availability in target Airflow 3.x installation before using.

## Client ID resolution

Two historical conventions co-exist:
- Webapp-generated DAGs: tag `client_santa_elena` → id `santa_elena` → registry has `santa_elena` ✓
- Hand-crafted DAGs: tag `client_alpha` → id `alpha` → registry has `client_alpha` (needs prefix resolution)

`_resolve_dag_client` handles both. Never assume a raw tag value equals a registered client ID.

## Known pending issues (from adversarial review)

| Severity | File | Issue |
|----------|------|-------|
| CRITICAL | `airflow_client.py:51` | `_authenticate` uses GET — should be `POST` with `json={"username":..., "password":...}` |
| CRITICAL | `dag_generator.py` | `_safe_client_id` needs `repr()` wrapping for single-quote injection in generated code |
| WARNING | `app.py:864` | `datetime.now()` naive mixed with tz-aware datetimes in Gantt chart |
| WARNING | `app.py:~2183` | Client ID derivation doesn't sanitize all special chars (`/`, `'`, `&`, etc.) |
| WARNING | `client_manager.py:263` | `Client(**client_data)` can raise `TypeError` on unexpected keys |
| WARNING | `app.py:~1065` | N+1 `_load_registry()` in search loop (partial fix — expander loop fixed, search loop not) |
| WARNING | `script_form.py` + `app.py` | `startswith()` path traversal check bypassable — use `Path.is_relative_to()` |
| WARNING | `airflow_client.py:93` | Dead `isinstance(e, AirflowClientError)` guard in `except RequestException` |

## Components

`webapp/components/status_badge.py`:
- `render_status_badge(status)` — Airflow states: success/failed/running/queued/paused/up_for_retry/upstream_failed/skipped/unknown
- `render_client_badge(client_dict)` — Shows logo if `logo_path` exists, else colored initial square. No emoji.
- `_client_icon_html(client_dict)` — Returns raw HTML for logo/initial (importable by `app.py`)
- `render_health_indicator(health_dict)` — healthy/unhealthy/unknown/pending
- `render_criticality_badge(criticality)` — alta/media/baja

`webapp/components/log_viewer.py`:
- `render_log_viewer(log_content, auto_refresh, key_prefix)` — accepts `key_prefix` to avoid duplicate Streamlit widget IDs when rendered multiple times.

## E2E tests

Playwright-based (`tests/e2e/`). Require both services running. Screenshots on failure → `tests/e2e/screenshots/`. Password from `KHARON_AIRFLOW_PASSWORD` env var or `airflow_home/simple_auth_manager_passwords.json.generated`.
