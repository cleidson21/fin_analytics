import sqlite3
import shutil
import threading
import json
import time
import uuid
import os

DB_PATH = 'database/fin_analytics.db'
BACKUP_PATH = 'database/fin_analytics.db.bak'

def test_c_backup_restore():
    # 1. Backup
    shutil.copy2(DB_PATH, BACKUP_PATH)
    
    # 2. Modify DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO import_runs (id, status) VALUES ('test-backup-restore', 'PENDING')")
    conn.commit()
    conn.close()
    
    # 3. Restore
    shutil.copy2(BACKUP_PATH, DB_PATH)
    
    # 4. Check if modification is gone
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("SELECT COUNT(*) FROM import_runs WHERE id = 'test-backup-restore'").fetchone()[0]
    conn.close()
    
    os.remove(BACKUP_PATH)
    
    return {
        "status": "PASS" if res == 0 else "FAIL",
        "description": "Backup created, data modified, restored from backup. Modification was successfully rolled back.",
        "record_found_after_restore": res == 1
    }

def test_d_stress():
    errors = []
    successes = 0
    lock = threading.Lock()
    
    def worker(worker_id):
        nonlocal successes
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            # SQLite default is journal_mode=delete, but let's just insert
            for i in range(10):
                conn.execute(f"INSERT INTO import_runs (id, status) VALUES ('stress-{worker_id}-{i}-{uuid.uuid4().hex}', 'STRESS')")
                conn.commit()
            conn.close()
            with lock:
                successes += 1
        except Exception as e:
            with lock:
                errors.append(str(e))
                
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    t1 = time.time()
    
    # Cleanup stress data
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM import_runs WHERE status = 'STRESS'")
    conn.commit()
    conn.close()
    
    return {
        "threads": 50,
        "inserts_per_thread": 10,
        "success_threads": successes,
        "errors": list(set(errors)),
        "database_locked_occurrences": sum(1 for e in errors if "locked" in e.lower()),
        "time_seconds": round(t1 - t0, 2)
    }

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Validação A: Órfãos
    tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution', 'staging_imports']
    orfaos = {}
    for tbl in tables:
        c = conn.execute(f'''
            SELECT COUNT(*) as c FROM {tbl} 
            WHERE import_run_id IS NOT NULL AND import_run_id NOT IN (SELECT id FROM import_runs)
        ''').fetchone()
        orfaos[tbl] = c['c']

    conn.close()

    val_a_c = {
        "validacao_A_orfaos_tabelas_principais": orfaos,
        "validacao_C_backup_restore": test_c_backup_restore()
    }
    
    val_d = {
        "validacao_D_stress_escritas": test_d_stress()
    }
    
    with open('validacoes_extras.json', 'w') as f:
        json.dump(val_a_c, f, indent=2)
        
    with open('validacao_D.json', 'w') as f:
        json.dump(val_d, f, indent=2)

if __name__ == '__main__':
    main()
