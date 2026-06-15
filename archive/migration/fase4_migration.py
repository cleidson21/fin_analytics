import sqlite3
import shutil
from database.config import DATABASE_PATH, GOVERNANCE_DB_PATH
import time

def migrate():
    # Make backups before starting Phase 4
    shutil.copy2(DATABASE_PATH, 'database/fin_analytics_backup_F4.db')
    shutil.copy2(GOVERNANCE_DB_PATH, 'database/governance_backup_F4.db')
    print("Backups F4 criados.")
    
    conn_fin = sqlite3.connect(DATABASE_PATH)
    conn_gov = sqlite3.connect(GOVERNANCE_DB_PATH)
    
    # Mapeamento Origem -> Destino
    # Note: Na fase 3, we named the tables in governance as governance_rules, etc.
    # We must map:
    # rules -> governance_rules
    # prompt_versions -> governance_prompt_versions
    # ai_runs -> governance_ai_runs
    # audit_log -> governance_audit_log
    # event_links -> governance_reconciliation
    # import_runs, import_artifacts, raw_events, staging_* -> same name
    
    tables_map = {
        'rules': 'governance_rules',
        'prompt_versions': 'governance_prompt_versions',
        'ai_runs': 'governance_ai_runs',
        'audit_log': 'governance_audit_log',
        'event_links': 'governance_reconciliation',
        'import_runs': 'import_runs',
        'import_artifacts': 'import_artifacts',
        'raw_events': 'raw_events',
        'staging_imports': 'staging_imports',
        'staging_positions': 'staging_positions',
        'staging_dividends': 'staging_dividends',
        'staging_portfolio_evolution': 'staging_portfolio_evolution'
    }
    
    report = []
    start_time = time.time()
    
    conn_fin.row_factory = sqlite3.Row
    conn_gov.execute("PRAGMA foreign_keys = OFF;")
    conn_fin.execute("PRAGMA foreign_keys = OFF;")
    
    try:
        conn_gov.execute("BEGIN TRANSACTION;")
        for src, dst in tables_map.items():
            # Check if source exists
            exists = conn_fin.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{src}'").fetchone()
            if not exists:
                print(f"[{src}] Tabela nao existe na origem, pulando.")
                continue
            
            src_count = conn_fin.execute(f"SELECT COUNT(*) as c FROM {src}").fetchone()['c']
            
            if src_count == 0:
                print(f"[{src}] Tabela vazia na origem.")
                report.append(f"{src} -> {dst}: Origem: 0, Destino: 0")
                continue
                
            # Get columns from destination
            dst_cols_info = conn_gov.execute(f"PRAGMA table_info({dst})").fetchall()
            dst_cols = [c[1] for c in dst_cols_info]
            
            # Select from source. Be careful with renamed columns or schemas.
            # We assume for now columns are mostly identical or compatible. 
            # In Phase 2, `event_links` -> `governance_reconciliation` might differ in schema.
            # Let's get source columns.
            src_cols_info = conn_fin.execute(f"PRAGMA table_info({src})").fetchall()
            src_cols = [c[1] for c in src_cols_info]
            
            # Intersect columns
            common_cols = [c for c in src_cols if c in dst_cols]
            if not common_cols:
                print(f"[{src}] Nenhuma coluna em comum com {dst}!")
                continue
                
            cols_str = ', '.join(common_cols)
            placeholders = ', '.join(['?' for _ in common_cols])
            
            rows = conn_fin.execute(f"SELECT {cols_str} FROM {src}").fetchall()
            
            # Prepare insert
            insert_sql = f"INSERT INTO {dst} ({cols_str}) VALUES ({placeholders})"
            
            data_to_insert = []
            for row in rows:
                data_to_insert.append(tuple(row[c] for c in common_cols))
                
            conn_gov.executemany(insert_sql, data_to_insert)
            
            dst_count = conn_gov.execute(f"SELECT COUNT(*) as c FROM {dst}").fetchone()[0]
            
            print(f"[{src}] -> [{dst}]: Migrados {len(data_to_insert)} registros.")
            report.append(f"{src} -> {dst}: Origem: {src_count}, Destino: {dst_count}")
            
        conn_gov.commit()
        print("Migração de dados para governance.db concluída.")
        
        # Agora apagar as tabelas antigas na origem
        conn_fin.execute("BEGIN TRANSACTION;")
        # Habilitar pragma de alter table pra ter certeza
        conn_fin.execute("PRAGMA legacy_alter_table = ON")
        dropped = []
        for src in tables_map.keys():
            exists = conn_fin.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{src}'").fetchone()
            if exists:
                conn_fin.execute(f"DROP TABLE {src}")
                dropped.append(src)
                
        conn_fin.execute("PRAGMA legacy_alter_table = OFF")
        conn_fin.commit()
        print(f"Tabelas removidas da origem: {dropped}")
        
    except Exception as e:
        conn_gov.rollback()
        conn_fin.rollback()
        print("ERRO na migração:", e)
        return
        
    conn_gov.execute("PRAGMA foreign_keys = ON;")
    conn_fin.execute("PRAGMA foreign_keys = ON;")
    
    print("Executando Integrity Check...")
    fin_integ = conn_fin.execute("PRAGMA integrity_check").fetchone()[0]
    gov_integ = conn_gov.execute("PRAGMA integrity_check").fetchone()[0]
    
    print("FinAnalytics Integrity:", fin_integ)
    print("Governance Integrity:", gov_integ)
    
    duration = time.time() - start_time
    print(f"Tempo total: {duration:.2f} segundos")
    print("Relatorio Final:\n" + "\n".join(report))
    
    conn_fin.close()
    conn_gov.close()

if __name__ == "__main__":
    migrate()
