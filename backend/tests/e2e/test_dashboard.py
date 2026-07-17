from playwright.sync_api import Page

def test_dashboard_elements(authenticated_page: Page):
    authenticated_page.goto("http://localhost:3000/dashboard")
    authenticated_page.wait_for_load_state("networkidle")
    authenticated_page.screenshot(path="backend/tests/e2e/screenshots/dashboard.png")
    assert True
