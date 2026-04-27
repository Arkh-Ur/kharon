import streamlit as st


_STATUS_CONFIG = {
    "success":      {"color": "#198754", "bg": "#d1e7dd", "label": "Exitoso",   "icon": "✅"},
    "failed":       {"color": "#dc3545", "bg": "#f8d7da", "label": "Fallido",    "icon": "❌"},
    "running":      {"color": "#fd7e14", "bg": "#fff3cd", "label": "Ejecutando", "icon": "🔄"},
    "queued":       {"color": "#0d6efd", "bg": "#cfe2ff", "label": "En cola",   "icon": "⏳"},
    "paused":       {"color": "#6c757d", "bg": "#e2e3e5", "label": "Pausado",    "icon": "⏸️"},
    "up_for_retry": {"color": "#fd7e14", "bg": "#fff3cd", "label": "Reintentando", "icon": "🔁"},
    "upstream_failed": {"color": "#dc3545", "bg": "#f8d7da", "label": "Padre fallido", "icon": "⚠️"},
    "skipped":      {"color": "#6c757d", "bg": "#e2e3e5", "label": "Omitido",   "icon": "⏭️"},
    "unknown":      {"color": "#6c757d", "bg": "#e2e3e5", "label": "Desconocido", "icon": "❓"},
}

_CRITICALITY_CONFIG = {
    "alta":    {"color": "#dc3545", "bg": "#f8d7da", "icon": "🔴"},
    "media":   {"color": "#fd7e14", "bg": "#fff3cd", "icon": "🟡"},
    "baja":    {"color": "#198754", "bg": "#d1e7dd", "icon": "🟢"},
    "default": {"color": "#6c757d", "bg": "#e2e3e5", "icon": "⚪"},
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


def render_client_badge(client: dict) -> None:
    """Renderiza un badge con el color e icono del cliente.

    Args:
        client: Dict con claves 'name', 'color' (hex), 'icon' (emoji opcional).
    """
    name = client.get("name", "Desconocido")
    color = client.get("color", "#4a1a8a")
    icon = client.get("icon", "🏢")
    bg = _lighten_color(color, 0.75)

    html = _badge_html(name, bg, color, icon)
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
        "healthy":   {"color": "#198754", "bg": "#d1e7dd", "icon": "✅", "label": "Saludable"},
        "unhealthy": {"color": "#dc3545", "bg": "#f8d7da", "icon": "❌", "label": "No saludable"},
        "unknown":   {"color": "#6c757d", "bg": "#e2e3e5", "icon": "❓", "label": "Desconocido"},
    }.get(status, {"color": "#6c757d", "bg": "#e2e3e5", "icon": "❓", "label": "Desconocido"})

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
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#e2e3e5"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"
