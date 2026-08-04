import requests
import json

BASE = "http://127.0.0.1:8080/api/v1"

endpoints = [
    ("GET", "/accounts"),
    ("GET", "/transactions"),
    ("GET", "/categories"),
    ("GET", "/dashboard"),
    ("POST", "/pierre/import", {"start_date": "2026-07-01", "end_date": "2026-07-31"}),
]

for entry in endpoints:
    method = entry[0]
    path = entry[1]
    body = entry[2] if len(entry) > 2 else None

    if method == "GET":
        r = requests.get(BASE + path)
    else:
        r = requests.post(BASE + path, json=body)

    print(f"\n{method} {path}")
    print(f"  Status : {r.status_code}")
    try:
        data = r.json()
        if isinstance(data, list):
            print(f"  Count  : {len(data)}")
            if data:
                print(f"  Sample : {json.dumps(data[0], default=str)[:300]}")
        elif isinstance(data, dict):
            print(f"  Body   : {json.dumps(data, default=str)[:400]}")
    except Exception as e:
        print(f"  Error parsing response: {e}")
