import subprocess
import time
import json
import urllib.request
import urllib.parse

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
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        "/api/v1/dashboard/summary-v2?month=2026-06",
        "/api/v1/dashboard/pacing-v2?month=2026-06",
        "/api/v1/dashboard/heatmap?month=2026-06",
        "/api/v1/dashboard/categories?month=2026-06",
        "/api/v1/catalog"
    ]

    for ep in endpoints:
        print(f"\\nTesting GET {ep}...")
        status, data = fetch(f"http://localhost:8000{ep}", headers=headers)
        print("Status Code:", status)
        if status == 200:
            print("Response:", data)
        else:
            print("Error:", data)

finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
