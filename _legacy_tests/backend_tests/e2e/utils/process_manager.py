import asyncio
import socket
import subprocess
import os
import time
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_url(url: str, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    return True
        except (urllib.error.URLError, ConnectionResetError):
            time.sleep(1)
    return False

class ProcessManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.is_managed_backend = False
        self.is_managed_frontend = False

    def start_backend(self):
        if is_port_in_use(8000):
            logger.info("Backend is already running on port 8000")
            return
        logger.info("Starting Backend...")
        env = os.environ.copy()
        # Set testing environment if needed
        self.backend_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "backend.main:app", "--port", "8000"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.is_managed_backend = True
        if not wait_for_url("http://localhost:8000/api/v1/health", timeout=60):
            raise RuntimeError("Backend failed to start")

    def start_frontend(self):
        if is_port_in_use(3000):
            logger.info("Frontend is already running on port 3000")
            return
        logger.info("Starting Frontend...")
        frontend_dir = os.path.join(os.getcwd(), 'frontend')
        self.frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.is_managed_frontend = True
        if not wait_for_url("http://localhost:3000", timeout=60):
            raise RuntimeError("Frontend failed to start")

    def stop_all(self):
        if self.is_managed_frontend and self.frontend_process:
            logger.info("Stopping Frontend...")
            self.frontend_process.terminate()
            self.frontend_process.wait()
        if self.is_managed_backend and self.backend_process:
            logger.info("Stopping Backend...")
            self.backend_process.terminate()
            self.backend_process.wait()
