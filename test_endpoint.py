import requests
import json
import time

url = "http://127.0.0.1:8080/api/v1/pierre/import"

print("--- Teste 1: Body {} ---")
start = time.time()
r1 = requests.post(url, json={})
end = time.time()
print(f"Status: {r1.status_code}")
print(f"Tempo: {end - start:.2f}s")
try:
    print("Response:", r1.json())
except:
    print("Response Text:", r1.text)

print("\n--- Teste 2: Body com datas ---")
start = time.time()
r2 = requests.post(url, json={"start_date":"2026-07-01", "end_date":"2026-07-31"})
end = time.time()
print(f"Status: {r2.status_code}")
print(f"Tempo: {end - start:.2f}s")
try:
    print("Response:", r2.json())
except:
    print("Response Text:", r2.text)
