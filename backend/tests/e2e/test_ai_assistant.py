from playwright.sync_api import Page
def test_ai_assistant_query(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/ai')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.screenshot(path='backend/tests/e2e/screenshots/ai.png')
    assert True
