import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.config import GOVERNANCE_DB_PATH
from database.governance_repository import GovernanceRepository
import time

def run_test():
    print(f"Testando GovernanceRepository em {GOVERNANCE_DB_PATH}")
    repo = GovernanceRepository(GOVERNANCE_DB_PATH)
    start = time.time()
    results = repo.test_connection_and_counts()
    latency = time.time() - start
    
    print(f"Latency: {latency*1000:.2f}ms")
    for tbl, res in results.items():
        print(f"{tbl}: {res}")

if __name__ == "__main__":
    run_test()
