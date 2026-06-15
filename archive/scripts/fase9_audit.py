import os
import ast
import sqlite3
import time
from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

def scan_coverage_and_security():
    print("--- ETAPA 1 & 6 & 7: Test Coverage, Security & Tech Debt ---")
    
    target_dirs = ['app/api/routes', 'app/api/services', 'database', 'app/core', 'etl']
    files_stats = []
    
    security_map = []
    tech_debt = []
    
    total_funcs = 0
    total_tested = 0 # Mocked logic: we don't have real tests except test_smoke.py
    
    for d in target_dirs:
        if not os.path.exists(d): continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    path = os.path.join(root, file).replace('\\\\', '/')
                    size = os.path.getsize(path)
                    
                    if size > 20 * 1024:
                        tech_debt.append({'file': path, 'size': size, 'reason': 'File > 20KB', 'impact': 'Hard to maintain'})
                    
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            tree = ast.parse(content)
                            
                            funcs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)]
                            func_count = len(funcs)
                            total_funcs += func_count
                            
                            # Security check for routes
                            if 'routes' in path:
                                for func in funcs:
                                    # Very basic check for dependencies
                                    is_public = True
                                    is_admin = False
                                    is_auth = False
                                    
                                    func_source = ast.get_source_segment(content, func)
                                    if func_source:
                                        if 'verify_admin' in func_source:
                                            is_admin = True
                                            is_public = False
                                        elif 'get_current_user' in func_source:
                                            is_auth = True
                                            is_public = False
                                            
                                        security_map.append({
                                            'endpoint': func.name,
                                            'file': path,
                                            'type': 'ADMIN' if is_admin else ('AUTH' if is_auth else 'PUBLIC')
                                        })
                                        
                            # Check large methods
                            for func in funcs:
                                if hasattr(func, 'end_lineno') and hasattr(func, 'lineno'):
                                    lines = func.end_lineno - func.lineno
                                    if lines > 50:
                                        tech_debt.append({'file': path, 'size': lines, 'reason': f'Method {func.name} > 50 lines', 'impact': 'High Cognitive Complexity'})
                            
                            # Coverage mock
                            files_stats.append({
                                'file': path,
                                'funcs': func_count,
                                'tested': 0, # Since we have no unit tests, just smoke tests
                                'cov': 0
                            })
                    except Exception as e:
                        pass
                        
    # Sort tech debt
    tech_debt = sorted(tech_debt, key=lambda x: x['size'], reverse=True)[:20]
    
    return files_stats, security_map, tech_debt

def check_databases():
    print("--- ETAPA 4: Database Consistency ---")
    dbs = ['database/fin_analytics.db', 'database/governance.db']
    db_stats = {}
    
    for db in dbs:
        if not os.path.exists(db): continue
        size = os.path.getsize(db) / (1024*1024)
        conn = sqlite3.connect(db)
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        fks = conn.execute('PRAGMA foreign_key_check').fetchall()
        tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        indices = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
        views = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
        
        db_stats[db] = {
            'size_mb': round(size, 2),
            'integrity': integrity,
            'fks': len(fks),
            'tables': tables,
            'indices': indices,
            'views': views
        }
    return db_stats

def run_performance():
    print("--- ETAPA 2 & 5: Contract & Performance ---")
    client = TestClient(app)
    
    endpoints = [
        ('/api/v1/auth/me', 'auth'),
        ('/api/v1/transactions', 'transactions'),
        ('/api/v1/dashboard/summary', 'dashboard'),
        ('/api/v1/accounts/summary', 'accounts'),
        ('/api/v1/catalog/accounts', 'catalog'),
        ('/api/v1/governance/imports', 'imports'),
        ('/api/v1/governance/prompts', 'prompts'),
        ('/api/v1/governance/learning/metrics', 'learning'),
        ('/api/v1/internal/health', 'internal')
    ]
    
    total_time = 0
    max_time = 0
    results = []
    
    for ep, name in endpoints:
        t0 = time.time()
        try:
            resp = client.get(ep)
            dt = (time.time() - t0) * 1000
            total_time += dt
            max_time = max(max_time, dt)
            status = resp.status_code
            
            results.append({
                'endpoint': ep,
                'status': status,
                'time_ms': round(dt, 2)
            })
        except Exception as e:
            results.append({
                'endpoint': ep,
                'status': '500_EXCEPTION',
                'time_ms': 0
            })
            
    avg_time = total_time / len(endpoints)
    return results, avg_time, max_time

if __name__ == '__main__':
    cov, sec, debt = scan_coverage_and_security()
    db = check_databases()
    perf_results, avg_time, max_time = run_performance()
    
    # Dump to txt so we can read it easily
    with open('fase9_raw_data.txt', 'w', encoding='utf-8') as f:
        f.write(f"COVERAGE: {len(cov)} files analyzed.\\n")
        f.write(f"TECH DEBT TOP 5: {debt[:5]}\\n")
        f.write(f"DB STATS: {db}\\n")
        f.write(f"AVG TIME: {avg_time}\\n")
        f.write(f"MAX TIME: {max_time}\\n")
        f.write(f"PERF RESULTS: {perf_results}\\n")
        
    print("Audit generated fase9_raw_data.txt")
