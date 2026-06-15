import sqlite3
import os
import re
from pathlib import Path

def get_db_path():
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "database" / "fin_analytics.db"

def add_fk_to_create_stmt(create_stmt, fk_clause):
    # Encontra o último parêntese antes do final (que fecha a definição da tabela)
    idx = create_stmt.rfind(')')
    if idx == -1:
        raise ValueError("Nao encontrou fechamento de CREATE TABLE")
    # Injeta a fk logo antes do parêntese final
    return create_stmt[:idx] + ",\n    " + fk_clause + "\n" + create_stmt[idx:]

def extract_create_table(schema_sql, table_name):
    pattern = r"CREATE TABLE IF NOT EXISTS " + table_name + r"\s*\((.*?)\);(?=\s*CREATE|\s*$)"
    match = re.search(pattern, schema_sql, re.IGNORECASE | re.DOTALL)
    if match:
        return f"CREATE TABLE {table_name}_new ({match.group(1)});"
    raise ValueError(f"CREATE TABLE for {table_name} not found in schema.sql")

def migrate():
    db_path = get_db_path()

    tables_to_migrate = [
        "transactions",
        "positions",
        "dividends",
        "portfolio_evolution",
        "staging_imports"
    ]

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("BEGIN TRANSACTION;")

        # 1. Inserir import_run legado
        conn.execute("""
            INSERT OR IGNORE INTO import_runs 
            (id, source_type, file_name, checksum, started_at, status)
            VALUES (
                'legacy-orphaned-imports', 
                'SYSTEM', 
                'legacy', 
                'legacy', 
                CURRENT_TIMESTAMP, 
                'LEGACY'
            );
        """)

        # 2. Atualizar orfaos em todas as 5 tabelas
        for tbl in tables_to_migrate:
            if tbl == "staging_imports":
                sql_update = f"""
                    UPDATE {tbl} 
                    SET import_run_id = 'legacy-orphaned-imports',
                        source_line_no = id
                    WHERE import_run_id IS NOT NULL 
                      AND import_run_id NOT IN (SELECT id FROM import_runs)
                """
            else:
                sql_update = f"""
                    UPDATE {tbl} 
                    SET import_run_id = 'legacy-orphaned-imports' 
                    WHERE import_run_id IS NOT NULL 
                      AND import_run_id NOT IN (SELECT id FROM import_runs)
                """
            cursor = conn.execute(sql_update)
            print(f"Updated {cursor.rowcount} orphans in {tbl}")

        # 3. Recriar as tabelas com o novo schema
        for tbl in tables_to_migrate:
            # Pegar o create table atual do sqlite_master
            current_create_stmt = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}'").fetchone()[0]
            if not current_create_stmt:
                raise ValueError(f"Tabela {tbl} não encontrada no banco.")
            
            # Renomear para _new (precisamos trocar CREATE TABLE <tbl> por CREATE TABLE <tbl>_new)
            # Para evitar trocar sub-strings não intencionais, vamos usar regex simples
            # ou apenas substituir a primeira ocorrencia de 'CREATE TABLE "tbl"' ou 'CREATE TABLE tbl'
            import re
            create_stmt_new = re.sub(
                r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?' + tbl + r'["\']?',
                f'CREATE TABLE {tbl}_new',
                current_create_stmt,
                flags=re.IGNORECASE
            )
            
            # Adicionar a FK
            fk_clause = "FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE"
            create_stmt_new = add_fk_to_create_stmt(create_stmt_new, fk_clause)

            # Criar a nova tabela
            conn.execute(create_stmt_new)

            # Obter colunas
            cols_info = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
            cols = [c[1] for c in cols_info]
            col_str = ", ".join(cols)

            # Copiar os dados
            conn.execute(f"INSERT INTO {tbl}_new ({col_str}) SELECT {col_str} FROM {tbl}")

            # Dropar antiga e renomear nova
            conn.execute("PRAGMA legacy_alter_table = ON")
            conn.execute(f"DROP TABLE {tbl}")
            conn.execute(f"ALTER TABLE {tbl}_new RENAME TO {tbl}")
            conn.execute("PRAGMA legacy_alter_table = OFF")

            print(f"Table {tbl} recreated with FKs successfully.")

        conn.commit()
        print("\nMigration concluída com sucesso!")
        
        # Check FK violations
        conn.execute("PRAGMA foreign_keys = ON;")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            print("AVISO: Violações de FK encontradas após migração:", violations)
        else:
            print("OK: Zero violações de FK no banco.")

    except Exception as e:
        conn.rollback()
        print("ERRO na migration:", e)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
