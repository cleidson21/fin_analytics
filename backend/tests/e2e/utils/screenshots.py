import os

def take_screenshot(page, name):
    os.makedirs("backend/tests/e2e/screenshots", exist_ok=True)
    page.screenshot(path=f"backend/tests/e2e/screenshots/{name}.png")
