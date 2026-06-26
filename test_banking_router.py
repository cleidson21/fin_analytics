import subprocess
import time
import json
import urllib.request
import urllib.parse

from backend.shared.security import create_access_token
from backend.shared.config import settings

print("Starting Uvicorn...")
process = subprocess.Popen(["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
time.sleep(3)

def fetch(url, method="GET", data=None, headers={}):
    req = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req.data = urllib.parse.urlencode(data).encode('utf-8')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 500, str(e)

try:
    # Generate a valid token
    token = create_access_token("064a944b-c4ff-4512-b661-37be968f0463")
    headers = {"Authorization": f"Bearer {token}"}

    print("\nTesting GET /api/v1/transactions...")
    status, data = fetch("http://localhost:8000/api/v1/transactions", headers=headers)
    print("Status Code:", status)
    if status == 200:
        print("Response keys:", list(data.keys()))
        print(f"Total: {data.get('total')}, Limit: {data.get('limit')}, Offset: {data.get('offset')}")
        print("Items returned:", len(data.get("items", [])))
        print("First item if any:", data.get("items")[0] if data.get("items") else None)
    else:
        print("Error:", data)

    print("\nTesting GET /api/v1/transactions with filters...")
    status, data = fetch("http://localhost:8000/api/v1/transactions?limit=10&offset=5&category=Food", headers=headers)
    print("Status Code:", status)
    if status == 200:
        print(f"Limit used: {data.get('limit')}, Offset used: {data.get('offset')}")
    else:
        print("Error:", data)
finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
