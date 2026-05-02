"""E2E test for the full new-script deploy flow.

Uses the real test.sh script at airflow_home/scripts_externos/test/test.sh.
Verifies that creating a script generates a DAG file and redirects to Procesos.
"""

import os
import time
from pathlib import Path

import pytest
import yaml
from playwright.sync_api import Page, expect

# Paths relativas al repo
_REPO_ROOT = Path(__file__).parent.parent.parent
_TEST_SCRIPT = _REPO_ROOT / "airflow_home" / "scripts_externos" / "test" / "test.sh"
_PROJECT_DIR = str(_REPO_ROOT / "airflow_home" / "scripts_externos" / "test")
_REGISTRY = _REPO_ROOT / "airflow_home" / "dags" / "config" / "generated_scripts.yaml"


def _get_dags_dir() -> Path:
    """Lee la ruta de DAGs desde kharon_config.yaml (igual que config.get_dags_dir())."""
    cfg_path = _REPO_ROOT / "airflow_home" / "config" / "kharon_config.yaml"
    if cfg_path.exists():
        try:
            with open(cfg_path) as f:
                cfg = yaml.safe_load(f) or {}
            dags_dir = cfg.get("airflow_dags_dir")
            if dags_dir:
                return Path(dags_dir)
        except Exception:
            pass
    return _REPO_ROOT / "airflow_home" / "dags"

_SCRIPT_NAME = "e2e_deploy_test"


def _cleanup_dag(dag_id: str) -> None:
    """Eliminar DAG generado y su entrada en el registry."""
    dag_file = _get_dags_dir() / f"{dag_id}.py"
    if dag_file.exists():
        dag_file.unlink()

    if _REGISTRY.exists():
        with open(_REGISTRY, "r") as f:
            registry = yaml.safe_load(f) or {}
        if dag_id in registry:
            del registry[dag_id]
        with open(_REGISTRY, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, allow_unicode=True)


def _find_generated_dag_id() -> str | None:
    """Buscar el DAG ID generado para el script de test."""
    if not _REGISTRY.exists():
        return None
    with open(_REGISTRY, "r") as f:
        registry = yaml.safe_load(f) or {}
    for dag_id, entry in registry.items():
        if entry.get("script_name") == _SCRIPT_NAME:
            return dag_id
    return None


def test_create_new_script_deploys_dag(page: Page, webapp_base_url: str, page_wait_time: int):
    """Verifica el flujo completo: crear script → DAG generado → redirige a Procesos."""
    assert _TEST_SCRIPT.exists(), f"Script de test no encontrado: {_TEST_SCRIPT}"

    # Cleanup previo por si quedó un run anterior
    prev = _find_generated_dag_id()
    if prev:
        _cleanup_dag(prev)

    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    # Navegar a Nuevo Script
    page.get_by_text("➕ Nuevo Script").click()
    time.sleep(page_wait_time)

    # ── Paso 1: Información Básica ───────────────────────────────────────────
    expect(page.get_by_text("Información Básica")).to_be_visible()

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill(_SCRIPT_NAME)
    name_input.press("Tab")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    # ── Paso 2: Configuración del Script ────────────────────────────────────
    expect(page.get_by_text("Configuración del Script")).to_be_visible()

    # Ruta del Proyecto
    proj_input = page.get_by_label("Ruta del Proyecto *")
    proj_input.fill(_PROJECT_DIR)
    proj_input.press("Tab")
    time.sleep(3)

    # Script principal (relativo al proyecto)
    script_input = page.get_by_label("Script Principal *")
    script_input.fill("test.sh")
    script_input.press("Tab")
    time.sleep(page_wait_time)

    # Esperar confirmación "✅ Script encontrado"
    expect(page.get_by_text("Script encontrado", exact=False)).to_be_visible(timeout=15000)

    # "Siguiente" debe estar habilitado ahora
    next_btn = page.locator('button:has-text("Siguiente")').first
    expect(next_btn).to_be_enabled()
    next_btn.click()
    time.sleep(page_wait_time)

    # ── Paso 3: Asignación de Cliente ────────────────────────────────────────
    expect(page.get_by_text("Asignación de Cliente")).to_be_visible()
    # Dejar el cliente default — el selectbox ya tiene uno preseleccionado
    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    # ── Paso 4: Modo de Ejecución ─────────────────────────────────────────────
    expect(page.get_by_text("🕐 Modo de Ejecución")).to_be_visible()
    # Dejar "Bajo Demanda" por defecto
    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    # ── Paso 5: Revisión ──────────────────────────────────────────────────────
    expect(page.get_by_text("Revisión")).to_be_visible()
    expect(page.get_by_text(_SCRIPT_NAME)).to_be_visible()

    submit_btn = page.locator('button:has-text("Crear Script")').first
    expect(submit_btn).to_be_enabled()
    submit_btn.click()
    time.sleep(page_wait_time)

    # ── Verificar redirección a Procesos ─────────────────────────────────────
    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Procesos", timeout=20000)

    # ── Verificar DAG generado en disco ───────────────────────────────────────
    dag_id = _find_generated_dag_id()
    assert dag_id is not None, f"No se encontró el DAG para '{_SCRIPT_NAME}' en el registry"

    dag_file = _get_dags_dir() / f"{dag_id}.py"
    assert dag_file.exists(), f"DAG file no generado: {dag_file}"

    print(f"✅ DAG generado correctamente: {dag_id} → {dag_file}")

    # ── Limpieza ──────────────────────────────────────────────────────────────
    _cleanup_dag(dag_id)
