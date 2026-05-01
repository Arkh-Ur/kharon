import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

from utils import describe_cron, safe_html


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

    if st.button("🗑️ Limpiar formulario", key="clear_form"):
        for key in list(st.session_state.keys()):
            if key.startswith("form_"):
                del st.session_state[key]
        st.rerun()

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
    # Process pending selections from file browser BEFORE creating widgets
    _pending_nav = st.session_state.pop("_pending_browse_root", None)
    if _pending_nav:
        st.session_state.browse_root = _pending_nav
        st.session_state["browse_root_input"] = _pending_nav
    _pending_proj = st.session_state.pop("_pending_project_path", None)
    if _pending_proj is not None:
        st.session_state.form_data["project_path"] = _pending_proj
        st.session_state["sf_project_path"] = _pending_proj
    _pending_script = st.session_state.pop("_pending_script_path", None)
    if _pending_script is not None:
        st.session_state.form_data["script_path"] = _pending_script
        st.session_state["sf_script_path"] = _pending_script
    _pending_config = st.session_state.pop("_pending_config_path", None)
    if _pending_config is not None:
        st.session_state.form_data["config_file"] = _pending_config
        st.session_state["sf_config_file"] = _pending_config

    project_path = st.session_state.form_data.get("project_path", "")
    script_path = st.session_state.form_data.get("script_path", "")
    config_file = st.session_state.form_data.get("config_file", "")

    _browse_mode = st.session_state.get("_browse_mode", "")

    col_proj, col_browse = st.columns([3, 1])
    with col_proj:
        project_path = st.text_input(
            "Ruta del Proyecto *",
            value=project_path,
            key="sf_project_path",
            placeholder="/ruta/al/proyecto",
        ).strip()
    with col_browse:
        if st.button("📂 Explorar", key="sf_browse_project"):
            st.session_state.browse_root = project_path if project_path and os.path.isdir(project_path) else os.path.expanduser("~")
            st.session_state.browse_root_input = project_path if project_path and os.path.isdir(project_path) else os.path.expanduser("~")
            st.session_state._browse_mode = "project"
            st.rerun()

    if _browse_mode == "project":
        _render_file_browser(mode="project")

    col_script, col_script_browse = st.columns([3, 1])
    with col_script:
        script_path = st.text_input(
            "Script Principal *",
            value=script_path,
            key="sf_script_path",
            placeholder="scripts/run_etl.sh (relativo al proyecto)",
        ).strip()
    with col_script_browse:
        if project_path and os.path.isdir(project_path) and st.button("📂 Explorar", key="sf_browse_script"):
            st.session_state.browse_root = project_path
            st.session_state.browse_root_input = project_path
            st.session_state._browse_mode = "script"
            st.rerun()

    if _browse_mode == "script":
        _render_file_browser(mode="script")

    if script_path:
        if os.path.isabs(script_path):
            if os.path.isfile(script_path):
                project_path = os.path.dirname(script_path)
                script_path = os.path.basename(script_path)
                st.info(f"📁 Ruta detectada: proyecto='{project_path}', script='{script_path}'")
            else:
                st.warning(f"⚠️ El archivo no existe: {script_path}")

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

    col_cfg, col_cfg_browse = st.columns([3, 1])
    with col_cfg:
        config_file = st.text_input(
            "Archivo de configuración (opcional)",
            value=config_file,
            key="sf_config_file",
            placeholder="config.yaml (relativo al proyecto)",
        ).strip()
    with col_cfg_browse:
        if project_path and os.path.isdir(project_path) and st.button("📂 Explorar", key="sf_browse_config"):
            st.session_state.browse_root = project_path
            st.session_state.browse_root_input = project_path
            st.session_state._browse_mode = "config"
            st.rerun()

    if _browse_mode == "config":
        _render_file_browser(mode="config")

    if config_file:
        full_cfg_path = config_file if os.path.isabs(config_file) else os.path.join(project_path, config_file)
        _allowed_root = Path(project_path).resolve() if project_path else None
        _safe_cfg = True
        if _allowed_root:
            try:
                _safe_cfg = Path(full_cfg_path).resolve().is_relative_to(_allowed_root)
            except Exception:
                _safe_cfg = False
        if not _safe_cfg:
            st.warning("⚠️ Config fuera del directorio del proyecto")
        elif os.path.isfile(full_cfg_path):
            st.success(f"✅ Config encontrado: {full_cfg_path}")
            with st.expander("📄 Vista previa del config"):
                try:
                    with open(full_cfg_path, "r", encoding="utf-8") as f:
                        preview = f.read(3000)
                    ext = os.path.splitext(full_cfg_path)[1]
                    lang = {'.py': 'python', '.sh': 'bash', '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json', '.toml': 'toml', '.env': 'bash'}.get(ext, '')
                    st.code(preview, language=lang)
                except Exception:
                    st.warning("No se pudo leer el archivo")
        else:
            st.warning(f"⚠️ El config no existe en el proyecto: {config_file}")

    can_continue = False
    if project_path and script_path:
        full_script_path = os.path.join(project_path, script_path)
        _allowed_root = Path(project_path).resolve()
        _safe_script = Path(full_script_path).resolve().is_relative_to(_allowed_root)
        if not _safe_script:
            st.warning("⚠️ Ruta fuera del directorio del proyecto")
        elif os.path.isfile(full_script_path):
            st.success(f"✅ Script encontrado: {full_script_path}")
            can_continue = True
            with st.expander("Vista previa del script"):
                try:
                    with open(full_script_path, "r", encoding="utf-8") as f:
                        preview = f.read(5000)
                    st.code(preview, language=interpreter)
                except Exception:
                    st.warning("No se pudo leer el archivo")
        elif not os.path.isdir(project_path):
            st.warning(f"⚠️ El directorio del proyecto no existe: {project_path}")
        else:
            st.warning(f"⚠️ El script no existe en el proyecto: {script_path}")

    if can_continue:
        st.session_state.form_data.update({
            "project_path": project_path,
            "script_path": script_path,
            "interpreter": interpreter,
            "timeout": timeout,
            "retries": retries,
            "config_file": config_file,
        })

    _nav_buttons(can_continue, "config")
    return None


def _render_file_browser(mode="project") -> None:
    browse_root = st.session_state.get("browse_root", os.path.expanduser("~"))

    with st.expander("📂 Explorar archivos", expanded=True):
        st.text_input("Ruta actual", value=browse_root, key="browse_root_input")

        current_root = st.session_state.browse_root_input
        if current_root != browse_root:
            browse_root = current_root
            st.session_state.browse_root = current_root

        if not os.path.isdir(browse_root):
            st.warning("⚠️ La ruta no existe o no es un directorio")
            if st.button("✕ Cerrar explorador", key="close_browser"):
                st.session_state.pop("browse_root", None)
                st.session_state.pop("_browse_mode", None)
                st.rerun()
            return

        st.caption(f"📍 {browse_root}")

        parent = os.path.dirname(browse_root)
        col_up, col_select = st.columns(2)
        with col_up:
            if st.button("⬆ Subir", key="browse_up", use_container_width=True):
                st.session_state._pending_browse_root = parent
                st.rerun()
        with col_select:
            if mode == "project" and st.button("✅ Usar esta carpeta", key="browse_select_dir", use_container_width=True, type="primary"):
                st.session_state._pending_project_path = browse_root
                st.session_state.pop("browse_root", None)
                st.session_state.pop("_browse_mode", None)
                st.rerun()

        try:
            entries = sorted(os.listdir(browse_root))
        except PermissionError:
            st.error("Sin permisos para leer este directorio")
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(browse_root, e)) and not e.startswith('.')]

        files = []
        if mode in ("script", "config"):
            if mode == "config":
                file_exts = ('.yaml', '.yml', '.json', '.toml', '.env', '.cfg', '.ini', '.conf')
            else:
                file_exts = ('.py', '.sh', '.bash')
            files = [e for e in entries if os.path.isfile(os.path.join(browse_root, e)) and not e.startswith('.') and e.endswith(file_exts)]

        if dirs:
            st.markdown("**📁 Directorios**")
            cols_per_row = 3
            for i in range(0, len(dirs), cols_per_row):
                row_dirs = dirs[i:i + cols_per_row]
                cols = st.columns(len(row_dirs))
                for j, d in enumerate(row_dirs):
                    with cols[j]:
                        if st.button(f"📁 {d}", key=f"dir_{i}_{j}_{d[:20]}", use_container_width=True):
                            st.session_state._pending_browse_root = os.path.join(browse_root, d)
                            st.rerun()

        if files and mode in ("script", "config"):
            st.markdown("**📄 Archivos**")
            for f in files:
                col_file, col_btn = st.columns([3, 1])
                with col_file:
                    st.text(f"  {f}")
                with col_btn:
                    _btn_key = f"pick_{mode}_{f[:20]}"
                    if st.button("📄", key=_btn_key, help=f"Seleccionar {f}"):
                        full_path = os.path.join(browse_root, f)
                        project_path = st.session_state.get("sf_project_path", "")
                        if project_path and os.path.isdir(project_path):
                            try:
                                if not Path(full_path).resolve().is_relative_to(Path(project_path).resolve()):
                                    st.warning("⚠️ El archivo está fuera del directorio del proyecto")
                                    st.rerun()
                            except Exception:
                                st.warning("⚠️ No se pudo verificar la ruta del archivo.")
                                st.stop()
                            rel = os.path.relpath(full_path, project_path)
                        else:
                            rel = full_path
                        if mode == "script":
                            st.session_state._pending_script_path = rel
                        else:
                            st.session_state._pending_config_path = rel
                        st.session_state.pop("browse_root", None)
                        st.session_state.pop("_browse_mode", None)
                        st.rerun()

        if st.button("✕ Cerrar explorador", key="close_browser"):
            st.session_state.pop("browse_root", None)
            st.session_state.pop("_browse_mode", None)
            st.rerun()


def _step_client_assignment(clients: List[dict]) -> Optional[Dict]:
    if not clients:
        st.error("No hay clientes registrados. Creá uno primero en Configuración.")
        _nav_buttons(False, "client")
        return None

    client_options = {c.get("name", ""): c.get("id", re.sub(r'_+', '_', re.sub(r'[^a-z0-9_]', '_', c.get("name", "").lower())).strip('_')) for c in clients if re.sub(r'_+', '_', re.sub(r'[^a-z0-9_]', '_', c.get("name", "").lower())).strip('_')}
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
            st.session_state.form_data.get("execution_mode", "on_demand")
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
        ("📋 Nombre", safe_html(fd.get('name', '—'))),
        ("📝 Descripción", safe_html(fd.get('description') or '—')),
        ("🔴 Criticalidad", safe_html(fd.get('criticality', '—'))),
        ("🔧 Intérprete", safe_html(fd.get('interpreter', '—'))),
        ("📂 Ruta", safe_html(fd.get('script_path', '—'))),
        ("📄 Config", safe_html(fd.get('config_file') or '—')),
        ("🏢 Cliente", safe_html(fd.get('client', '—'))),
        ("⏱ Modo", safe_html(mode_display.get(fd.get('execution_mode', ''), '—'))),
        ("🏷 Tags", safe_html(', '.join(fd.get('tags', [])) or '—')),
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
