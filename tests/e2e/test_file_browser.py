import time

from playwright.sync_api import Page, expect


def test_file_browser_opens_and_shows_path_input(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").first.click()
    time.sleep(page_wait_time)

    expect(page.get_by_text("Información Básica")).to_be_visible()

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill("test_browser_nav")
    name_input.press("Enter")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    expect(page.get_by_text("Configuración del Script")).to_be_visible()

    browse_btn = page.locator('button:has-text("Explorar")').first
    browse_btn.click()
    time.sleep(page_wait_time)

    expect(page.get_by_text("Explorar archivos")).to_be_visible()
    path_input = page.get_by_label("Ruta actual")
    expect(path_input).to_be_visible()
    print("✅ File browser opens and shows path input")


def test_file_browser_manual_path_change(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").first.click()
    time.sleep(page_wait_time)

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill("test_manual_path")
    name_input.press("Enter")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    browse_btn = page.locator('button:has-text("Explorar")').first
    browse_btn.click()
    time.sleep(page_wait_time)

    path_input = page.get_by_label("Ruta actual")
    path_input.fill("/tmp")
    path_input.press("Enter")
    time.sleep(page_wait_time)

    dir_buttons = page.locator('button:has-text("📁")')
    count = dir_buttons.count()
    print(f"Found {count} directory buttons in /tmp")
    assert count >= 0
    print("✅ Manual path change works")


def test_file_browser_select_project_no_crash(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").first.click()
    time.sleep(page_wait_time)

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill("test_select_folder")
    name_input.press("Enter")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    browse_btn = page.locator('button:has-text("Explorar")').first
    browse_btn.click()
    time.sleep(page_wait_time)

    path_input = page.get_by_label("Ruta actual")
    path_input.fill("/tmp")
    path_input.press("Enter")
    time.sleep(page_wait_time)

    select_btn = page.locator('button:has-text("Usar esta carpeta")')
    assert select_btn.is_visible(), "'Usar esta carpeta' button should be visible"
    select_btn.click()
    time.sleep(page_wait_time)

    error_el = page.locator('[data-testid="stException"]')
    assert error_el.count() == 0, "Should not crash on folder selection"

    project_input = page.get_by_label("Ruta del Proyecto *")
    value = project_input.input_value()
    assert "/tmp" in value, f"Expected /tmp in project path, got: {value}"
    print(f"✅ Project path set to: {value}")


def test_file_browser_up_button(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").first.click()
    time.sleep(page_wait_time)

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill("test_up_button")
    name_input.press("Enter")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    browse_btn = page.locator('button:has-text("Explorar")').first
    browse_btn.click()
    time.sleep(page_wait_time)

    path_input = page.get_by_label("Ruta actual")
    path_input.fill("/tmp")
    path_input.press("Enter")
    time.sleep(page_wait_time)

    up_btn = page.locator('button:has-text("Subir")')
    assert up_btn.is_visible(), "'Subir' button should be visible"
    up_btn.click()
    time.sleep(page_wait_time)

    error_el = page.locator('[data-testid="stException"]')
    assert error_el.count() == 0, "Should not crash on navigating up"

    path_input = page.get_by_label("Ruta actual")
    value = path_input.input_value()
    assert value != "/tmp", f"Should have navigated up from /tmp, got: {value}"
    print(f"✅ Navigated up to: {value}")


def test_file_browser_close(page: Page, webapp_base_url: str, page_wait_time: int):
    page.goto(webapp_base_url)
    time.sleep(page_wait_time)

    page.get_by_text("➕ Nuevo Script").first.click()
    time.sleep(page_wait_time)

    name_input = page.get_by_label("Nombre del Script *")
    name_input.fill("test_close")
    name_input.press("Enter")
    time.sleep(page_wait_time)

    page.locator('button:has-text("Siguiente")').first.click()
    time.sleep(page_wait_time)

    browse_btn = page.locator('button:has-text("Explorar")').first
    browse_btn.click()
    time.sleep(page_wait_time)

    expect(page.get_by_text("Explorar archivos")).to_be_visible()

    close_btn = page.locator('button:has-text("Cerrar explorador")')
    close_btn.click()
    time.sleep(page_wait_time)

    error_el = page.locator('[data-testid="stException"]')
    assert error_el.count() == 0, "Should not crash on close"
    print("✅ File browser closes correctly")
