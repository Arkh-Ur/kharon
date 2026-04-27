import os
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, Browser, BrowserType, expect


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {
        "headless": False,
        "slow_mo": 0,
    }


@pytest.fixture(scope="session")
def context_args(browser_type, browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "viewport": None,
    }


@pytest.fixture(scope="function")
def browser(browser_type: BrowserType) -> Browser:
    browser = browser_type.launch()
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser, request) -> Page:
    context = browser.new_context()
    page = context.new_page()
    
    viewport_size = {"width": 1400, "height": 900}
    page.set_viewport_size(viewport_size)
    
    def take_screenshot_on_failure():
        if request.node.rep_call.failed:
            screenshot_dir = Path(__file__).parent / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            test_name = request.node.name.replace("[", "").replace("]", "")
            screenshot_path = screenshot_dir / f"{test_name}_failure.png"
            page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved to: {screenshot_path}")
    
    request.addfinalizer(take_screenshot_on_failure)
    
    yield page
    context.close()


@pytest.fixture(scope="function")
def webapp_base_url():
    return "http://localhost:8501"


@pytest.fixture(scope="function")
def airflow_base_url():
    return "http://localhost:8080"


@pytest.fixture(scope="function")
def airflow_password():
    env_password = os.environ.get("KHARON_AIRFLOW_PASSWORD")
    if env_password:
        return env_password
    
    fallback_path = "airflow_home/simple_auth_manager_passwords.json.generated"
    try:
        with open(fallback_path, 'r') as f:
            data = f.read().strip()
            return data
    except FileNotFoundError:
        raise RuntimeError(
            "KHARON_AIRFLOW_PASSWORD not found and fallback file not available. "
            "Please set the environment variable or ensure the fallback file exists."
        )


@pytest.fixture(scope="function")
def page_wait_time():
    return 8