import subprocess
import time
import json
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
import os

from backend.shared.security import create_access_token
from backend.shared.config import settings
import jose.jwt as jwt

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
    print("\n--- VALIDAÇÃO 2 — JWT ---")
    status, payload_login = fetch("http://localhost:8000/api/v1/auth/token", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    token = payload_login.get("access_token")
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    print("Decoded JWT:", decoded)
    print("Has 'sub':", "sub" in decoded)
    print("Has 'exp':", "exp" in decoded)

    print("\n--- VALIDAÇÃO 3 — EQUIVALÊNCIA DE ENDPOINTS ---")
    status1, payload1 = fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    status2, payload2 = fetch("http://localhost:8000/api/v1/auth/token", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    
    # We must exclude the tokens themselves because they expire at different timestamps or have different signatures, 
    # but their structure should be identical. Actually, if called in the same second they might be identical.
    # Let's compare keys and the user object
    print("Same keys:", payload1.keys() == payload2.keys())
    print("User identical:", payload1.get("user") == payload2.get("user"))
    print("Both have access_token:", "access_token" in payload1 and "access_token" in payload2)

    print("\n--- VALIDAÇÃO 4 — TOKEN INVÁLIDO ---")
    inv_token = "invalid.token.123"
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {inv_token}"})
    print("Status:", s)

    print("\n--- VALIDAÇÃO 5 — TOKEN EXPIRADO ---")
    expire = datetime.utcnow() - timedelta(minutes=1)
    to_encode = {"exp": expire, "sub": "test-id"}
    expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    print("Status:", s)

    print("\n--- VALIDAÇÃO 6 — BANCO ---")
    conn = sqlite3.connect("database/fin_analytics_v3.db")
    print("COUNT users:", conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    user = conn.execute("SELECT * FROM users").fetchone()
    print("USER DATA:", user)
    columns = [desc[0] for desc in conn.execute("PRAGMA table_info(users)").fetchall()]
    print("Has password_hash:", "password_hash" in columns)
    
    print("\n--- VALIDAÇÃO 7 — MIGRATIONS ---")
    migrations = conn.execute("SELECT * FROM _schema_migrations").fetchall()
    print("Migrations Count:", len(migrations))
    for m in migrations:
        print(" ", m[0])

finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
