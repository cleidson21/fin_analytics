import pytest
from backend.tests.e2e.utils.process_manager import ProcessManager
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import os
import json

metrics = {}

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    pm = ProcessManager()
    pm.start_backend()
    pm.start_frontend()
    
    yield
    
    pm.stop_all()

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "backend/tests/e2e/videos/",
        "record_har_path": "backend/tests/e2e/network/network.har"
    }

@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    # Go to login
    page.goto("http://localhost:3000")
    # Simulate login if necessary (Assuming local dev environment auto-logs in or we fill a form)
    # The exact login flow depends on the actual frontend implementation
    # Just navigate and ensure dashboard is loaded
    page.goto("http://localhost:3000/dashboard")
    page.wait_for_load_state('networkidle')
    yield page

def pytest_html_report_title(report):
    report.title = "FINANALYTICS V3 - E2E Validation Report"
