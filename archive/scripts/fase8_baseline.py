import time
import os
import psutil
from fastapi.testclient import TestClient
from app.api.main import app

def measure_baseline():
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    start_time = time.time()
    client = TestClient(app)
    startup_ms = (time.time() - start_time) * 1000

    endpoints = [
        ('/api/v1/auth/me', 'Auth (Current User)'),
        ('/api/v1/transactions', 'Financeiro (Transactions)'),
        ('/api/v1/dashboard/summary', 'Financeiro (Dashboard)'),
        ('/api/v1/accounts/summary', 'Financeiro (Accounts)'),
        ('/api/v1/catalog/accounts', 'Financeiro (Catalog)'),
        ('/api/v1/governance/imports', 'Governança (Imports)'),
        ('/api/v1/governance/prompts', 'Governança (Prompts)'),
        ('/api/v1/governance/learning/metrics', 'Governança (Learning Metrics)'),
        ('/api/v1/governance/audit-logs', 'Governança (Audit Logs)')
    ]

    total_time = 0
    runs = 10
    
    for ep, name in endpoints:
        for _ in range(runs):
            t0 = time.time()
            client.get(ep)
            total_time += (time.time() - t0) * 1000
            
    avg_query_time = total_time / (len(endpoints) * runs)
    mem_after = process.memory_info().rss / (1024 * 1024)

    print(f"BASELINE_AVG_QUERY_MS={avg_query_time:.2f}")
    print(f"BASELINE_MEM_MB={mem_after:.2f}")
    
    with open('database/baseline.txt', 'w') as f:
        f.write(f"{avg_query_time},{mem_after}")

if __name__ == '__main__':
    measure_baseline()
