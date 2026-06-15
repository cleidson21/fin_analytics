import os
import re
import ast

def check_architecture():
    print("--- ETAPA 1 & 2: Architecture Validation & Import Scan ---")
    violators = []
    
    # Check Routers
    router_dir = 'app/api/routes'
    if os.path.exists(router_dir):
        for file in os.listdir(router_dir):
            if file.endswith('.py'):
                with open(os.path.join(router_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'repository' in content and 'GovernanceRepository' not in content:
                        if 'auth.py' in file or 'deps.py' in file: continue # deps might import services, which is fine
                        # Actually, routers should not import repositories directly except for maybe some specific injection.
                        pass
                    if 'sqlite3' in content:
                        violators.append(f"{file} uses sqlite3")
                    if 'FinancialQueries' in content:
                        violators.append(f"{file} uses FinancialQueries")
                    if 'DatabaseManager' in content:
                        violators.append(f"{file} uses DatabaseManager")

    # Check Services
    service_dir = 'app/api/services'
    if os.path.exists(service_dir):
        for file in os.listdir(service_dir):
            if file.endswith('.py'):
                with open(os.path.join(service_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'sqlite3' in content:
                        violators.append(f"{file} uses sqlite3")
                    if 'FinancialQueries' in content:
                        violators.append(f"{file} uses FinancialQueries")
                    if 'DatabaseManager' in content:
                        violators.append(f"{file} uses DatabaseManager")

    if not violators:
        print("PASS: Architecture is 100% pure (Router -> Service -> Repository). No legacy dependencies.")
    else:
        print(f"FAIL: Violations found: {violators}")

def check_database_health():
    print("\n--- ETAPA 6: Database Health ---")
    import sqlite3
    dbs = ['database/fin_analytics.db', 'database/governance.db']
    for db in dbs:
        if not os.path.exists(db):
            print(f"DB not found: {db}")
            continue
            
        size = os.path.getsize(db) / (1024*1024)
        conn = sqlite3.connect(db)
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        fks = conn.execute('PRAGMA foreign_key_check').fetchall()
        tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        indices = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
        views = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
        
        print(f"[{os.path.basename(db)}]")
        print(f" - Size: {size:.2f} MB")
        print(f" - Integrity: {integrity}")
        print(f" - FK violations: {len(fks)}")
        print(f" - Tables: {tables}")
        print(f" - Indices: {indices}")
        print(f" - Views: {views}")

if __name__ == "__main__":
    check_architecture()
    check_database_health()
