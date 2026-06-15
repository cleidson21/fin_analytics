import requests
import sqlite3
import json

def test_crud():
    # 1. Get an admin token
    from app.api.deps import create_access_token
    token = create_access_token({"sub": "admin", "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Check the database for a position
    conn = sqlite3.connect("database/fin_analytics.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, data_snapshot, classe_ativo, observacao FROM positions LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("Nenhuma posição no banco.")
        return

    ticker = row["ticker"]
    data_snapshot = row["data_snapshot"]
    old_classe = row["classe_ativo"]
    old_obs = row["observacao"]

    print(f"--- ANTES ---")
    print(f"Ticker: {ticker} | Snapshot: {data_snapshot}")
    print(f"Classe Atual: {old_classe}")
    print(f"Obs Atual: {old_obs}")

    # 3. Simulate Frontend Update Request
    payload = {
        "classe_ativo": "Classe Teste Automatizado",
        "observacao": "Obs Teste Automatizado"
    }
    print(f"\n--- ENVIANDO PUT PAYLOAD ---")
    print(json.dumps(payload, indent=2))

    url = f"http://localhost:8000/api/v1/governance/positions/{ticker}/{data_snapshot}"
    res = requests.put(url, headers=headers, json=payload)
    
    print(f"\n--- RESPOSTA API ---")
    print(f"Status Code: {res.status_code}")
    print(f"Body: {res.text}")

    # 4. Check Database After
    cursor.execute("SELECT classe_ativo, observacao FROM positions WHERE ticker = ? AND data_snapshot = ?", (ticker, data_snapshot))
    new_row = cursor.fetchone()
    print(f"\n--- DEPOIS ---")
    print(f"Classe Atualizada: {new_row['classe_ativo']}")
    print(f"Obs Atualizada: {new_row['observacao']}")

    # 5. Check Audit Log
    entity_id = f"{ticker}|{data_snapshot}"
    cursor.execute("SELECT action, changed_by, field_changes, created_at FROM audit_log WHERE entity_id = ? ORDER BY created_at DESC LIMIT 1", (entity_id,))
    audit = cursor.fetchone()
    if audit:
        print(f"\n--- AUDIT LOG ---")
        print(f"Action: {audit['action']}")
        print(f"Usuário: {audit['changed_by']}")
        print(f"Mudanças: {audit['field_changes']}")
        print(f"Timestamp: {audit['created_at']}")
    else:
        print("\n--- ERRO: AUDIT LOG NÃO ENCONTRADO ---")

    # 6. Revert (Clean up)
    requests.put(url, headers=headers, json={"classe_ativo": old_classe, "observacao": old_obs})
    print("\n--- TESTE CONCLUÍDO (VALORES REVERTIDOS) ---")

if __name__ == "__main__":
    test_crud()
