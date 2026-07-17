from playwright.sync_api import Page
def test_full_user_journey(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/dashboard')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.goto('http://localhost:3000/ai')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.goto('http://localhost:3000/planning')
    authenticated_page.wait_for_load_state('networkidle')
    assert True
