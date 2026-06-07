import requests

try:
    with open('_temp/novos_imports_drops/tableExport.csv', 'r', encoding='utf-8') as f:
        raw_text = f.read()

    payload = {
        "file_name": "tableExport.csv",
        "raw_text": raw_text
    }

    r = requests.post("http://localhost:8000/api/v1/governance/import-myprofit", json=payload)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(str(e))
