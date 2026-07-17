from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            record_video_dir="backend/tests/e2e/videos/"
        )
    def new_page(self):
        return self.context.new_page()
    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
