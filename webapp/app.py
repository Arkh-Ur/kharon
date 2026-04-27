import json
from datetime import datetime, timedelta
from typing import List

import streamlit as st

from airflow_client import AirflowClient, AirflowClientError
from client_manager import ClientManager
from dag_generator import DAGGenerator
import config
from components.dag_card import render_dag_card
from components.log_viewer import render_log_viewer
from components.script_form import render_script_form
from components.status_badge import (
    render_client_badge,
    render_criticality_badge,
    render_health_indicator,
    render_status_badge,
)


# ─── Custom CSS ────────────────────────────────────────────────────────────────

_KHARON_CSS = """
<style>
    :root {
        --primary: #4a1a8a;
        --primary-light: #6f42c1;
        --secondary: #0d6efd;
        --success: #198754;
        --warning: #fd7e14;
        --danger: #dc3545;
        --bg-dark: #1a1a2e;
        --bg-card: #f8f9fa;
        --text-dark: #1a1a2e;
        --text-muted: #6c757d;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: #e0e0e0 !important;
        width: 100%;
        text-align: left;
        padding: 10px 16px;
        border-radius: 6px;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(74,26,138,0.5);
        border-color: #6f42c1;
    }

    .metric-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, #ffffff 100%);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .metric-card .metric-value {
        font-size: 2.2em;
        font-weight: 800;
        color: var(--primary);
        line-height: 1.1;
    }
    .metric-card .metric-label {
        font-size: 0.85em;
        color: var(--text-muted);
        margin-top: 4px;
    }

    .health-bar {
        height: 8px;
        border-radius: 4px;
        background: #e9ecef;
        overflow: hidden;
        margin-top: 4px;
    }
    .health-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.4s ease;
    }

    h1, h2, h3 {
        color: var(--primary) !important;
    }

    .stAlert {
        border-radius: 8px;
    }
</style>
"""


# ─── Initialization ────────────────────────────────────────────────────────────

def _init_session_state() -> None:
    defaults = {
        "current_page": "Tablero",
        "client_filter": "Todos",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _get_airflow_client() -> AirflowClient:
    return AirflowClient()


def _get_client_manager() -> ClientManager:
    return ClientManager()


def _get_dag_generator() -> DAGGenerator:
    return DAGGenerator()


def _get_clients() -> List[dict]:
    try:
        cm = _get_client_manager()
        return cm.list_clients()
    except Exception:
        return []


def _get_client_filter_options() -> List[str]:
    clients = _get_clients()
    names = ["Todos"] + [c.get("name", "") for c in clients if c.get("name")]
    return names if len(names) > 1 else ["Todos"]


def _filter_by_client(items: List[dict], client_key: str = "client") -> List[dict]:
    filt = st.session_state.get("client_filter", "Todos")
    if filt == "Todos":
        return items
    return [it for it in items if it.get(client_key) == filt]


# ─── Sidebar ───────────────────────────────────────────────────────────────────

_PAGES = [
    "📊 Tablero",
    "🚀 Ejecutar Scripts",
    "📄 Ver Logs",
    "📡 Monitoreo Global",
    "❤️ Salud por Cliente",
    "➕ Nuevo Script",
    "⚙️ Configuración",
]

_PAGE_MAP = {p: p for p in _PAGES}


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center; padding: 16px 0;">'
            '<span style="font-size:2em;">⚓</span><br/>'
            '<span style="font-size:1.4em; font-weight:800; color:#ffffff;">Kharōn</span><br/>'
            '<span style="font-size:0.75em; color:#adb5bd;">Arkh-Ur — Data Engineering</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        for page in _PAGES:
            is_active = st.session_state.current_page == page
            btn_type = "primary" if is_active else "secondary"
            if st.button(page, key=f"nav_{page}", type=btn_type):
                st.session_state.current_page = page
                st.rerun()

        st.divider()
        client_options = _get_client_filter_options()
        st.session_state.client_filter = st.selectbox(
            "🏢 Filtrar por cliente",
            options=client_options,
            index=client_options.index(st.session_state.client_filter)
            if st.session_state.client_filter in client_options
            else 0,
            key="sidebar_client_filter",
        )

        st.divider()
        st.caption("Kharōn v1.0 — Arkh-Ur © 2025")


# ─── Page 1: Tablero ──────────────────────────────────────────────────────────

def _page_dashboard() -> None:
    st.title("📊 Tablero")

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    if not dags:
        st.info("No hay DAGs registrados.")
        return

    dag_runs_map = {}
    for dag in dags:
        dag_id = dag.get("dag_id", "")
        try:
            runs = client.list_dag_runs(dag_id, limit=1)
            dag_runs_map[dag_id] = runs
        except AirflowClientError:
            dag_runs_map[dag_id] = []

    total = len(dags)
    success_count = 0
    failed_count = 0
    running_count = 0

    for runs in dag_runs_map.values():
        if runs:
            last_state = runs[0].get("state", "unknown")
            if last_state == "success":
                success_count += 1
            elif last_state == "failed":
                failed_count += 1
            elif last_state == "running":
                running_count += 1

    col1, col2, col3, col4 = st.columns(4)
    for col, label, value, color in [
        (col1, "Total DAGs", total, "#4a1a8a"),
        (col2, "Exitosos", success_count, "#198754"),
        (col3, "Fallidos", failed_count, "#dc3545"),
        (col4, "Ejecutando", running_count, "#fd7e14"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("DAGs Registrados")

    client_filt = st.session_state.get("client_filter", "Todos")
    for dag in dags:
        dag_id = dag.get("dag_id", "")
        if client_filt != "Todos" and client_filt.lower() not in dag_id.lower():
            continue

        runs = dag_runs_map.get(dag_id, [])
        last_state = runs[0].get("state", "unknown") if runs else "unknown"
        last_run_date = runs[0].get("execution_date") or runs[0].get("start_date") if runs else None

        dag_info = {
            "dag_id": dag_id,
            "description": dag.get("description", ""),
            "status": last_state,
            "last_run": last_run_date,
            "schedule_interval": dag.get("schedule_interval", {}),
            "owners": dag.get("owners", []),
            "tags": [t.get("name", "") for t in dag.get("tags", [])],
        }

        client_name = None
        for tag in dag.get("tags", []):
            tag_name = tag.get("name", "")
            if tag_name.startswith("client_"):
                client_name = tag_name.replace("client_", "")
                break

        if client_filt != "Todos" and client_name and client_filt.lower() != client_name.lower():
            continue

        render_dag_card(dag_info, client_badge=client_name)

    st.divider()
    st.subheader("Ejecuciones Recientes")
    recent_runs = []
    for dag_id, runs in dag_runs_map.items():
        for run in runs[:3]:
            recent_runs.append({**run, "dag_id": dag_id})

    recent_runs.sort(
        key=lambda r: r.get("execution_date") or r.get("start_date") or "",
        reverse=True,
    )
    recent_runs = recent_runs[:20]

    if recent_runs:
        for run in recent_runs:
            col_state, col_dag, col_date, col_type = st.columns([1, 2, 2, 1])
            with col_state:
                render_status_badge(run.get("state", "unknown"))
            with col_dag:
                st.markdown(f"**{run.get('dag_id', '—')}**")
            with col_date:
                exec_date = run.get("execution_date") or run.get("start_date", "—")
                try:
                    dt = datetime.fromisoformat(str(exec_date).replace("Z", "+00:00"))
                    st.caption(dt.strftime("%d/%m/%Y %H:%M"))
                except (ValueError, TypeError):
                    st.caption(str(exec_date))
            with col_type:
                conf = run.get("conf") or {}
                if conf.get("triggered_from") == "kharon":
                    st.caption("🔘 Manual")
                else:
                    st.caption("⏰ Programado")
    else:
        st.info("No hay ejecuciones recientes.")


# ─── Page 2: Ejecutar Scripts ─────────────────────────────────────────────────

def _page_execute_scripts() -> None:
    st.title("🚀 Ejecutar Scripts")

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    kharon_dags = [d for d in dags if d.get("dag_id", "").startswith("kharon_")]
    if not kharon_dags:
        st.info("No hay scripts registrados.")
        return

    client_filt = st.session_state.get("client_filter", "Todos")

    clients_map = {}
    try:
        cm = _get_client_manager()
        for c in cm.list_clients():
            clients_map[c.get("name", "").lower()] = c
    except Exception:
        pass

    grouped = {}
    for dag in kharon_dags:
        dag_id = dag.get("dag_id", "")
        client_name = "Sin cliente"
        for tag in dag.get("tags", []):
            tn = tag.get("name", "")
            if tn.startswith("client_"):
                client_name = tn.replace("client_", "")
                break

        if client_filt != "Todos" and client_filt.lower() != client_filt.lower():
            continue

        grouped.setdefault(client_name, []).append(dag)

    if not grouped:
        st.info("No hay scripts para el cliente seleccionado.")
        return

    for client_name, client_dags in grouped.items():
        client_info = clients_map.get(client_name.lower(), {"name": client_name, "color": "#4a1a8a", "icon": "🏢"})
        with st.expander(f"🏢 {client_name} ({len(client_dags)} scripts)", expanded=True):
            render_client_badge(client_info)
            st.markdown("---")

            for dag in client_dags:
                dag_id = dag.get("dag_id", "")
                desc = dag.get("description") or "Sin descripción"

                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**{dag_id}**")
                    st.caption(desc)

                with col_btn:
                    if st.button("▶ Ejecutar", key=f"exec_{dag_id}"):
                        st.session_state[f"confirm_exec_{dag_id}"] = True

                if st.session_state.get(f"confirm_exec_{dag_id}"):
                    st.warning(f"¿Confirmar ejecución de `{dag_id}`?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Confirmar", key=f"yes_{dag_id}"):
                            try:
                                client.trigger_dag(
                                    dag_id,
                                    conf={"triggered_from": "kharon", "manual": True},
                                )
                                st.toast(f"✅ {dag_id} ejecutado correctamente", icon="✅")
                                st.session_state[f"confirm_exec_{dag_id}"] = False
                            except AirflowClientError as e:
                                st.error(f"Error al ejecutar {dag_id}: {e}")
                                st.session_state[f"confirm_exec_{dag_id}"] = False
                    with col_no:
                        if st.button("❌ Cancelar", key=f"no_{dag_id}"):
                            st.session_state[f"confirm_exec_{dag_id}"] = False

                st.markdown("---")


# ─── Page 3: Ver Logs ─────────────────────────────────────────────────────────

def _page_view_logs() -> None:
    st.title("📄 Ver Logs")

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    kharon_dags = [d for d in dags if d.get("dag_id", "").startswith("kharon_")]
    if not kharon_dags:
        st.info("No hay DAGs disponibles.")
        return

    dag_options = {d.get("dag_id", ""): d.get("dag_id", "") for d in kharon_dags}
    selected_dag = st.selectbox("Seleccioná un DAG", options=list(dag_options.keys()), key="log_dag_select")

    if not selected_dag:
        return

    st.session_state.selected_dag_id = selected_dag

    try:
        runs = client.list_dag_runs(selected_dag, limit=20)
    except AirflowClientError as e:
        st.error(f"Error al obtener ejecuciones: {e}")
        return

    if not runs:
        st.info("No hay ejecuciones para este DAG.")
        return

    run_options = {}
    for run in runs:
        run_id = run.get("dag_run_id", "")
        exec_date = run.get("execution_date") or run.get("start_date", "")
        state = run.get("state", "unknown")
        try:
            dt = datetime.fromisoformat(str(exec_date).replace("Z", "+00:00"))
            label = f"{dt.strftime('%d/%m/%Y %H:%M')} [{state}]"
        except (ValueError, TypeError):
            label = f"{exec_date} [{state}]"
        run_options[run_id] = label

    selected_run = st.selectbox("Seleccioná una ejecución", options=list(run_options.keys()), format_func=lambda x: run_options.get(x, x), key="log_run_select")

    if not selected_run:
        return

    st.session_state.selected_run_id = selected_run

    try:
        tasks = client.list_task_instances(selected_dag, selected_run)
    except AirflowClientError as e:
        st.error(f"Error al obtener tareas: {e}")
        return

    if not tasks:
        st.info("No hay tareas para esta ejecución.")
        return

    task_options = {t.get("task_id", ""): t.get("task_id", "") for t in tasks}
    selected_task = st.selectbox("Seleccioná una tarea", options=list(task_options.keys()), key="log_task_select")

    if not selected_task:
        return

    st.session_state.selected_task_id = selected_task

    st.divider()

    try:
        log_content = client.get_task_log(selected_dag, selected_run, selected_task)
        render_log_viewer(log_content, auto_refresh=True)
    except AirflowClientError as e:
        st.error(f"Error al obtener log: {e}")


# ─── Page 4: Monitoreo Global ─────────────────────────────────────────────────

def _page_global_monitoring() -> None:
    st.title("📡 Monitoreo Global")

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    kharon_dags = [d for d in dags if d.get("dag_id", "").startswith("kharon_")]

    all_runs = []
    for dag in kharon_dags:
        dag_id = dag.get("dag_id", "")
        try:
            runs = client.list_dag_runs(dag_id, limit=10)
            for run in runs:
                run["dag_id"] = dag_id
                all_runs.append(run)
        except AirflowClientError:
            continue

    all_runs.sort(
        key=lambda r: r.get("execution_date") or r.get("start_date") or "",
        reverse=True,
    )
    all_runs = all_runs[:100]

    col_status, col_type, col_client, col_date = st.columns(4)
    with col_status:
        status_filter = st.selectbox("Estado", options=["Todos", "success", "failed", "running", "queued"], key="mon_status")
    with col_type:
        type_filter = st.selectbox("Tipo", options=["Todos", "Manual", "Programado"], key="mon_type")
    with col_client:
        client_options = _get_client_filter_options()
        mon_client = st.selectbox("Cliente", options=client_options, key="mon_client")
    with col_date:
        days_back = st.number_input("Últimos N días", min_value=1, max_value=90, value=7, key="mon_days")

    cutoff = datetime.now().astimezone() - timedelta(days=days_back)

    filtered = []
    for run in all_runs:
        state = run.get("state", "unknown")
        if status_filter != "Todos" and state != status_filter:
            continue

        conf = run.get("conf") or {}
        is_manual = conf.get("triggered_from") == "kharon"
        if type_filter == "Manual" and not is_manual:
            continue
        if type_filter == "Programado" and is_manual:
            continue

        if mon_client != "Todos":
            dag_id = run.get("dag_id", "")
            if mon_client.lower() not in dag_id.lower():
                continue

        exec_date_str = run.get("execution_date") or run.get("start_date")
        if exec_date_str:
            try:
                exec_dt = datetime.fromisoformat(str(exec_date_str).replace("Z", "+00:00"))
                if exec_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

        filtered.append(run)

    total_f = len(filtered)
    success_f = sum(1 for r in filtered if r.get("state") == "success")
    failed_f = sum(1 for r in filtered if r.get("state") == "failed")
    running_f = sum(1 for r in filtered if r.get("state") == "running")

    col1, col2, col3, col4 = st.columns(4)
    for col, label, value, color in [
        (col1, "Total Ejecuciones", total_f, "#4a1a8a"),
        (col2, "Exitosas", success_f, "#198754"),
        (col3, "Fallidas", failed_f, "#dc3545"),
        (col4, "En ejecución", running_f, "#fd7e14"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader(f"Ejecuciones ({len(filtered)} resultados)")

    for run in filtered[:50]:
        col_state, col_dag, col_date, col_type, col_run = st.columns([1, 2, 2, 1, 2])
        with col_state:
            render_status_badge(run.get("state", "unknown"))
        with col_dag:
            st.markdown(f"**{run.get('dag_id', '—')}**")
        with col_date:
            exec_date = run.get("execution_date") or run.get("start_date", "—")
            try:
                dt = datetime.fromisoformat(str(exec_date).replace("Z", "+00:00"))
                st.caption(dt.strftime("%d/%m/%Y %H:%M"))
            except (ValueError, TypeError):
                st.caption(str(exec_date))
        with col_type:
            conf = run.get("conf") or {}
            if conf.get("triggered_from") == "kharon":
                st.caption("🔘 Manual")
            else:
                st.caption("⏰ Programado")
        with col_run:
            st.caption(run.get("dag_run_id", "")[:20] + "...")


# ─── Page 5: Salud por Cliente ────────────────────────────────────────────────

def _page_health_by_client() -> None:
    st.title("❤️ Salud por Cliente")

    monitoring_data = []
    monitoring_dir = getattr(Config, "MONITORING_DIR", None)
    if monitoring_dir:
        import pathlib
        mon_path = pathlib.Path(monitoring_dir)
        if mon_path.exists():
            json_files = sorted(mon_path.glob("*.json"), reverse=True)
            if json_files:
                latest = json_files[0]
                try:
                    with open(latest, "r") as f:
                        monitoring_data = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    st.warning(f"Error al leer datos de monitoreo: {e}")

    if not monitoring_data:
        st.info("No hay datos de monitoreo disponibles. Ejecutá el monitoreo primero.")
        return

    grouped = {}
    for entry in monitoring_data:
        client_name = entry.get("client", "Sin cliente")
        grouped.setdefault(client_name, []).append(entry)

    for client_name, scripts in grouped.items():
        total_scripts = len(scripts)
        healthy_count = sum(1 for s in scripts if s.get("status") == "healthy")
        unhealthy_count = sum(1 for s in scripts if s.get("status") == "unhealthy")

        health_pct = (healthy_count / total_scripts * 100) if total_scripts > 0 else 0
        bar_color = "#198754" if health_pct >= 80 else "#fd7e14" if health_pct >= 50 else "#dc3545"

        with st.container():
            col_header, col_bar = st.columns([2, 3])
            with col_header:
                st.markdown(f"### 🏢 {client_name}")
                st.caption(f"{total_scripts} scripts — {healthy_count} saludables, {unhealthy_count} con problemas")

            with col_bar:
                st.markdown(
                    f'<div class="health-bar">'
                    f'<div class="health-bar-fill" style="width:{health_pct:.0f}%;background:{bar_color};"></div>'
                    f'</div>'
                    f'<span style="font-size:0.75em;color:{bar_color};">{health_pct:.0f}% saludable</span>',
                    unsafe_allow_html=True,
                )

            with st.expander(f"Ver detalle de {client_name}"):
                for script in scripts:
                    col_name, col_health, col_detail = st.columns([2, 1, 2])
                    with col_name:
                        st.markdown(f"**{script.get('script_name', script.get('dag_id', '—'))}**")
                        if script.get("criticality"):
                            render_criticality_badge(script["criticality"])
                    with col_health:
                        render_health_indicator({
                            "status": script.get("status", "unknown"),
                            "detail": script.get("detail", ""),
                        })
                    with col_detail:
                        if script.get("last_run"):
                            st.caption(f"Última ejecución: {script['last_run']}")
                        if script.get("consecutive_failures", 0) > 0:
                            st.caption(f"⚠️ {script['consecutive_failures']} fallos consecutivos")
                        if script.get("success_rate") is not None:
                            st.caption(f"Tasa de éxito: {script['success_rate']:.1%}")
                    st.markdown("---")

        st.markdown("---")


# ─── Page 6: Nuevo Script ─────────────────────────────────────────────────────

def _page_new_script() -> None:
    st.title("➕ Nuevo Script")

    clients = _get_clients()
    if not clients:
        st.warning("No hay clientes registrados. Creá uno primero en ⚙️ Configuración.")

    try:
        client = _get_airflow_client()
        existing_dags = client.list_dags(limit=200)
    except AirflowClientError:
        existing_dags = []

    existing_scripts = [
        {"name": d.get("dag_id", "")}
        for d in existing_dags
        if d.get("dag_id", "").startswith("kharon_")
    ]

    result = render_script_form(clients, existing_scripts)

    if result:
        with st.spinner("Generando DAG..."):
            try:
                generator = _get_dag_generator()
                generator.generate(result)
                st.balloons()
                st.success(f"✅ Script **{result.get('name', '')}** creado exitosamente.")
                st.info("El DAG se generará en el próximo ciclo de parsing de Airflow (~30s).")
            except Exception as e:
                st.error(f"Error al generar el DAG: {e}")


# ─── Page 7: Configuración ────────────────────────────────────────────────────

def _page_configuration() -> None:
    st.title("⚙️ Configuración")

    col_config, col_health = st.columns(2)

    with col_config:
        st.subheader("Configuración Actual")
        env_info = {
            "app_name": config.APP_NAME,
            "company": config.COMPANY,
            "airflow_url": config.AIRFLOW_BASE_URL,
            "airflow_host": config.AIRFLOW_HOST,
            "airflow_port": config.AIRFLOW_PORT,
            "kharon_port": config.KHARON_PORT,
            "project_root": str(config.PROJECT_ROOT),
            "dags_dir": str(config.DAGS_DIR),
            "external_scripts_dir": str(config.EXTERNAL_SCRIPTS_DIR),
        }
        for key, val in env_info.items():
            st.markdown(f"**{key}:** `{val}`")

    with col_health:
        st.subheader("Estado de Airflow")
        try:
            client = _get_airflow_client()
            health = client.health_check()
            metadatabase = health.get("metadatabase", {})
            scheduler = health.get("scheduler", {})
            st.markdown(f"**Metadatabase:** {metadatabase.get('status', '—')}")
            st.markdown(f"**Scheduler:** {scheduler.get('status', '—')}")
            st.markdown(f"**Último heartbeat:** {scheduler.get('latest_scheduler_heartbeat', '—')}")
        except AirflowClientError as e:
            st.error(f"Airflow no disponible: {e}")

    st.divider()

    st.subheader("Clientes Registrados")
    clients = _get_clients()
    if clients:
        cols_per_row = 3
        for i in range(0, len(clients), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(clients):
                    with col:
                        render_client_badge(clients[i + j])
    else:
        st.info("No hay clientes registrados.")

    st.divider()

    st.subheader("Agregar Cliente")
    with st.form("add_client_form"):
        new_name = st.text_input("Nombre del cliente *", placeholder="ej: ACME Corp")
        new_color = st.color_picker("Color", value="#4a1a8a", key="new_client_color")
        new_icon = st.text_input("Icono (emoji)", value="🏢", key="new_client_icon")
        new_description = st.text_area("Descripción", placeholder="Descripción del cliente...", key="new_client_desc")

        submitted = st.form_submit_button("Crear Cliente")
        if submitted and new_name:
            try:
                cm = _get_client_manager()
                cm.add_client({
                    "name": new_name,
                    "color": new_color,
                    "icon": new_icon,
                    "description": new_description,
                })
                st.toast(f"✅ Cliente '{new_name}' creado exitosamente", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear cliente: {e}")
        elif submitted and not new_name:
            st.warning("El nombre es obligatorio.")

    st.divider()

    st.subheader("Información del Registro")
    try:
        cm = _get_client_manager()
        registry_info = cm.get_registry_info()
        st.json(registry_info)
    except Exception as e:
        st.info(f"No se pudo obtener información del registro: {e}")


# ─── Page Router ───────────────────────────────────────────────────────────────

_PAGE_HANDLERS = {
    "📊 Tablero": _page_dashboard,
    "🚀 Ejecutar Scripts": _page_execute_scripts,
    "📄 Ver Logs": _page_view_logs,
    "📡 Monitoreo Global": _page_global_monitoring,
    "❤️ Salud por Cliente": _page_health_by_client,
    "➕ Nuevo Script": _page_new_script,
    "⚙️ Configuración": _page_configuration,
}


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Kharōn — Arkh-Ur",
        page_icon="⚓",
        layout="wide",
    )
    st.markdown(_KHARON_CSS, unsafe_allow_html=True)

    _init_session_state()
    _render_sidebar()

    current = st.session_state.current_page
    handler = _PAGE_HANDLERS.get(current)
    if handler:
        handler()
    else:
        st.error(f"Página no encontrada: {current}")


if __name__ == "__main__":
    main()
