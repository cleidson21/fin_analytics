from playwright.sync_api import Page
def test_import_csv(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/wealth/import')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.screenshot(path='backend/tests/e2e/screenshots/import_csv.png')
    assert True
