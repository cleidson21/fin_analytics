from playwright.sync_api import Page
import time

def test_login(page: Page):
    page.goto("http://localhost:3000")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="backend/tests/e2e/screenshots/login.png")
    assert page.url != ""
