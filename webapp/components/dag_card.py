from datetime import datetime

import streamlit as st

from .status_badge import render_status_badge, render_client_badge


_STATUS_BORDER_COLORS = {
    "success": "#198754",
    "failed": "#dc3545",
    "running": "#fd7e14",
    "queued": "#0d6efd",
    "paused": "#6c757d",
    "unknown": "#6c757d",
}


def render_dag_card(dag_info: dict, client_badge: str = None) -> None:
    """Renderiza una tarjeta estilizada para un DAG.

    Args:
        dag_info: Dict con 'dag_id', 'description', 'status'/'state',
                  'last_run' (ISO str), 'schedule' (opcional), 'owners'.
        client_badge: Nombre del cliente para mostrar como badge opcional.
    """
    dag_id = dag_info.get("dag_id", "sin-id")
    description = dag_info.get("description") or dag_info.get("tags", [])
    if isinstance(description, list):
        description = ", ".join(description) if description else "Sin descripción"

    status = dag_info.get("status") or dag_info.get("state", "unknown")
    last_run = dag_info.get("last_run") or dag_info.get("last_execution")
    schedule = dag_info.get("schedule_interval") or dag_info.get("schedule", "—")
    owners = dag_info.get("owners", [])

    border_color = _STATUS_BORDER_COLORS.get(status, "#6c757d")

    if last_run:
        try:
            dt = datetime.fromisoformat(str(last_run).replace("Z", "+00:00"))
            last_run_display = dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            last_run_display = str(last_run)
    else:
        last_run_display = "Nunca"

    card_html = f"""
    <div style="
        border-left: 4px solid {border_color};
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:1.05em; font-weight:700; color:#1a1a2e;">{dag_id}</span>
        </div>
        <div style="font-size:0.85em; color:#495057; margin-bottom:10px;">{description}</div>
        <div style="display:flex; gap:16px; font-size:0.78em; color:#6c757d;">
            <span>📅 {last_run_display}</span>
            <span>🕐 {schedule}</span>
            {f'<span>👤 {", ".join(owners)}</span>' if owners else ''}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    col_status, col_client, col_spacer = st.columns([1, 1, 3])
    with col_status:
        render_status_badge(status)
    if client_badge:
        with col_client:
            render_client_badge({"name": client_badge, "color": "#4a1a8a", "icon": "🏢"})
