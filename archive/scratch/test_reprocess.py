import requests
r = requests.post("http://localhost:8000/api/v1/governance/imports/b4e90e0a2e11439aae384f6783bf5174/reprocess")
print(r.status_code)
print(r.text)
