import sqlite3

def run_health_check():
    conn = sqlite3.connect('database/fin_analytics.db')
    cursor = conn.cursor()

    print("--- Bateria 6: Health Check Completo do Banco ---")
    
    # 1. Integrity check
    integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"Integrity Check: {integrity}")

    # 2. Foreign Keys check
    fk_check = cursor.execute("PRAGMA foreign_key_check").fetchall()
    print(f"Foreign Key Violations: {len(fk_check)}")

    # 3. Orphans (transactions without categories)
    orphans = cursor.execute("SELECT COUNT(*) FROM transactions WHERE macro_categoria IS NULL OR macro_categoria = '' OR sub_categoria IS NULL OR sub_categoria = ''").fetchone()[0]
    print(f"Orphan Transactions (No Category): {orphans}")

    # 4. Duplicates (basic check based on hash or exact matches)
    dupes = cursor.execute("SELECT COUNT(*) FROM (SELECT data, descricao_original, valor, COUNT(*) FROM transactions GROUP BY data, descricao_original, valor HAVING COUNT(*) > 1)").fetchone()[0]
    print(f"Potential Duplicate Transactions: {dupes}")

if __name__ == '__main__':
    run_health_check()
