import time

def wait_for_element(page, selector, timeout=5000):
    page.wait_for_selector(selector, timeout=timeout)
