import streamlit as st


def render_log_viewer(log_content: str, auto_refresh: bool = False) -> None:
    """Visor de logs con busqueda, descarga y auto-refresh.

    Args:
        log_content: Contenido del log como string.
        auto_refresh: Mostrar toggle de auto-refresh.
    """
    if not log_content:
        st.info("No hay logs disponibles para esta ejecución.")
        return

    col_search, col_download, col_refresh = st.columns([3, 1, 1])

    with col_search:
        search_term = st.text_input(
            "🔍 Buscar en logs",
            key="log_search_term",
            placeholder="Filtrar líneas...",
        )

    with col_download:
        dag_id = st.session_state.get("selected_dag_id", "log")
        run_id = st.session_state.get("selected_run_id", "run")
        task_id = st.session_state.get("selected_task_id", "task")
        filename = f"{dag_id}_{run_id}_{task_id}.log"
        st.download_button(
            "📥 Descargar",
            data=log_content,
            file_name=filename,
            mime="text/plain",
            key="log_download_btn",
        )

    if auto_refresh:
        with col_refresh:
            if st.button("🔄 Refrescar", key="log_refresh_btn", use_container_width=True):
                st.rerun()

    lines = log_content.split("\n")

    if search_term:
        lines = [
            line
            for line in lines
            if search_term.lower() in line.lower()
        ]
        if not lines:
            st.warning(f"No se encontraron líneas con '{search_term}'.")
            return

    max_lines = 2000
    if len(lines) > max_lines:
        st.warning(
            f"El log tiene {len(lines)} líneas. Mostrando las últimas {max_lines}."
        )
        lines = lines[-max_lines:]

    numbered = "".join(
        f"{i + 1:>5} | {line}\n" for i, line in enumerate(lines)
    )

    st.code(numbered, language="log")
