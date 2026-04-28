import os
from typing import Dict, List, Optional

import streamlit as st

from utils import describe_cron


_STEPS = [
    "📋 Información Básica",
    "⚙️ Configuración del Script",
    "🏢 Asignación de Cliente",
    "🕐 Modo de Ejecución",
    "✔️ Revisión",
]


def render_script_form(
    clients: List[dict],
    existing_scripts: List[dict] = None,
) -> Optional[Dict]:
    """Formulario multi-paso (5 pasos) para crear un nuevo script.

    Args:
        clients: Lista de dicts de clientes con 'name' y 'id'.
        existing_scripts: Lista de scripts existentes para evitar duplicados.

    Returns:
        Dict con datos del formulario si se envió, None si no.
    """
    existing_scripts = existing_scripts or []

    if "form_step" not in st.session_state:
        st.session_state.form_step = 0
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    step = st.session_state.form_step
    st.markdown(f"### {_STEPS[step]}")
    _render_step_progress(step)

    result = None

    if step == 0:
        result = _step_basic_info(existing_scripts)
    elif step == 1:
        result = _step_script_config()
    elif step == 2:
        result = _step_client_assignment(clients)
    elif step == 3:
        result = _step_schedule_tags()
    elif step == 4:
        result = _step_review(clients)

    return result


def _render_step_progress(current: int) -> None:
    steps_html = '<div style="display:flex;align-items:center;justify-content:center;gap:4px;padding:16px 8px;flex-wrap:nowrap;overflow-x:auto;">'
    for i in range(len(_STEPS)):
        if i < current:
            bg = "#22c55e"
            content = "✓"
            text_c = "#ffffff"
            border = "2px solid #22c55e"
        elif i == current:
            bg = "transparent"
            content = str(i + 1)
            text_c = "#3b82f6"
            border = "2px solid #3b82f6"
        else:
            bg = "transparent"
            content = str(i + 1)
            text_c = "#545B67"
            border = "2px solid #545B67"

        steps_html += (
            f'<div style="'
            f'width:34px;height:34px;min-width:34px;'
            f'border-radius:50%;'
            f'background:{bg};'
            f'color:{text_c};'
            f'border:{border};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.85em;font-weight:700;'
            f'touch-action:manipulation;'
            f'">{"✓" if i < current else str(i + 1)}</div>'
        )

        if i < len(_STEPS) - 1:
            line_color = "#22c55e" if i < current else "#2d3748"
            steps_html += (
                f'<div style="'
                f'flex:1;height:2px;'
                f'background:{line_color};'
                f'min-width:20px;max-width:60px;'
                f'"></div>'
            )

    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)


def _nav_buttons(can_continue: bool, step_key: str = "") -> None:
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.session_state.form_step > 0:
            if st.button("⬅ Anterior", key=f"back_{step_key}"):
                st.session_state.form_step -= 1
                st.rerun()

    with col_next:
        if st.session_state.form_step < len(_STEPS) - 1:
            st.button(
                "Siguiente ➡",
                disabled=not can_continue,
                key=f"next_{step_key}",
                type="primary",
                on_click=lambda: st.session_state.update(form_step=st.session_state.form_step + 1),
            )


def _step_basic_info(existing_scripts: List[dict]) -> Optional[Dict]:
    existing_names = {s.get("name", "") for s in existing_scripts}

    name = st.text_input(
        "Nombre del Script *",
        value=st.session_state.form_data.get("name", ""),
        key="sf_name",
        placeholder="ej: etl_clientes_diario",
    ).strip()
    description = st.text_area(
        "Descripción (opcional)",
        value=st.session_state.form_data.get("description", ""),
        key="sf_description",
        placeholder="Descripción clara del propósito del script...",
        max_chars=300,
    )
    criticality = st.selectbox(
        "Criticalidad",
        options=["baja", "media", "alta"],
        index=["baja", "media", "alta"].index(st.session_state.form_data.get("criticality", "media")),
        key="sf_criticality",
    )

    can_continue = bool(name)

    if name and name in existing_names:
        st.warning(f"Ya existe un script llamado '{name}'. Usá otro nombre.")
        can_continue = False

    if can_continue:
        st.session_state.form_data.update({
            "name": name,
            "description": description,
            "criticality": criticality,
        })

    _nav_buttons(can_continue, "basic")
    return None


def _step_script_config() -> Optional[Dict]:
    script_path = st.text_input(
        "Ruta del Script *",
        value=st.session_state.form_data.get("script_path", ""),
        key="sf_script_path",
        placeholder="/ruta/al/script.sh",
    ).strip()
    interpreter = st.selectbox(
        "Intérprete",
        options=["bash", "python", "sh"],
        index=["bash", "python", "sh"].index(st.session_state.form_data.get("interpreter", "bash")),
        key="sf_interpreter",
    )
    timeout = st.number_input(
        "Timeout (segundos)",
        min_value=60,
        max_value=86400,
        value=st.session_state.form_data.get("timeout", 3600),
        step=60,
        key="sf_timeout",
    )
    retries = st.number_input(
        "Reintentos",
        min_value=0,
        max_value=5,
        value=st.session_state.form_data.get("retries", 2),
        key="sf_retries",
    )

    if script_path and script_path.startswith("~"):
        script_path = os.path.expanduser(script_path)

    can_continue = False
    if script_path and not os.path.isabs(script_path):
        st.info("Usá una ruta absoluta para el script.")
    elif script_path and os.path.isfile(script_path):
        st.success(f"✅ Script encontrado: {script_path}")
        can_continue = True
        with st.expander("Vista previa del script"):
            try:
                with open(script_path, "r") as f:
                    preview = f.read(5000)
                st.code(preview, language=interpreter)
            except Exception:
                st.warning("No se pudo leer el archivo.")
    elif script_path:
        st.warning(f"⚠️ El archivo no existe: {script_path}")

    if can_continue:
        st.session_state.form_data.update({
            "script_path": script_path,
            "interpreter": interpreter,
            "timeout": timeout,
            "retries": retries,
        })

    _nav_buttons(can_continue, "config")
    return None


def _step_client_assignment(clients: List[dict]) -> Optional[Dict]:
    if not clients:
        st.error("No hay clientes registrados. Creá uno primero en Configuración.")
        _nav_buttons(False, "client")
        return None

    client_options = {c.get("name", ""): c.get("id", c.get("name", "").lower().replace(" ", "_")) for c in clients}
    client_names = list(client_options.keys())
    default_idx = 0
    saved = st.session_state.form_data.get("client")
    if saved:
        for i, n in enumerate(client_names):
            if n == saved or client_options[n] == saved:
                default_idx = i
                break

    selected = st.selectbox(
        "Cliente *",
        options=client_names,
        index=default_idx,
        key="sf_client",
    )
    selected_id = client_options.get(selected, selected)
    env_vars = st.text_area(
        "Variables de entorno (una por línea, FORMATO=VALOR)",
        value=st.session_state.form_data.get("env_vars", ""),
        key="sf_env_vars",
        placeholder="DB_HOST=localhost\nDB_PORT=5432",
    )

    st.session_state.form_data.update({
        "client": selected,
        "client_id": selected_id,
        "env_vars": env_vars,
    })

    _nav_buttons(bool(selected), "client")
    return None


def _step_schedule_tags() -> Optional[Dict]:
    execution_mode = st.selectbox(
        "Modo de ejecución *",
        options=["on_demand", "continuous", "scheduled"],
        format_func=lambda x: {
            "on_demand": "🎯 Bajo Demanda — ejecución manual",
            "continuous": "🔄 Continuo — se re-ejecuta al terminar",
            "scheduled": "📅 Agendado — según horario cron",
        }[x],
        index=["on_demand", "continuous", "scheduled"].index(
            st.session_state.form_data.get("execution_mode", "scheduled")
        ),
        key="sf_execution_mode",
    )

    schedule = None
    if execution_mode == "scheduled":
        schedule = st.text_input(
            "Expresión Cron",
            value=st.session_state.form_data.get("schedule", "0 6 * * *"),
            key="sf_schedule",
            placeholder="0 6 * * * (todos los días a las 6:00)",
        )

        desc = describe_cron(schedule) if schedule else ""
        if desc:
            st.success(f"📅 Se ejecutará: **{desc}**")

        with st.expander("📖 Guía rápida de Cron"):
            st.markdown("""
**Formato:** `minuto hora día-mes mes día-semana`

| Campo | Valores | Ejemplo |
|---|---|---|
| Minuto | 0–59 | `0`, `30`, `*/15` |
| Hora | 0–23 | `6`, `9`, `*/2` |
| Día del mes | 1–31 | `*`, `1`, `15` |
| Mes | 1–12 | `*`, `1` (Ene) |
| Día de semana | 0–6 (dom–sáb) | `*`, `0` (dom), `1-5` (lun–vie) |

**Operadores:**

| Símbolo | Significado | Ejemplo |
|---|---|---|
| `*` | Cualquier valor | `* * * * *` = cada minuto |
| `,` | Lista de valores | `0 6,18 * * *` = 6:00 y 18:00 |
| `-` | Rango | `0 9-17 * * 1-5` = cada hora laburables |
| `/` | Cada N | `*/30 * * * *` = cada 30 min |

**Ejemplos comunes:**

| Expresión | Significado |
|---|---|
| `0 6 * * *` | Todos los días a las 06:00 |
| `0 */4 * * *` | Cada 4 horas |
| `*/30 * * * *` | Cada 30 minutos |
| `0 9 * * 1-5` | Lunes a viernes a las 09:00 |
| `0 2 * * 0` | Cada domingo a las 02:00 |
| `0 0 1 * *` | El día 1 de cada mes |
| `0 6,18 * * *` | Dos veces al día: 06:00 y 18:00 |
""")

    elif execution_mode == "continuous":
        st.info("🔄 El script se re-ejecutará automáticamente al finalizar cada ejecución.")
    else:
        st.info("🎯 El script solo se ejecutará cuando lo actives manualmente desde el tablero.")

    tags_str = st.text_input(
        "Tags (separados por coma)",
        value=st.session_state.form_data.get("tags_str", ""),
        key="sf_tags",
        placeholder="etl, diarios, producción",
    )

    st.session_state.form_data.update({
        "execution_mode": execution_mode,
        "schedule": schedule if execution_mode == "scheduled" else None,
        "tags_str": tags_str,
        "tags": [t.strip() for t in tags_str.split(",") if t.strip()],
    })

    _nav_buttons(True, "schedule")
    return None


def _step_review(clients: List[dict]) -> Optional[Dict]:
    fd = st.session_state.form_data

    st.markdown("#### Resumen del Script")
    st.markdown(
        '<div style="background:#111827;border:1px solid rgba(59,130,246,0.1);border-radius:12px;padding:16px 20px;">',
        unsafe_allow_html=True,
    )

    _cron = fd.get('schedule', '')
    _cron_desc = describe_cron(_cron) if _cron else "—"
    mode_display = {
        "on_demand": "🎯 Bajo Demanda — ejecución manual",
        "continuous": "🔄 Continuo — se re-ejecuta al terminar",
        "scheduled": f"📅 {_cron_desc}",
    }

    review_rows = [
        ("📋 Nombre", fd.get('name', '—')),
        ("📝 Descripción", fd.get('description') or '—'),
        ("🔴 Criticalidad", fd.get('criticality', '—')),
        ("🔧 Intérprete", fd.get('interpreter', '—')),
        ("📂 Ruta", fd.get('script_path', '—')),
        ("🏢 Cliente", fd.get('client', '—')),
        ("⏱ Modo", mode_display.get(fd.get('execution_mode', ''), '—')),
        ("🏷 Tags", ', '.join(fd.get('tags', [])) or '—'),
        ("⏰ Timeout", f"{fd.get('timeout', 3600)}s"),
        ("🔁 Reintentos", str(fd.get('retries', 2))),
    ]

    for label, value in review_rows:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:8px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="color:#6b7280;font-size:10px;letter-spacing:1px;text-transform:uppercase;">{label}</span>'
            f'<span style="font-size:0.9em;font-weight:500;color:#e5e7eb;font-family:monospace;">{value}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if fd.get("env_vars"):
        with st.expander("Variables de entorno"):
            st.code(fd["env_vars"])

    col_back, col_spacer, col_submit = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅ Anterior", key="back_review"):
            st.session_state.form_step -= 1
            st.rerun()
    with col_submit:
        submitted = st.button("✅ Crear Script", type="primary", key="sf_submit", use_container_width=True)

    if submitted:
        data = dict(fd)
        st.session_state.form_step = 0
        st.session_state.form_data = {}
        return data

    return None
