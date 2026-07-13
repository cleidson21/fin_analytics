import subprocess
import time
import json
import urllib.request
import urllib.error

from backend.shared.security import create_access_token

print("Starting Uvicorn...")
process = subprocess.Popen(["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
time.sleep(3)

def fetch(url, method="GET", headers={}):
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 500, str(e)

try:
    token = create_access_token("064a944b-c4ff-4512-b661-37be968f0463")
    valid_headers = {"Authorization": f"Bearer {token}"}
    invalid_headers = {"Authorization": "Bearer invalid_token_123"}

    print("\n--- TEST: VALID JWT (installments) ---")
    status, data = fetch("http://localhost:8000/api/v1/dashboard/installments?month=2026-06", headers=valid_headers)
    print("Status:", status)
    print("Data keys:", data.keys() if isinstance(data, dict) else data)

    print("\n--- TEST: VALID JWT (subscriptions) ---")
    status, data = fetch("http://localhost:8000/api/v1/dashboard/subscriptions?month=2026-06", headers=valid_headers)
    print("Status:", status)
    print("Data keys:", data.keys() if isinstance(data, dict) else data)

    print("\n--- TEST: INVALID JWT ---")
    status, data = fetch("http://localhost:8000/api/v1/dashboard/installments?month=2026-06", headers=invalid_headers)
    print("Status:", status)
    print("Data:", data)

finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
