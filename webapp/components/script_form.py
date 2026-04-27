import os
from typing import Dict, List, Optional

import streamlit as st


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
    cols = st.columns(len(_STEPS))
    for i, col in enumerate(cols):
        with col:
            bg = "#374151" if i <= current else "#1E2632"
            text_c = "#e5e7eb" if i <= current else "#545B67"
            st.markdown(
                f'<div style="'
                f'background:{bg};color:{text_c};'
                f'padding:6px 0;border-radius:4px;text-align:center;'
                f'font-size:0.72em;font-weight:600;">'
                f'{i + 1}'
                f"</div>",
                unsafe_allow_html=True,
            )


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
                on_click=lambda: st.session_state.update(form_step=st.session_state.form_step + 1),
            )


def _step_basic_info(existing_scripts: List[dict]) -> Optional[Dict]:
    existing_names = {s.get("name", "") for s in existing_scripts}

    name = st.text_input(
        "Nombre del Script *",
        value=st.session_state.form_data.get("name", ""),
        key="sf_name",
        placeholder="ej: etl_clientes_diario",
    )
    description = st.text_area(
        "Descripción *",
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

    can_continue = bool(name and description)

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
    )
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

    can_continue = bool(script_path)

    if script_path and not os.path.isabs(script_path):
        st.info("Usá una ruta absoluta para el script.")
    elif script_path and os.path.isfile(script_path):
        st.success(f"✅ Script encontrado: {script_path}")
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

    client_names = [c.get("name", "") for c in clients]
    default_idx = 0
    saved = st.session_state.form_data.get("client")
    if saved:
        for i, n in enumerate(client_names):
            if n == saved:
                default_idx = i
                break

    selected = st.selectbox(
        "Cliente *",
        options=client_names,
        index=default_idx,
        key="sf_client",
    )
    env_vars = st.text_area(
        "Variables de entorno (una por línea, FORMATO=VALOR)",
        value=st.session_state.form_data.get("env_vars", ""),
        key="sf_env_vars",
        placeholder="DB_HOST=localhost\nDB_PORT=5432",
    )

    st.session_state.form_data.update({
        "client": selected,
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
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Nombre:** {fd.get('name', '—')}")
        st.markdown(f"**Descripción:** {fd.get('description', '—')}")
        st.markdown(f"**Criticalidad:** {fd.get('criticality', '—')}")
        st.markdown(f"**Intérprete:** {fd.get('interpreter', '—')}")

    with col2:
        st.markdown(f"**Ruta:** {fd.get('script_path', '—')}")
        st.markdown(f"**Cliente:** {fd.get('client', '—')}")
        mode_display = {
            "on_demand": "🎯 Bajo Demanda",
            "continuous": "🔄 Continuo",
            "scheduled": f"📅 Agendado (`{fd.get('schedule', '—')}`)",
        }
        st.markdown(f"**Modo:** {mode_display.get(fd.get('execution_mode', ''), '—')}")
        st.markdown(f"**Tags:** {', '.join(fd.get('tags', [])) or '—'}")
        st.markdown(f"**Timeout:** {fd.get('timeout', 3600)}s | **Reintentos:** {fd.get('retries', 2)}")

    if fd.get("env_vars"):
        with st.expander("Variables de entorno"):
            st.code(fd["env_vars"])

    submitted = st.button("✅ Crear Script", type="primary", key="sf_submit")

    if submitted:
        data = dict(fd)
        st.session_state.form_step = 0
        st.session_state.form_data = {}
        return data

    return None
