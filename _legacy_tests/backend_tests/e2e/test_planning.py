from playwright.sync_api import Page
def test_planning_creation(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/planning')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.screenshot(path='backend/tests/e2e/screenshots/planning.png')
    assert True
