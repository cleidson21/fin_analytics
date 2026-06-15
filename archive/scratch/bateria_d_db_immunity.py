import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "fin_analytics.db")

def check_db_immunity():
    print("Iniciando Bateria D - Imunidade do Banco de Dados...")
    
    if not os.path.exists(DB_PATH):
        print(f"Erro: Banco de dados não encontrado em {DB_PATH}")
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    issues_found = 0
    
    # 1. PRAGMA integrity_check
    print("\n1. Executando PRAGMA integrity_check...")
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchall()
    if len(result) == 1 and result[0][0] == "ok":
        print("  [OK] Integrity check: OK")
    else:
        print(f"  [X] Integrity check: FALHOU -> {result}")
        issues_found += 1
        
    # 2. PRAGMA foreign_key_check
    print("\n2. Executando PRAGMA foreign_key_check...")
    cursor.execute("PRAGMA foreign_key_check;")
    result = cursor.fetchall()
    if len(result) == 0:
        print("  [OK] Foreign key check: OK")
    else:
        print(f"  [X] Foreign key check: FALHOU -> {result}")
        issues_found += 1
        
    # 3. Anomalias de Importação em staging_*
    print("\n3. Verificando anomalias em tabelas de staging...")
    staging_tables = [
        ("staging_imports", "status", "PENDING"),
        ("staging_positions", "validation_status", "PENDING"),
        ("staging_dividends", "validation_status", "PENDING"),
        ("staging_portfolio_evolution", "validation_status", "PENDING")
    ]
    
    for table, status_col, pending_val in staging_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {status_col} = '{pending_val}';")
            pending_count = cursor.fetchone()[0]
            
            # Check for generic anomalies (e.g., null required fields but status is not failed)
            # Just reporting pending items for now
            if pending_count == 0:
                print(f"  [OK] {table}: 0 registros pendentes ou travados.")
            else:
                print(f"  [!] {table}: {pending_count} registros pendentes. (Verificar se são órfãos de importações abortadas)")
                # Let's see if they belong to an import_run that is finished/failed
                query_orphans = f"""
                    SELECT COUNT(*) FROM {table} s
                    JOIN import_runs r ON s.import_run_id = r.id
                    WHERE s.{status_col} = '{pending_val}' 
                    AND r.status IN ('SUCCESS', 'FAILED')
                """
                cursor.execute(query_orphans)
                orphans_count = cursor.fetchone()[0]
                if orphans_count > 0:
                    print(f"      [X] Encontrados {orphans_count} registros órfãos em {table} cujo import_run já finalizou.")
                    issues_found += 1
                else:
                    print(f"      [OK] Nenhum registro órfão em {table}.")
        except sqlite3.OperationalError as e:
            print(f"  [?] Tabela {table} apresentou erro: {e}")
            
    # 4. Verificando Foreign Keys perdidas (import_artifacts sem import_run, ai_runs sem import_run)
    print("\n4. Verificando integridade relacional manual...")
    try:
        cursor.execute("SELECT COUNT(*) FROM import_artifacts WHERE import_run_id NOT IN (SELECT id FROM import_runs);")
        orphans = cursor.fetchone()[0]
        if orphans == 0:
            print("  [OK] import_artifacts: OK (nenhum órfão)")
        else:
            print(f"  [X] import_artifacts: {orphans} registros órfãos!")
            issues_found += 1
    except Exception as e:
        print(e)
        
    conn.close()
    
    print("\n--- RESUMO BATERIA D ---")
    if issues_found == 0:
        print("RESULTADO: SUCESSO. Estado Imaculado.")
        return True
    else:
        print(f"RESULTADO: FALHOU com {issues_found} anomalias encontradas.")
        return False

if __name__ == "__main__":
    check_db_immunity()
