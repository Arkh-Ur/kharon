import time

import pytest
from playwright.sync_api import Page, expect


def test_dashboard_page_loads_and_shows_metrics(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("📊 Tablero").first.click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("📊 Tablero")

    expect(page.get_by_text("Total Scripts")).to_be_visible()
    expect(page.get_by_text("En Ejecución")).to_be_visible()
    expect(page.get_by_text("Tasa de Éxito")).to_be_visible()
    expect(page.get_by_text("Duración Prom.")).to_be_visible()

    metric_cards = page.locator(".metric-card")
    expect(metric_cards).to_have_count(4)


def test_execute_scripts_page_loads_and_shows_dags(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("⚙️ Procesos").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Procesos")

    expect(page.get_by_text("Filtrar por cliente").first).to_be_visible()


def test_view_logs_page_loads_and_shows_dag_selector(page: Page, webapp_base_url: str, airflow_base_url: str,
                      airflow_password: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("📄 Logs").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Ver Logs")

    expect(page.get_by_text("Seleccioná un DAG")).to_be_visible()


def test_monitoring_global_page_loads_correctly(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("📡 Monitoreo").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Monitoreo Global")


def test_health_by_client_page_loads_correctly(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("❤️ Salud").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Salud por Cliente")


def test_new_script_page_loads_correctly(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Nuevo Script")


def test_configuration_page_loads_and_shows_airflow_health(page: Page, webapp_base_url: str, airflow_base_url: str,
                          airflow_password: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("🔧 Configuración").click()
    time.sleep(page_wait_time)

    assert "Página no encontrada" not in page.content()

    h1 = page.get_by_role("heading", level=1)
    expect(h1).to_contain_text("Configuración")

    expect(page.get_by_text("Estado de Airflow")).to_be_visible()
    expect(page.get_by_text("Scheduler", exact=False)).to_be_visible()
