import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Obter tokens
res = requests.post(f"{BASE_URL}/auth/token", data={"username": "admin", "password": "admin123"})
admin_token = res.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

print("=== TESTANDO COMO ADMIN ===")
r_pos = requests.get(f"{BASE_URL}/governance/positions?limit=2", headers=admin_headers)
print("GET /positions:", r_pos.status_code, r_pos.json().get("total") if r_pos.status_code==200 else "")

r_div = requests.get(f"{BASE_URL}/governance/dividends?limit=2", headers=admin_headers)
print("GET /dividends:", r_div.status_code, r_div.json().get("total") if r_div.status_code==200 else "")

r_cat = requests.get(f"{BASE_URL}/governance/categories?limit=2", headers=admin_headers)
print("GET /categories:", r_cat.status_code, r_cat.json().get("total") if r_cat.status_code==200 else "")

print("\n=== TESTANDO SEM TOKEN ===")
print("GET /positions:", requests.get(f"{BASE_URL}/governance/positions").status_code)
print("GET /dividends:", requests.get(f"{BASE_URL}/governance/dividends").status_code)
print("GET /categories:", requests.get(f"{BASE_URL}/governance/categories").status_code)
