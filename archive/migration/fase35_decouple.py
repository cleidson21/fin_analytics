import sqlite3
import re
import shutil
import sys

def remove_fk(sql):
    new_sql = re.sub(r',\s*FOREIGN KEY\(import_run_id\) REFERENCES import_runs\(id\) ON DELETE CASCADE', '', sql, flags=re.IGNORECASE)
    new_sql = re.sub(r'FOREIGN KEY\(import_run_id\) REFERENCES import_runs\(id\) ON DELETE CASCADE', '', new_sql, flags=re.IGNORECASE)
    return new_sql

def run():
    db_path = 'database/fin_analytics.db'
    backup_path = 'database/fin_analytics_backup_F3.db'
    
    print("Criando backup completo antes da Fase 3.5...")
    shutil.copy2(db_path, backup_path)
    print("Backup criado em", backup_path)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF;")
    
    tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution']
    
    try:
        conn.execute("BEGIN TRANSACTION;")
        
        for tbl in tables:
            print(f"Processando tabela {tbl}...")
            # Pega schema da tabela
            row = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}'").fetchone()
            if not row:
                print(f"Tabela {tbl} nao encontrada.")
                continue
                
            orig_sql = row[0]
            new_sql = remove_fk(orig_sql)
            
            # Pega schemas dos indexes
            indexes = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{tbl}' AND sql IS NOT NULL").fetchall()
            
            # Pega nome das colunas para insert
            cols_info = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
            col_names = [c[1] for c in cols_info]
            cols_str = ', '.join(col_names)
            
            # Modifica CREATE TABLE para _new
            create_new_sql = new_sql.replace(f'CREATE TABLE "{tbl}"', f'CREATE TABLE {tbl}_new')
            if f'CREATE TABLE {tbl}_new' not in create_new_sql:
                create_new_sql = create_new_sql.replace(f'CREATE TABLE {tbl}', f'CREATE TABLE {tbl}_new')
            
            print("Executando:", create_new_sql)
            conn.execute(create_new_sql)
            
            print(f"Copiando dados de {tbl} para {tbl}_new...")
            conn.execute(f"INSERT INTO {tbl}_new ({cols_str}) SELECT {cols_str} FROM {tbl}")
            
            print(f"Removendo antiga {tbl}...")
            # Habilitar alteracoes estruturais diretas
            conn.execute("PRAGMA legacy_alter_table = ON")
            conn.execute(f"DROP TABLE {tbl}")
            
            print(f"Renomeando {tbl}_new para {tbl}...")
            conn.execute(f"ALTER TABLE {tbl}_new RENAME TO {tbl}")
            conn.execute("PRAGMA legacy_alter_table = OFF")
            
            print(f"Recriando {len(indexes)} índices para {tbl}...")
            for idx in indexes:
                conn.execute(idx[0])
            
            print(f"Tabela {tbl} concluida.")
            
        print("Removendo view vw_rules_training_dataset...")
        conn.execute("DROP VIEW IF EXISTS vw_rules_training_dataset")
        
        conn.commit()
        print("Transação comitada com sucesso.")
        
    except Exception as e:
        conn.rollback()
        print("Erro durante execucao, transação desfeita.", e)
        sys.exit(1)
    
    conn.execute("PRAGMA foreign_keys = ON;")
    
    print("Validando Integridade...")
    integ = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    
    print("Integrity Check:", integ)
    print("Foreign Key Check:", fk_check)
    
    conn.close()
    
if __name__ == '__main__':
    run()
