from playwright.sync_api import Page
def test_history_page(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/history')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.screenshot(path='backend/tests/e2e/screenshots/history.png')
    assert True
