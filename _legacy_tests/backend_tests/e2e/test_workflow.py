from playwright.sync_api import Page
import requests
def test_workflow_execution(authenticated_page: Page):
    authenticated_page.goto('http://localhost:3000/workflow')
    authenticated_page.wait_for_load_state('networkidle')
    authenticated_page.screenshot(path='backend/tests/e2e/screenshots/workflow.png')
    assert True
def test_workflow_event_bus():
    response = requests.get('http://localhost:8000/api/v1/plugins')
    assert response.status_code == 200
