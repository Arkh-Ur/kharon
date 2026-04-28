import json
import os
import random
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from airflow_client import AirflowClient, AirflowClientError
from client_manager import ClientManager
from dag_generator import DAGGenerator
import config
from utils import describe_cron, extract_primary_color
from components.dag_card import render_dag_card
from components.log_viewer import render_log_viewer
from components.script_form import render_script_form
from components.status_badge import (
    _client_icon_html,
    render_client_badge,
    render_criticality_badge,
    render_health_indicator,
    render_status_badge,
)

_STATIC_DIR = Path(__file__).parent / "static"


def _svg_to_data_uri(filename: str) -> str:
    svg_path = _STATIC_DIR / filename
    svg_bytes = svg_path.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


_KHARON_LOGO_URI = _svg_to_data_uri("kharon-logo-text.svg")
_KHARON_ICON_URI = _svg_to_data_uri("kharon-logo.svg")
_ARKHUR_LOGO_URI = _svg_to_data_uri("arkh-ur-logo-text.svg")


# ─── Custom CSS ────────────────────────────────────────────────────────────────

_KHARON_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root {
        --primary: #3b82f6;
        --primary-dark: #374151;
        --primary-light: #545B67;
        --secondary: #1E2632;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
        --bg-dark: #0A0F18;
        --bg-card: #1E2632;
        --text-dark: #e5e7eb;
        --text-muted: #9ca3af;
        --border-color: #545B67;
    }

    .stApp {
        background: radial-gradient(ellipse at 50% 0%, #131923 0%, #0A0F18 70%);
    }
    
    .stApp, .stMarkdown, .stTextInput, .stSelectbox, .stTextArea {
        font-family: 'DM Sans', sans-serif !important;
    }
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A0F18 0%, #131923 100%);
    }
    [data-testid="stSidebar"] > div > div {
        display: flex;
        flex-direction: column;
    }
    [data-testid="stSidebar"] section[data-testid="stSidebarContent"] {
        flex: 1;
    }
    [data-testid="stSidebar"] .stButton {
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton .element-container,
    [data-testid="stSidebar"] .stButton [data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] .stButton [data-testid="stBaseButton-primary"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        display: block !important;
    }
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        background: rgba(30, 38, 50, 0.8);
        border: 1px solid #545B67;
        color: #e5e7eb !important;
        text-align: left;
        padding: 10px 16px;
        border-radius: 6px;
        transition: all 0.2s;
        display: block;
    }
    /* Active sidebar nav button — blue left border accent */
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        background: rgba(59,130,246,0.12) !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        border-left: 3px solid #3b82f6 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        text-align: left;
        padding: 10px 16px;
        border-radius: 6px;
        transition: all 0.2s;
        display: block;
    }

    .metric-card {
        background: #1E2632;
        border-radius: 10px;
        padding: 20px;
        padding-top: 17px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        border: 1px solid #545B67;
        text-align: center;
        border-top: 3px solid var(--card-accent, #3b82f6);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
    .metric-card .metric-value {
        font-size: 1.6em;
        font-weight: 800;
        line-height: 1.1;
    }
    .metric-card .metric-label {
        font-size: 0.9em;
        color: #9ca3af;
        margin-top: 4px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(55, 65, 81, 0.6);
        border-color: #545B67;
    }
    
    .stButton > button:not(:disabled) {
        transition: all 0.15s ease !important;
    }
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: #3b82f6 !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: #2563eb !important;
        border-color: #2563eb !important;
        box-shadow: 0 0 16px rgba(59,130,246,0.3);
    }
    .stButton > button:disabled {
        opacity: 0.4 !important;
    }
    [data-testid="stExpander"] > div:first-child:hover {
        background: rgba(59,130,246,0.05);
        border-radius: 8px;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.3); }
    }

    .health-bar {
        height: 8px;
        border-radius: 4px;
        background: #1E2632;
        overflow: hidden;
        margin-top: 4px;
    }
    .health-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.4s ease;
    }

    h1, h2, h3 {
        color: #e5e7eb !important;
    }

    .stAlert {
        border-radius: 8px;
    }

    header[data-testid="stHeader"] {
        background: none !important;
        box-shadow: none !important;
    }
    header[data-testid="stHeader"] [data-testid="stHeaderActionElements"] {
        display: none !important;
    }
    [data-testid="stToolbar"] {
        display: flex !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebar"] .sidebar-footer {
        margin-top: auto !important;
        padding-top: 16px !important;
    }
    [data-testid="stSidebar"] .sidebar-footer > div {
        position: sticky !important;
        bottom: 0 !important;
    }

    /* ── Mobile responsive (< 768px) ────────────────────────────────── */
    @media only screen and (max-width: 768px) {
        .metric-card {
            padding: 14px 10px;
            padding-top: 12px;
        }
        .metric-card .metric-value {
            font-size: 1.3em;
        }
        .metric-card .metric-label {
            font-size: 0.8em;
        }
        .metric-card > div:first-child {
            font-size: 1.1em !important;
        }
        .metric-card:hover {
            transform: none;
        }
        h1 {
            font-size: 1.4em !important;
        }
        h2 {
            font-size: 1.15em !important;
        }
        h3 {
            font-size: 1.05em !important;
        }
        .stApp {
            background: #0A0F18;
        }
        .stMarkdown p {
            font-size: 0.9em;
        }
        /* Sidebar mobile adjustments */
        [data-testid="stSidebar"] > div:first-child {
            width: 260px !important;
            max-width: 85vw !important;
        }
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
        [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
            padding: 12px 14px;
            font-size: 0.95em;
        }
        /* Health bars smaller on mobile */
        .health-bar {
            height: 6px;
        }
        /* Summary bar scrollable */
        .kharon-summary-bar {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            flex-wrap: nowrap !important;
        }
        /* Status dot + label row */
        .kharon-process-header {
            flex-wrap: wrap;
        }
    }
    @media only screen and (max-width: 480px) {
        .metric-card .metric-value {
            font-size: 1.1em;
        }
        .metric-card > div:first-child {
            font-size: 0.9em !important;
            margin-bottom: 2px !important;
        }
    }
</style>
"""


# ─── Initialization ────────────────────────────────────────────────────────────

def _init_session_state() -> None:
    defaults = {
        "current_page": "📊 Tablero",
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
        clients_dict = cm.load_clients()
        from dataclasses import asdict
        return [asdict(c) for c in clients_dict.values()]
    except Exception:
        return []


def _is_kharon_dag(dag: dict) -> bool:
    """True si el DAG pertenece a Kharōn — por prefijo O por tag kharon-auto."""
    if dag.get("dag_id", "").startswith("kharon_"):
        return True
    return any(t.get("name", "") == "kharon-auto" for t in dag.get("tags", []))


def _dag_run_date(run: dict) -> str:
    """Fecha canónica de un run (Airflow 3.x renombró execution_date → logical_date)."""
    return (
        run.get("logical_date")
        or run.get("execution_date")
        or run.get("start_date")
        or ""
    )


def _dag_client_id(dag: dict) -> str:
    """Extrae el client_id desde los tags del DAG (tag 'client_{id}')."""
    for tag in dag.get("tags", []):
        name = tag.get("name", "")
        if name.startswith("client_"):
            return name[len("client_"):]
    return ""


def _status_dot_html(state: str) -> str:
    """CSS circle status indicator — no emoji, cross-platform consistent."""
    colors = {
        "success": "#22c55e", "failed": "#ef4444",
        "running": "#3b82f6", "queued": "#f59e0b", "never": "#545B67",
    }
    color = colors.get(state, "#545B67")
    pulse = "animation:pulse-dot 2s infinite;" if state == "running" else ""
    return (
        f'<span style="'
        f'display:inline-block;width:10px;height:10px;'
        f'border-radius:50%;background:{color};'
        f'{pulse}'
        f'vertical-align:middle;margin-right:6px;'
        f'"></span>'
    )


# ─── Sidebar ───────────────────────────────────────────────────────────────────

_PAGES = [
    "📊 Tablero",
    "⚙️ Procesos",
    "📄 Logs",
    "📡 Monitoreo",
    "❤️ Salud",
    "➕ Nuevo Script",
    "🔧 Configuración",
]

_PAGE_MAP = {p: p for p in _PAGES}


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f'<div style="text-align:center; padding: 8px 0 4px 0;">'
            f'<img src="{_KHARON_LOGO_URI}" alt="Kharōn" style="width:180px; margin:0 auto; display:block;" />'
            f'</div>'
            f'<div style="text-align:center; padding: 0 0 8px 0;">'
            f'<span style="font-size:0.7em; color:#9ca3af; letter-spacing:0.5px;">Sistema de Monitoreo y Ejecución</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        for page in _PAGES:
            is_active = st.session_state.current_page == page
            icon, label = page.split(" ", 1)
            active_cls = "nav-btn-active" if is_active else "nav-btn"
            if st.button(
                f"{icon} {label}",
                key=f"nav_{page}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.current_page = page
                st.rerun()

        st.divider()
        st.markdown(
            f'<div class="sidebar-footer" style="text-align:center; padding: 4px 0;">'
            f'<img src="{_ARKHUR_LOGO_URI}" alt="Arkh-Ur" style="width:120px; margin:0 auto; display:block; opacity:0.7;" />'
            f'<span style="font-size:0.6em; color:#545B67; letter-spacing:0.3px;">© {datetime.now().year}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ─── Page 1: Tablero ──────────────────────────────────────────────────────────

def _page_dashboard() -> None:
    st.title("📊 Tablero")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Vista general del estado de ejecuciones</p>", unsafe_allow_html=True)

    _PLOTLY_LAYOUT = {
        "paper_bgcolor": "#0A0F18",
        "plot_bgcolor": "#131923",
        "font_color": "#e5e7eb",
        "font_family": "JetBrains Mono, monospace",
        "margin": dict(l=20, r=20, t=40, b=20),
        "xaxis": dict(gridcolor="#1E2632", zerolinecolor="#545B67"),
        "yaxis": dict(gridcolor="#1E2632", zerolinecolor="#545B67"),
    }

    _STATE_COLORS = {
        "success": "#22c55e",
        "running": "#3b82f6",
        "failed": "#ef4444",
        "queued": "#f59e0b",
    }

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.warning(f"Airflow no disponible: {e}")
        col1, col2, col3, col4 = st.columns(4)
        _placeholder_data = [
            (col1, "—", "Total Scripts", "#3b82f6", "📦"),
            (col2, "—", "En Ejecución", "#3b82f6", "⚡"),
            (col3, "—", "Tasa de Éxito", "#545B67", "✅"),
            (col4, "—", "Duración Prom.", "#545B67", "⏱"),
        ]
        for col, value, label, color, icon in _placeholder_data:
            with col:
                st.markdown(
                    f'<div class="metric-card" style="--card-accent:{color};">'
                    f'<div style="font-size:1.4em;margin-bottom:4px;">{icon}</div>'
                    f'<div class="metric-value" style="color:{color}">{value}</div>'
                    f'<div class="metric-label">{label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        fig_placeholder = go.Figure()
        fig_placeholder.update_layout(**_PLOTLY_LAYOUT, height=400, title_text="Sin datos (Airflow no disponible)")
        st.plotly_chart(fig_placeholder, use_container_width=True)
        return

    if not dags:
        st.info("No hay DAGs registrados.")
        return

    kharon_dags = [
        d for d in dags
        if d.get("dag_id", "").startswith("kharon_")
        or any(t.get("name", "") == "kharon-auto" for t in d.get("tags", []))
    ]

    if not kharon_dags:
        st.info("No hay DAGs de Kharōn registrados.")
        return

    dag_runs_map = {}
    dag_client_map = {}
    for dag in kharon_dags:
        dag_id = dag.get("dag_id", "")
        try:
            runs = client.list_dag_runs(dag_id, limit=10)
            dag_runs_map[dag_id] = runs
        except AirflowClientError:
            dag_runs_map[dag_id] = []

        client_name = None
        for tag in dag.get("tags", []):
            tag_name = tag.get("name", "")
            if tag_name.startswith("client_"):
                client_name = tag_name.replace("client_", "")
                break
        dag_client_map[dag_id] = client_name or "sin cliente"

    all_runs = []
    for dag_id, runs in dag_runs_map.items():
        for run in runs:
            all_runs.append({**run, "dag_id": dag_id, "client": dag_client_map.get(dag_id, "sin cliente")})

    total_scripts = len(kharon_dags)
    running_count = sum(1 for r in all_runs if r.get("state") == "running")

    completed_runs = [r for r in all_runs if r.get("state") in ("success", "failed")]
    success_count = sum(1 for r in completed_runs if r.get("state") == "success")
    success_rate = (success_count / len(completed_runs) * 100) if completed_runs else 0.0

    durations = []
    for r in completed_runs:
        start = r.get("start_date")
        end = r.get("end_date")
        if start and end:
            try:
                dt_start = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                dt_end = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
                durations.append((dt_end - dt_start).total_seconds())
            except (ValueError, TypeError):
                pass
    avg_duration_seconds = sum(durations) / len(durations) if durations else 0
    avg_min = int(avg_duration_seconds // 60)
    avg_sec = int(avg_duration_seconds % 60)

    col1, col2, col3, col4 = st.columns(4)
    _metric_data = [
        (col1, f"{total_scripts}", "Total Scripts", "#3b82f6", "📦"),
        (col2, f"{running_count}", "En Ejecución", "#3b82f6", "⚡"),
        (col3, f"{success_rate:.1f}%", "Tasa de Éxito", "#22c55e", "✅"),
        (col4, f"{avg_min}m {avg_sec}s", "Duración Prom.", "#f59e0b", "⏱"),
    ]
    for col, value, label, color, icon in _metric_data:
        with col:
            st.markdown(
                f'<div class="metric-card" style="--card-accent:{color};">'
                f'<div style="font-size:1.4em;margin-bottom:4px;">{icon}</div>'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    all_runs.sort(
        key=lambda r: r.get("start_date") or r.get("logical_date") or "",
        reverse=True,
    )
    recent_20 = all_runs[:20]

    if recent_20:
        gantt_fig = go.Figure()
        y_labels = []
        seen_dag_ids = []
        for run in reversed(recent_20):
            dag_id = run.get("dag_id", "—")
            if dag_id not in seen_dag_ids:
                seen_dag_ids.append(dag_id)
            y_idx = seen_dag_ids.index(dag_id)
            y_labels.append(dag_id)

            state = run.get("state", "queued")
            color = _STATE_COLORS.get(state, "#545B67")

            start_str = run.get("start_date") or run.get("logical_date")
            end_str = run.get("end_date")

            try:
                dt_start = datetime.fromisoformat(str(start_str).replace("Z", "+00:00")) if start_str else datetime.now()
            except (ValueError, TypeError):
                dt_start = datetime.now()

            if end_str and state in ("success", "failed"):
                try:
                    dt_end = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    dt_end = dt_start + timedelta(minutes=1)
            elif state == "running":
                dt_end = datetime.now()
            else:
                dt_end = dt_start + timedelta(minutes=1)

            duration_s = (dt_end - dt_start).total_seconds()
            start_epoch = dt_start.timestamp()

            state_label = {"success": "✓", "failed": "✗", "running": "⟳", "queued": "◷"}.get(state, "?")

            gantt_fig.add_trace(go.Bar(
                name=dag_id,
                orientation="h",
                x=[max(duration_s, 5)],
                y=[dag_id],
                base=[start_epoch],
                text=[state_label],
                textposition="inside",
                marker_color=color,
                hovertext=(
                    f"<b>{dag_id}</b><br>"
                    f"Estado: {state}<br>"
                    f"Inicio: {dt_start.strftime('%H:%M:%S')}<br>"
                    f"Duración: {int(duration_s // 60)}m {int(duration_s % 60)}s"
                ),
                hoverinfo="text",
                showlegend=False,
            ))

        gantt_fig.update_layout(
            **_PLOTLY_LAYOUT,
            title=dict(text="Timeline de Ejecuciones", font=dict(size=16, color="#e5e7eb")),
            barmode="overlay",
            height=max(300, len(seen_dag_ids) * 40 + 80),
            xaxis_showticklabels=False,
            xaxis_title="",
            yaxis_title="",
            yaxis_autorange="reversed",
            bargap=0.3,
        )
        st.plotly_chart(gantt_fig, use_container_width=True)
    else:
        st.info("No hay ejecuciones recientes para el timeline.")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        client_success = {}
        client_failed = {}
        for r in all_runs:
            c = r.get("client", "sin cliente")
            if r.get("state") == "success":
                client_success[c] = client_success.get(c, 0) + 1
            elif r.get("state") == "failed":
                client_failed[c] = client_failed.get(c, 0) + 1

        if client_success or client_failed:
            all_clients = sorted(set(list(client_success.keys()) + list(client_failed.keys())))
            bar_fig = go.Figure(data=[
                go.Bar(
                    name="Exitosos",
                    x=all_clients,
                    y=[client_success.get(c, 0) for c in all_clients],
                    marker_color="#22c55e",
                ),
                go.Bar(
                    name="Fallidos",
                    x=all_clients,
                    y=[client_failed.get(c, 0) for c in all_clients],
                    marker_color="#ef4444",
                ),
            ])
            bar_fig.update_layout(
                **_PLOTLY_LAYOUT,
                title=dict(text="Ejecuciones por Cliente", font=dict(size=16, color="#e5e7eb")),
                barmode="group",
                height=350,
                legend=dict(
                    bgcolor="#131923",
                    font=dict(color="#e5e7eb", size=11),
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                xaxis_title="",
                yaxis_title="Ejecuciones",
            )
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("Sin datos de clientes.")

    with bottom_right:
        state_counts = {}
        for r in all_runs:
            s = r.get("state", "unknown")
            state_counts[s] = state_counts.get(s, 0) + 1

        if state_counts:
            labels = list(state_counts.keys())
            values = list(state_counts.values())
            colors = [_STATE_COLORS.get(s, "#545B67") for s in labels]

            donut_fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker_colors=colors,
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="radial",
                textfont=dict(color="#e5e7eb", size=14),
                hoverinfo="label+value+percent",
                sort=False,
            )])
            donut_fig.update_layout(
                **_PLOTLY_LAYOUT,
                title=dict(text="Distribución de Estados", font=dict(size=16, color="#e5e7eb")),
                height=350,
                showlegend=True,
                legend=dict(
                    bgcolor="#131923",
                    font=dict(color="#e5e7eb", size=11),
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                ),
            )
            st.plotly_chart(donut_fig, use_container_width=True)
        else:
            st.info("Sin datos de estados.")


# ─── Page: Procesos ────────────────────────────────────────────────────────────

def _page_processes() -> None:
    st.title("⚙️ Procesos")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Gestión y monitoreo de scripts</p>", unsafe_allow_html=True)

    try:
        st_autorefresh = getattr(st, "autorefresh", None)
        if callable(st_autorefresh):
            st_autorefresh(interval=30000)
    except Exception:
        pass

    clients = _get_clients()
    if not clients:
        st.warning("No hay clientes registrados.")
        return

    client_options = {c.get("name", ""): c.get("id", "") for c in clients}
    client_names = ["Todos"] + list(client_options.keys())
    selected_client = st.selectbox("🏢 Filtrar por cliente", client_names, key="proc_client_filter")

    try:
        client = _get_airflow_client()
        all_dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.warning(f"No se pudo conectar con Airflow: {e}")
        return

    kharon_dags = [
        d for d in all_dags
        if any(t.get("name", "") == "kharon-auto" for t in d.get("tags", []))
    ]

    if selected_client != "Todos":
        selected_client_id = client_options.get(selected_client, selected_client)
        filtered_dags = []
        for dag in kharon_dags:
            tags = [t.get("name", "") for t in dag.get("tags", [])]
            if f"client_{selected_client_id}" in tags:
                filtered_dags.append(dag)
        kharon_dags = filtered_dags

    if not kharon_dags:
        st.info("No hay procesos para el cliente seleccionado.")
        return

    # ── Summary bar ──
    _summary_colors = {
        "success": "#22c55e", "failed": "#ef4444",
        "running": "#3b82f6", "queued": "#f59e0b", "never": "#545B67",
    }
    _state_counts = {}
    for dag in kharon_dags:
        _did = dag.get("dag_id", "")
        try:
            _runs_check = client.list_dag_runs(_did, limit=1)
            _s = _runs_check[0].get("state", "never") if _runs_check else "never"
        except Exception:
            _s = "never"
        _state_counts[_s] = _state_counts.get(_s, 0) + 1

    _label_map = {
        "success": "OK", "failed": "Failed", "running": "Running",
        "queued": "En cola", "never": "Sin ejecución",
    }
    _summary_parts = []
    for _state, _count in sorted(_state_counts.items()):
        _c = _summary_colors.get(_state, "#545B67")
        _l = _label_map.get(_state, _state)
        _summary_parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:14px;">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{_c};display:inline-block;"></span>'
            f'<span style="color:{_c};font-weight:600;">{_count}</span>'
            f'<span style="color:#9ca3af;font-size:0.85em;">{_l}</span>'
            f'</span>'
        )
    st.markdown(
        f'<div class="kharon-summary-bar" style="background:#131923;border-radius:8px;padding:12px 16px;margin-bottom:16px;'
        f'border:1px solid #2d3748;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">'
        f'<span style="color:#e5e7eb;font-weight:600;margin-right:8px;">Resumen:</span>'
        + "".join(_summary_parts) +
        f'<span style="color:#545B67;margin-left:auto;font-size:0.85em;">{len(kharon_dags)} procesos</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for dag in kharon_dags:
        dag_id = dag.get("dag_id", "")
        desc = dag.get("description") or dag_id
        schedule = dag.get("schedule_interval", {})
        schedule_val = schedule.get("value", "") if isinstance(schedule, dict) else ""

        if schedule_val == "@continuous":
            mode = "🔄 Continuo — se re-ejecuta al terminar"
        elif not schedule_val:
            mode = "🎯 Demanda — solo ejecución manual"
        else:
            mode = f"📅 {describe_cron(schedule_val)}"

        try:
            runs = client.list_dag_runs(dag_id, limit=15)
        except AirflowClientError:
            runs = []

        last_state = runs[0].get("state", "never") if runs else "never"
        # CSS-based status dot above the expander
        st.markdown(
            f'<div class="kharon-process-header" style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">'
            f'{_status_dot_html(last_state)}'
            f'<span style="font-weight:600;color:#e5e7eb;">{desc}</span> '
            f'<span style="color:#9ca3af;font-size:0.85em;">— {mode}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"  Ver detalles ({dag_id})"):

            if runs:
                _color_map = {
                    "success": "#22c55e",
                    "failed": "#ef4444",
                    "running": "#3b82f6",
                    "queued": "#f59e0b",
                }
                df_data = []
                for r in runs:
                    start_str = r.get("start_date") or r.get("logical_date", "")
                    end_str = r.get("end_date", "")
                    state = r.get("state", "")
                    duration = 0.0
                    if start_str:
                        try:
                            s = datetime.fromisoformat(str(start_str).replace("Z", "+00:00"))
                            if end_str:
                                e = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
                            elif state == "running":
                                e = datetime.now(s.tzinfo)
                            else:
                                e = s
                            duration = max((e - s).total_seconds(), 0.0)
                        except (ValueError, TypeError):
                            pass

                    run_id_full = r.get("dag_run_id", "")
                    if "__" in run_id_full:
                        time_part = run_id_full.split("__", 1)[1]
                        label = time_part.split("T")[1][:8] if "T" in time_part else time_part[:10]
                    else:
                        label = run_id_full[-10:] if run_id_full else f"#{len(df_data)}"

                    df_data.append({
                        "run": label,
                        "display_dur": max(duration, 0.5),  # mínimo visible
                        "real_dur": duration,
                        "state": state,
                    })

                df = pd.DataFrame(df_data)
                fig = go.Figure(go.Bar(
                    x=df["run"],
                    y=df["display_dur"],
                    marker_color=[_color_map.get(s, "#545B67") for s in df["state"]],
                    text=[f"{d:.0f}s" if d >= 1 else "<1s" for d in df["real_dur"]],
                    textposition="auto",
                    hovertemplate="%{x}<br>%{text}<extra></extra>",
                ))
                fig.update_layout(
                    title="Historial de Ejecuciones",
                    paper_bgcolor="#131923",
                    plot_bgcolor="#0A0F18",
                    font_color="#e5e7eb",
                    height=300,
                    xaxis_title="",
                    yaxis_title="Segundos",
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{dag_id}")
            else:
                st.info("Sin ejecuciones previas.")

            col_exec, col_log, col_del = st.columns(3)

            with col_exec:
                if st.button("▶ Ejecutar", key=f"exec_{dag_id}", use_container_width=True):
                    try:
                        result = client.trigger_dag(dag_id)
                        st.success(f"✅ Ejecución iniciada: {result.get('dag_run_id', '')}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al ejecutar: {e}")

            with col_log:
                if runs:
                    last_run_id = runs[0].get("dag_run_id", "")
                    _log_key = f"log_data_{dag_id}"
                    if st.button("📄 Ver Log", key=f"log_{dag_id}", use_container_width=True):
                        try:
                            tasks = client.list_task_instances(dag_id, last_run_id)
                            parts = []
                            for task in tasks:
                                task_id = task.get("task_id", "")
                                task_state = task.get("state")
                                try_n = int(task.get("try_number") or 0)
                                _NO_LOG = {"queued", "scheduled", "no_status", "none", None}
                                if task_state in _NO_LOG or try_n == 0:
                                    parts.append(f"=== {task_id} === [{task_state or 'sin estado'}] sin log todavía")
                                    continue
                                try_n = max(try_n, 1)
                                try:
                                    log = client.get_task_log(dag_id, last_run_id, task_id, try_n)
                                    if log:
                                        parts.append(f"=== {task_id} (intento {try_n}) ===\n{log}")
                                except AirflowClientError as log_err:
                                    parts.append(f"=== {task_id} === Error: {log_err}")
                            st.session_state[_log_key] = "\n\n".join(parts) if parts else "(sin contenido de log)"
                        except Exception as exc:
                            st.session_state[_log_key] = f"Error al obtener log: {exc}"

            # Log persiste entre reruns usando session_state — se muestra en ancho completo
            _log_key = f"log_data_{dag_id}"
            if _log_key in st.session_state:
                _col_title, _col_close = st.columns([5, 1])
                with _col_title:
                    st.markdown("**📄 Log — última ejecución**")
                with _col_close:
                    if st.button("✕ Cerrar", key=f"close_log_{dag_id}"):
                        del st.session_state[_log_key]
                        st.rerun()
                st.code(st.session_state[_log_key], language="log")

            with col_del:
                if st.button("🗑 Eliminar", key=f"del_{dag_id}", use_container_width=True):
                    st.session_state[f"confirm_del_{dag_id}"] = True

            if st.session_state.get(f"confirm_del_{dag_id}"):
                st.warning(f"⚠️ ¿Eliminar el proceso **{dag_id}**? Se borrará el DAG y su archivo. Esta acción no se puede deshacer.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Confirmar eliminación", key=f"del_yes_{dag_id}", type="primary"):
                        _errors = []
                        try:
                            generator = _get_dag_generator()
                            generator.delete_dag(dag_id)
                        except Exception as exc:
                            _errors.append(f"Archivo/registro: {exc}")
                        try:
                            client.pause_dag(dag_id, paused=True)
                            client.delete_dag(dag_id)
                        except Exception as exc:
                            _errors.append(f"Airflow API: {exc}")
                        st.session_state.pop(f"confirm_del_{dag_id}", None)
                        if _errors:
                            st.error("Eliminado con errores parciales: " + " | ".join(_errors))
                        else:
                            st.toast(f"🗑️ Proceso '{dag_id}' eliminado", icon="🗑️")
                        st.rerun()
                with col_no:
                    if st.button("Cancelar", key=f"del_no_{dag_id}"):
                        st.session_state.pop(f"confirm_del_{dag_id}", None)
                        st.rerun()


# ─── Page: Ver Logs ───────────────────────────────────────────────────────────

def _page_view_logs() -> None:
    st.title("📄 Ver Logs")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Exploración detallada de logs de ejecución</p>", unsafe_allow_html=True)

    try:
        client = _get_airflow_client()
        dags = client.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    kharon_dags = [d for d in dags if _is_kharon_dag(d)]
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
        exec_date = _dag_run_date(run)
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

    _STATE_ICON = {
        "success": "✅", "failed": "❌", "running": "🔄",
        "queued": "⏳", "scheduled": "📅", "skipped": "⏭️",
        "up_for_retry": "🔁", "upstream_failed": "⚠️",
    }
    _task_map = {t.get("task_id", ""): t for t in tasks if t.get("task_id")}

    def _task_label(tid: str) -> str:
        t = _task_map.get(tid, {})
        state = t.get("state", "?")
        icon = _STATE_ICON.get(state, "❓")
        try_n = t.get("try_number", 0)
        return f"{tid}  {icon} {state}  (intento {try_n})"

    selected_task = st.selectbox(
        "Seleccioná una tarea",
        options=list(_task_map.keys()),
        format_func=_task_label,
        key="log_task_select",
    )

    if not selected_task:
        return

    task_obj = _task_map[selected_task]
    task_state = task_obj.get("state")          # puede ser None (JSON null)
    try_number = int(task_obj.get("try_number") or 0)

    st.session_state.selected_task_id = selected_task

    _NO_LOG_STATES = {"queued", "scheduled", "no_status", "none", None}
    if task_state in _NO_LOG_STATES or try_number == 0:
        label = task_state or "sin estado"
        st.info(f"La tarea está en estado **{label}** (intento {try_number}) — aún no hay log disponible.")
        return

    try_number = max(try_number, 1)

    st.divider()

    try:
        log_content = client.get_task_log(selected_dag, selected_run, selected_task, try_number)
        render_log_viewer(log_content, auto_refresh=True)
    except AirflowClientError as e:
        st.error(f"Error al obtener log: {e}")


# ─── Page 4: Monitoreo Global ─────────────────────────────────────────────────

def _page_global_monitoring() -> None:
    st.title("📡 Monitoreo Global")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Seguimiento en tiempo real de todas las ejecuciones</p>", unsafe_allow_html=True)

    try:
        af = _get_airflow_client()
        dags = af.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    # Incluye DAGs por tag kharon-auto O prefijo kharon_ (DAGs manuales incluidos)
    kharon_dags = [d for d in dags if _is_kharon_dag(d)]

    # Construir mapa dag_id → client_id para filtrar por cliente usando tags
    dag_client_map: dict = {d.get("dag_id", ""): _dag_client_id(d) for d in kharon_dags}

    all_runs: list = []
    for dag in kharon_dags:
        dag_id = dag.get("dag_id", "")
        try:
            runs = af.list_dag_runs(dag_id, limit=15)
            for run in runs:
                run["dag_id"] = dag_id
                run["_client_id"] = dag_client_map.get(dag_id, "")
                all_runs.append(run)
        except AirflowClientError:
            continue

    all_runs.sort(key=lambda r: _dag_run_date(r), reverse=True)
    all_runs = all_runs[:200]

    # ── Filtros ──────────────────────────────────────────────────────────────────
    col_status, col_type, col_client, col_date = st.columns(4)
    with col_status:
        status_filter = st.selectbox(
            "Estado",
            options=["Todos", "success", "failed", "running", "queued"],
            key="mon_status",
        )
    with col_type:
        type_filter = st.selectbox(
            "Tipo", options=["Todos", "Manual", "Programado"], key="mon_type"
        )
    with col_client:
        _clients_list = _get_clients()
        client_names = ["Todos"] + [c.get("name", "") for c in _clients_list if c.get("name")]
        client_names = client_names if len(client_names) > 1 else ["Todos"]
        mon_client = st.selectbox("Cliente", options=client_names, key="mon_client")
    with col_date:
        days_back = st.number_input(
            "Últimos N días", min_value=1, max_value=90, value=7, key="mon_days"
        )

    cutoff = datetime.now().astimezone() - timedelta(days=days_back)

    # ── Aplicar filtros ───────────────────────────────────────────────────────────
    # Obtener el client_id del nombre seleccionado
    _clients = _get_clients()
    _name_to_id = {c.get("name", ""): c.get("id", "") for c in _clients}
    selected_client_id = _name_to_id.get(mon_client, "") if mon_client != "Todos" else ""

    filtered = []
    for run in all_runs:
        if status_filter != "Todos" and run.get("state", "") != status_filter:
            continue

        # Tipo: usa run_type de Airflow 3.x primero, después conf como fallback
        run_type = run.get("run_type", "")
        conf = run.get("conf") or {}
        is_manual = run_type == "manual" or conf.get("triggered_from") == "kharon"
        if type_filter == "Manual" and not is_manual:
            continue
        if type_filter == "Programado" and is_manual:
            continue

        # Cliente: comparar contra el client_id guardado en el run (desde tags)
        if selected_client_id and run.get("_client_id", "") != selected_client_id:
            continue

        date_str = _dag_run_date(run)
        if date_str:
            try:
                exec_dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                if exec_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

        filtered.append(run)

    # ── Métricas ──────────────────────────────────────────────────────────────────
    total_f = len(filtered)
    success_f = sum(1 for r in filtered if r.get("state") == "success")
    failed_f = sum(1 for r in filtered if r.get("state") == "failed")
    running_f = sum(1 for r in filtered if r.get("state") == "running")

    col1, col2, col3, col4 = st.columns(4)
    for col, label, value, color, icon in [
        (col1, "Total Ejecuciones", total_f, "#3b82f6", "📊"),
        (col2, "Exitosas", success_f, "#22c55e", "✅"),
        (col3, "Fallidas", failed_f, "#ef4444", "❌"),
        (col4, "En ejecución", running_f, "#f59e0b", "⚡"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card" style="--card-accent:{color};">'
                f'<div style="font-size:1.4em;margin-bottom:4px;">{icon}</div>'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader(f"Ejecuciones ({total_f} resultados)")

    if not filtered:
        st.info("No hay ejecuciones que coincidan con los filtros.")
        return

    for run in filtered[:50]:
        col_state, col_dag, col_client_col, col_date_col, col_type_col = st.columns([1, 2, 1, 2, 1])

        with col_state:
            render_status_badge(run.get("state", "unknown"))

        with col_dag:
            st.markdown(f"**{run.get('dag_id', '—')}**")

        with col_client_col:
            cid = run.get("_client_id", "")
            st.caption(cid or "—")

        with col_date_col:
            date_str = _dag_run_date(run)
            try:
                dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                st.caption(dt.strftime("%d/%m/%Y %H:%M"))
            except (ValueError, TypeError):
                st.caption(str(date_str) if date_str else "—")

        with col_type_col:
            run_type = run.get("run_type", "")
            conf = run.get("conf") or {}
            if run_type == "manual" or conf.get("triggered_from") == "kharon":
                st.caption("🔘 Manual")
            else:
                st.caption("⏰ Auto")


# ─── Page 5: Salud por Cliente ────────────────────────────────────────────────

def _page_health_by_client() -> None:
    st.title("❤️ Salud por Cliente")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Análisis de salud y rendimiento por cliente</p>", unsafe_allow_html=True)

    try:
        af = _get_airflow_client()
        dags = af.list_dags(limit=200)
    except AirflowClientError as e:
        st.error(f"Error al conectar con Airflow: {e}")
        return

    kharon_dags = [d for d in dags if _is_kharon_dag(d)]
    if not kharon_dags:
        st.info("No hay DAGs de Kharōn registrados.")
        return

    # ── Calcular salud por DAG desde los runs de Airflow ─────────────────────────
    dag_health: list = []
    progress = st.progress(0, text="Calculando estado de salud…")
    total_dags = len(kharon_dags)

    for idx, dag in enumerate(kharon_dags):
        dag_id = dag.get("dag_id", "")
        client_id = _dag_client_id(dag) or "sin_cliente"

        try:
            runs = af.list_dag_runs(dag_id, limit=20)
        except AirflowClientError:
            runs = []

        completed = [r for r in runs if r.get("state") in ("success", "failed")]
        total = len(completed)

        if total == 0:
            dag_health.append({
                "dag_id": dag_id, "client_id": client_id,
                "status": "unknown", "success_rate": None,
                "consecutive_failures": 0, "last_state": None,
                "last_date": None, "total_runs": 0,
            })
        else:
            success_count = sum(1 for r in completed if r.get("state") == "success")
            rate = success_count / total

            consecutive_failures = 0
            for r in runs:
                if r.get("state") == "failed":
                    consecutive_failures += 1
                elif r.get("state") == "success":
                    break

            last = runs[0]
            dag_health.append({
                "dag_id": dag_id, "client_id": client_id,
                "status": "healthy" if (rate >= 0.8 and consecutive_failures < 3) else "unhealthy",
                "success_rate": rate,
                "consecutive_failures": consecutive_failures,
                "last_state": last.get("state"),
                "last_date": _dag_run_date(last),
                "total_runs": total,
            })

        progress.progress((idx + 1) / total_dags)

    progress.empty()

    # ── Agrupar por cliente ────────────────────────────────────────────────────
    grouped: dict = {}
    for entry in dag_health:
        grouped.setdefault(entry["client_id"], []).append(entry)

    for client_id, scripts in sorted(grouped.items()):
        known = [s for s in scripts if s["status"] != "unknown"]
        healthy_count = sum(1 for s in known if s["status"] == "healthy")
        unhealthy_count = sum(1 for s in known if s["status"] == "unhealthy")
        unknown_count = len(scripts) - len(known)

        if known:
            health_pct = healthy_count / len(known) * 100
            bar_color = "#22c55e" if health_pct >= 80 else "#f59e0b" if health_pct >= 50 else "#ef4444"
            pct_label = f"{health_pct:.0f}% saludable"
            bar_w = f"{health_pct:.0f}%"
        else:
            bar_color, pct_label, bar_w = "#545B67", "Sin ejecuciones", "0%"

        with st.container():
            col_hdr, col_bar = st.columns([2, 3])
            with col_hdr:
                st.markdown(f"### 🏢 {client_id}")
                parts = []
                if healthy_count:
                    parts.append(f"{healthy_count} ✅")
                if unhealthy_count:
                    parts.append(f"{unhealthy_count} ❌")
                if unknown_count:
                    parts.append(f"{unknown_count} ❓ sin datos")
                st.caption(f"{len(scripts)} scripts — " + " · ".join(parts) if parts else f"{len(scripts)} scripts")

            with col_bar:
                st.markdown(
                    f'<div class="health-bar">'
                    f'<div class="health-bar-fill" style="width:{bar_w};background:{bar_color};"></div>'
                    f'</div>'
                    f'<span style="font-size:0.75em;color:{bar_color};">{pct_label}</span>',
                    unsafe_allow_html=True,
                )

            with st.expander(f"Ver detalle — {client_id}"):
                for s in scripts:
                    col_name, col_hlth, col_detail = st.columns([2, 1, 2])
                    with col_name:
                        st.markdown(f"**{s['dag_id']}**")
                    with col_hlth:
                        render_health_indicator({"status": s["status"], "detail": s["last_state"] or ""})
                    with col_detail:
                        if s["last_date"]:
                            try:
                                dt = datetime.fromisoformat(str(s["last_date"]).replace("Z", "+00:00"))
                                st.caption(f"Último: {dt.strftime('%d/%m %H:%M')} [{s['last_state']}]")
                            except (ValueError, TypeError):
                                st.caption(f"Último: {s['last_date']}")
                        else:
                            st.caption("Sin ejecuciones")
                        if s["success_rate"] is not None:
                            st.caption(f"Éxito: {s['success_rate']:.0%}  ({s['total_runs']} runs)")
                        if s["consecutive_failures"] > 0:
                            st.caption(f"⚠️ {s['consecutive_failures']} fallos consecutivos")
                    st.markdown("---")

        st.markdown("---")


# ─── Page 6: Nuevo Script ─────────────────────────────────────────────────────

def _page_new_script() -> None:
    st.title("➕ Nuevo Script")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Configurá un nuevo script en 5 pasos</p>", unsafe_allow_html=True)

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
                gen_result = generator.generate_dag(
                    script_id=result.get("name", "").replace(" ", "_").lower(),
                    script_name=result.get("name", ""),
                    script_path=result.get("script_path", ""),
                    client_id=result.get("client_id", result.get("client", "")),
                    timeout=result.get("timeout", 3600),
                    retries=result.get("retries", 2),
                    schedule=result.get("schedule"),
                    criticality=result.get("criticality", "media"),
                    tags=result.get("tags", []),
                    python="python3" if result.get("interpreter") == "python" else "bash",
                    execution_mode=result.get("execution_mode", "scheduled"),
                )
                if gen_result.success:
                    st.success(f"✅ Script **{result.get('name', '')}** creado exitosamente.")
                    st.toast("🎉 DAG generado — Airflow lo detectará en ~30s", icon="✅")
                    st.info("El DAG se generará en el próximo ciclo de parsing de Airflow (~30s).")
                else:
                    st.error(f"Error: {', '.join(gen_result.errors)}")
            except Exception as e:
                st.error(f"Error al generar el DAG: {e}")


# ─── Page 7: Configuración ────────────────────────────────────────────────────

def _page_configuration() -> None:
    st.title("⚙️ Configuración")
    st.markdown("<p style='color:#9ca3af;font-size:0.9em;margin-top:-8px;'>Administración de clientes y parámetros del sistema</p>", unsafe_allow_html=True)

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

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    st.subheader("Clientes Registrados")
    clients = _get_clients()
    if clients:
        tags_html = '<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:10px;padding:8px 0;">'
        for c in clients:
            name = c.get("name", "")
            color = c.get("color", "#374151")
            try:
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                bg = f"rgba({r},{g},{b},0.18)"
            except Exception:
                bg = "rgba(55,65,81,0.18)"

            icon_html = _client_icon_html(c)
            tags_html += (
                f'<span style="background-color:{bg};color:{color};'
                f'padding:5px 14px;border-radius:14px;font-size:0.85em;'
                f'font-weight:600;white-space:nowrap;display:inline-flex;'
                f'align-items:center;gap:6px;">'
                f'{icon_html} {name}</span>'
            )
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("---")
        options = [c.get("name", "") for c in clients]
        selected = st.selectbox("Seleccioná un cliente para eliminar", [""] + options, key="sel_del_client")

        if selected:
            cid = next((c.get("id", "") for c in clients if c.get("name") == selected), "")
            col_warn, col_cancel, col_del = st.columns([3, 1, 1])
            with col_warn:
                st.warning(f"⚠️ ¿Eliminar **{selected}**? Esta acción no se puede deshacer.")
            with col_cancel:
                if st.button("Cancelar", key="cancel_del"):
                    st.rerun()
            with col_del:
                if st.button("🗑 Eliminar", type="primary", key="confirm_del"):
                    try:
                        cm = _get_client_manager()
                        cm.delete_client(cid)
                        st.toast(f"🗑️ Cliente '{selected}' eliminado", icon="🗑️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {e}")
    else:
        st.info("No hay clientes registrados.")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    st.subheader("Agregar Cliente")

    if "add_client_color" not in st.session_state:
        st.session_state.add_client_color = f"#{random.randint(0x334, 0xBBBBBB):06x}"
    if "_color_picker_counter" not in st.session_state:
        st.session_state._color_picker_counter = 0

    new_name = st.text_input("Nombre del cliente *", placeholder="ej: ACME Corp", key="new_client_name")

    _logo_uploaded = st.file_uploader(
        "Logo (PNG, JPG, SVG, BMP) — opcional",
        type=["png", "jpg", "jpeg", "svg", "bmp"],
        key="new_client_logo_uploader",
    )

    if _logo_uploaded:
        logo_bytes = _logo_uploaded.getvalue()
        extracted = extract_primary_color(logo_bytes, _logo_uploaded.name)
        if extracted and st.session_state.get("_last_logo_name") != _logo_uploaded.name:
            st.session_state["_last_logo_name"] = _logo_uploaded.name
            st.session_state.add_client_color = extracted
            st.session_state._color_picker_counter += 1
            st.rerun()

    _cp_key = f"new_client_color_{st.session_state._color_picker_counter}"
    new_color = st.color_picker("Color del cliente", value=st.session_state.add_client_color, key=_cp_key)
    st.session_state.add_client_color = new_color

    new_description = st.text_area("Descripción (opcional)", placeholder="Descripción del cliente...", key="new_client_desc")

    if st.button("✅ Crear Cliente", type="primary", key="create_client_btn", use_container_width=True):
        if new_name:
            try:
                cm = _get_client_manager()
                clean_name = new_name.strip()
                client_id = clean_name.lower().replace(" ", "_").replace(".", "")

                logo_path = ""
                if _logo_uploaded:
                    logos_dir = config.CONFIG_DIR / "client_logos"
                    logos_dir.mkdir(exist_ok=True)
                    ext = Path(_logo_uploaded.name).suffix
                    logo_path = str(logos_dir / f"{client_id}{ext}")
                    with open(logo_path, "wb") as f:
                        f.write(_logo_uploaded.getbuffer())

                cm.create_client({
                    "id": client_id,
                    "name": clean_name,
                    "short_name": clean_name[:3].upper(),
                    "color": st.session_state.add_client_color,
                    "icon": "",
                    "logo_path": logo_path,
                    "description": new_description,
                    "contact_email": f"admin@{client_id}.com",
                    "contact_name": clean_name,
                })
                st.toast(f"✅ Cliente '{clean_name}' creado exitosamente", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear cliente: {e}")
        else:
            st.warning("El nombre es obligatorio.")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    st.subheader("Información del Registro")
    try:
        cm = _get_client_manager()
        registry_info = cm.get_cache_status()
        if isinstance(registry_info, dict):
            info_html = '<div style="background:#131923;border:1px solid #2d3748;border-radius:8px;padding:12px 16px;">'
            label_map = {
                "file_path": "Archivo",
                "clients_count": "Clientes registrados",
                "last_loaded": "Última carga",
                "format": "Formato",
            }
            for key, val in registry_info.items():
                label = label_map.get(key, key.replace("_", " ").title())
                info_html += (
                    f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                    f'border-bottom:1px solid #1E2632;">'
                    f'<span style="color:#9ca3af;font-size:0.85em;">{label}</span>'
                    f'<span style="color:#e5e7eb;font-size:0.85em;font-family:JetBrains Mono,monospace;">{val}</span>'
                    f'</div>'
                )
            info_html += '</div>'
            st.markdown(info_html, unsafe_allow_html=True)
        else:
            st.json(registry_info)
    except Exception as e:
        st.info(f"No se pudo obtener información del registro: {e}")


# ─── Page Router ───────────────────────────────────────────────────────────────

_PAGE_HANDLERS = {
    "📊 Tablero": _page_dashboard,
    "⚙️ Procesos": _page_processes,
    "📄 Logs": _page_view_logs,
    "📡 Monitoreo": _page_global_monitoring,
    "❤️ Salud": _page_health_by_client,
    "➕ Nuevo Script": _page_new_script,
    "🔧 Configuración": _page_configuration,
}


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Kharōn — Arkh-Ur",
        page_icon=_KHARON_ICON_URI,
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
