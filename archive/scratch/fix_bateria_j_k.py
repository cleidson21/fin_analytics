import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "fin_analytics.db")

def fix_issues():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fix malformed parcelamento (Bateria J)
    cursor.execute("SELECT id_economico, parcelamento FROM transactions WHERE parcelamento NOT LIKE '%/%' AND parcelamento IS NOT NULL")
    malformadas = cursor.fetchall()
    
    for row in malformadas:
        print(f"Malformada: {row['id_economico']} -> {row['parcelamento']}")
        # Se for apenas um número, ex: "1", talvez devesse ser "1/1"
        if row['parcelamento'].isdigit():
            new_val = f"{row['parcelamento']}/{row['parcelamento']}"
            cursor.execute("UPDATE transactions SET parcelamento = ? WHERE id_economico = ?", (new_val, row['id_economico']))
            print(f"  Fixed: {new_val}")
        elif row['parcelamento'] == "":
            cursor.execute("UPDATE transactions SET parcelamento = NULL WHERE id_economico = ?", (row['id_economico'],))
            print("  Fixed: set to NULL")
            
    conn.commit()
    
    # Check duplicates (Bateria K)
    cursor.execute("SELECT data, descricao_original, valor_cents, COUNT(*) as c FROM transactions GROUP BY data, descricao_original, valor_cents HAVING c > 1")
    duplicadas = cursor.fetchall()
    print(f"\nDuplicadas encontradas: {len(duplicadas)}")
    for row in duplicadas:
        print(f" - {row['data']} | {row['descricao_original']} | {row['valor_cents']} -> {row['c']} vezes")
        
        # Opcional: deletar duplicatas mantendo apenas a primeira (se forem perfeitamente idênticas)
        cursor.execute("SELECT id_economico FROM transactions WHERE data=? AND descricao_original=? AND valor_cents=? ORDER BY criado_em ASC", 
                       (row['data'], row['descricao_original'], row['valor_cents']))
        ids = [r['id_economico'] for r in cursor.fetchall()]
        
        # Manter o primeiro, apagar o resto
        ids_to_delete = ids[1:]
        if ids_to_delete:
            for id_del in ids_to_delete:
                cursor.execute("DELETE FROM transactions WHERE id_economico=?", (id_del,))
            print(f"   Deletados duplicados: {ids_to_delete}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_issues()
