import time
import pytest
from playwright.sync_api import Page, expect


def _goto_config(page: Page, base_url: str):
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    time.sleep(8)
    nav = page.locator("text=Configuración")
    nav.wait_for(state="visible", timeout=15000)
    nav.click()
    page.wait_for_load_state("networkidle")
    time.sleep(5)


def test_config_page_shows_client_tags(page: Page, webapp_base_url: str):
    _goto_config(page, webapp_base_url)

    heading = page.get_by_role("heading", level=1)
    expect(heading).to_contain_text("Configuración")

    expect(page.get_by_text("Clientes Registrados")).to_be_visible()

    iframe_loc = page.locator("iframe").first
    expect(iframe_loc).to_be_visible(timeout=10000)

    frame = iframe_loc.content_frame
    tags = frame.locator(".tag")
    expect(tags.first).to_be_visible(timeout=10000)

    count = tags.count()
    assert count > 0, f"Expected client tags, found {count}"

    first_tag = tags.first
    style = first_tag.get_attribute("style") or ""
    assert "background-color" in style, f"Tag missing bg: {style}"

    x_button = first_tag.locator(".tag-x")
    expect(x_button).to_be_visible()
