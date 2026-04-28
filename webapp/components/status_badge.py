import base64
import os
from pathlib import Path

import streamlit as st


_STATUS_CONFIG = {
    "success":      {"color": "#22c55e", "bg": "rgba(34,197,94,0.15)", "label": "Exitoso",   "icon": "✅"},
    "failed":       {"color": "#ef4444", "bg": "rgba(239,68,68,0.15)", "label": "Fallido",    "icon": "❌"},
    "running":      {"color": "#f59e0b", "bg": "rgba(245,158,11,0.15)", "label": "Ejecutando", "icon": "🔄"},
    "queued":       {"color": "#3b82f6", "bg": "rgba(59,130,246,0.15)", "label": "En cola",   "icon": "⏳"},
    "paused":       {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "label": "Pausado",    "icon": "⏸️"},
    "up_for_retry": {"color": "#f59e0b", "bg": "rgba(245,158,11,0.15)", "label": "Reintentando", "icon": "🔁"},
    "upstream_failed": {"color": "#ef4444", "bg": "rgba(239,68,68,0.15)", "label": "Padre fallido", "icon": "⚠️"},
    "skipped":      {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "label": "Omitido",   "icon": "⏭️"},
    "unknown":      {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "label": "Desconocido", "icon": "❓"},
}

_CRITICALITY_CONFIG = {
    "alta":    {"color": "#ef4444", "bg": "rgba(239,68,68,0.15)", "icon": "🔴"},
    "media":   {"color": "#f59e0b", "bg": "rgba(245,158,11,0.15)", "icon": "🟡"},
    "baja":    {"color": "#22c55e", "bg": "rgba(34,197,94,0.15)", "icon": "🟢"},
    "default": {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "icon": "⚪"},
}


def _badge_html(text: str, bg_color: str, text_color: str, icon: str = "") -> str:
    return (
        f'<span style="'
        f'background-color:{bg_color};'
        f'color:{text_color};'
        f'padding:2px 10px;'
        f'border-radius:12px;'
        f'font-size:0.78em;'
        f'font-weight:600;'
        f'white-space:nowrap;'
        f'display:inline-flex;'
        f'align-items:center;'
        f'gap:4px;'
        f'">'
        f'{icon} {text}'
        f'</span>'
    )


def render_status_badge(status: str) -> None:
    """Renderiza un badge de color segun el estado del DAG/Task.

    Args:
        status: Estado (success, failed, running, paused, queued, etc.)
    """
    cfg = _STATUS_CONFIG.get(status, _STATUS_CONFIG["unknown"])
    html = _badge_html(cfg["label"], cfg["bg"], cfg["color"], cfg["icon"])
    st.markdown(html, unsafe_allow_html=True)


def _client_icon_html(client: dict) -> str:
    """Logo image si existe, sino cuadrado de inicial con color del cliente."""
    logo_path = client.get("logo_path", "")
    color = client.get("color", "#374151")
    name = client.get("name", "?")
    initial = name[0].upper() if name else "?"

    if logo_path and os.path.isfile(logo_path):
        ext = Path(logo_path).suffix.lstrip(".").lower()
        mime = {"svg": "svg+xml", "png": "png", "jpg": "jpeg", "jpeg": "jpeg", "bmp": "bmp"}.get(ext, "png")
        try:
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return (
                f'<img src="data:image/{mime};base64,{b64}" '
                f'style="height:16px;width:16px;object-fit:contain;vertical-align:middle;">'
            )
        except OSError:
            pass

    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:16px;height:16px;min-width:16px;background:{color};color:#fff;'
        f'font-size:0.55em;font-weight:800;border-radius:3px;">{initial}</span>'
    )


def render_client_badge(client: dict) -> None:
    """Renderiza un badge con logo (o inicial) y nombre del cliente.

    Args:
        client: Dict con claves 'name', 'color' (hex), 'logo_path' (opcional).
    """
    name = client.get("name", "Desconocido")
    color = client.get("color", "#374151")
    bg = _lighten_color(color)
    icon_html = _client_icon_html(client)

    html = _badge_html(name, bg, color, icon_html)
    st.markdown(html, unsafe_allow_html=True)


def render_health_indicator(health: dict) -> None:
    """Renderiza un indicador de salud con icono y texto.

    Args:
        health: Dict con clave 'status' ('healthy', 'unhealthy', 'unknown')
                y opcionalmente 'detail' (str).
    """
    status = health.get("status", "unknown")
    detail = health.get("detail", "")

    cfg = {
        "healthy":   {"color": "#22c55e", "bg": "rgba(34,197,94,0.15)", "icon": "✅", "label": "Saludable"},
        "unhealthy": {"color": "#ef4444", "bg": "rgba(239,68,68,0.15)", "icon": "❌", "label": "No saludable"},
        "unknown":   {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "icon": "❓", "label": "Desconocido"},
    }.get(status, {"color": "#9ca3af", "bg": "rgba(156,163,175,0.15)", "icon": "❓", "label": "Desconocido"})

    label = f'{cfg["label"]}'
    if detail:
        label += f" — {detail}"

    html = _badge_html(label, cfg["bg"], cfg["color"], cfg["icon"])
    st.markdown(html, unsafe_allow_html=True)


def render_criticality_badge(criticality: str) -> None:
    """Renderiza un badge de nivel de criticalidad.

    Args:
        criticality: Nivel ('alta', 'media', 'baja').
    """
    key = criticality.lower() if criticality else "default"
    cfg = _CRITICALITY_CONFIG.get(key, _CRITICALITY_CONFIG["default"])
    label = criticality.title() if criticality else "Sin definir"
    html = _badge_html(label, cfg["bg"], cfg["color"], cfg["icon"])
    st.markdown(html, unsafe_allow_html=True)


def _lighten_color(hex_color: str, factor: float = 0.7) -> str:
    """Devuelve un rgba semitransparente del color para badges en tema dark."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "rgba(55,65,81,0.2)"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},0.2)"
