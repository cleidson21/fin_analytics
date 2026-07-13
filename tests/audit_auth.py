import subprocess
import time
import json
import sqlite3
import urllib.request
import urllib.error
import urllib.parse

print("Starting uvicorn...")
process = subprocess.Popen(["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
time.sleep(4)

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

try:
    print("\n--- 1. Health Check ---")
    s, r = fetch("http://localhost:8000/api/v1/health")
    print(s, r)

    print("\n--- 2. Login Valido ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    print(s, r)
    token = r.get("access_token") if isinstance(r, dict) else None

    print("\n--- 3. Login Invalido ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "wrong"})
    print(s, r)

    print("\n--- 4. Seed Automatico ---")
    conn = sqlite3.connect("database/fin_analytics_v3.db")
    print(conn.execute("SELECT * FROM users").fetchall())

    print("\n--- 5. Duplicacao de Seed ---")
    fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    print(conn.execute("SELECT COUNT(*) FROM users").fetchone())

    print("\n--- 6. Token JWT ---")
    from backend.shared.security import create_access_token
    print(create_access_token('admin@finanalytics.local'))

    print("\n--- 7. Endpoint /me ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(s, r)

    print("\n--- 8. Token invalido ---")
    inv_token = token[:-1] + ('a' if token[-1] != 'a' else 'b')
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {inv_token}"})
    print(s, r)

finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
