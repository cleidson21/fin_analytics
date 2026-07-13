import subprocess
import time
import json
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

from backend.shared.security import create_access_token
from backend.shared.config import settings

print("Starting uvicorn...")
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

try:
    print("\n--- TESTE 1: POST /auth/token ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/token", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    print("Status:", s)
    print("Payload:", r)
    token = r.get("access_token") if isinstance(r, dict) else None

    print("\n--- TESTE 2: POST /auth/login ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    print("Status:", s)
    print("Payload:", r)

    print("\n--- TESTE 3: GET /auth/me ---")
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    print("Status:", s)
    print("Payload:", r)

    print("\n--- TESTE 4: Token invalido ---")
    inv_token = token[:-1] + ('a' if token[-1] != 'a' else 'b')
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {inv_token}"})
    print("Status:", s)
    print("Payload:", r)

    print("\n--- TESTE 5: Token expirado ---")
    import jose.jwt as jwt
    # Cria token expirado manualmente (1 min atrás)
    expire = datetime.utcnow() - timedelta(minutes=1)
    to_encode = {"exp": expire, "sub": "test-id"}
    expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    s, r = fetch("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    print("Status:", s)
    print("Payload:", r)

    print("\n--- TESTE 6: Seed Automatico ---")
    conn = sqlite3.connect("database/fin_analytics_v3.db")
    print("Payload:", conn.execute("SELECT * FROM users").fetchall())

    print("\n--- TESTE 7: Nao duplicacao de usuario ---")
    fetch("http://localhost:8000/api/v1/auth/token", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    fetch("http://localhost:8000/api/v1/auth/login", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    print("Payload:", conn.execute("SELECT COUNT(*) FROM users").fetchone())

    print("\n--- TESTE 8: Compatibilidade Frontend ---")
    print("Expected keys from login response: 'token', 'user' with username/role")
    s, r = fetch("http://localhost:8000/api/v1/auth/token", method="POST", data={"username": "admin@finanalytics.local", "password": "admin"})
    if isinstance(r, dict) and "token" in r and "user" in r and "username" in r["user"] and "role" in r["user"]:
        print("Status: Compatible")
        print("Payload:", r["user"])
    else:
        print("Status: Incompatible")

finally:
    print("\nTerminating uvicorn...")
    process.terminate()
    process.wait()
