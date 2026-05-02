import time
import pytest
from playwright.sync_api import Page, expect


def _goto_config(page: Page, base_url: str):
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    time.sleep(8)
    nav = page.locator('button:has-text("Configuración")')
    nav.wait_for(state="visible", timeout=15000)
    nav.click()
    page.wait_for_load_state("networkidle")
    time.sleep(5)


def test_config_page_shows_client_tags(page: Page, webapp_base_url: str):
    _goto_config(page, webapp_base_url)

    heading = page.get_by_role("heading", level=1)
    expect(heading).to_contain_text("Configuración")

    expect(page.get_by_text("Clientes Registrados")).to_be_visible()

    pills = page.locator(".kharon-client-pill")
    count = pills.count()
    assert count > 0, f"Expected kharon-client-pill elements, found {count}"

    first_pill = pills.first
    expect(first_pill).to_be_visible()
