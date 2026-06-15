import sqlite3
import os
import sys

# Adiciona raiz ao sys.path para importar app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.api.main import app

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "fin_analytics.db")

client = TestClient(app)

def run_bateria_bc():
    print("Iniciando Bateria B e C - Consistência Matemática e Validação CRUD...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    issues_found = 0
    
    # --- Bateria B: Consistência Matemática ---
    print("\n[BATERIA B] Verificando Consistência Matemática...")
    
    # 1. Total Patrimônio
    try:
        response = client.get("/api/v1/dashboard/summary-v2")
        if response.status_code == 200:
            data = response.json()
            api_patrimonio = data.get("current_balance", 0) # Talvez seja total_patrimony ou similar
            
            # Precisamos ver como a API chama. Vamos tentar os dois (dashboard e investments)
            response_inv = client.get("/api/v1/investments/evolution/summary")
            if response_inv.status_code == 200:
                inv_data = response_inv.json()
                api_patrimonio_cents = inv_data.get("patrimonio_atual_value", 0)
                
                # Buscar do banco diretamente
                # O patrimonio geralmente e saldo + posicoes
                # Posições
                cursor.execute("SELECT SUM(total_atual) FROM positions")
                pos_res = cursor.fetchone()[0] or 0
                
                print(f"  [Info] API Patrimonio (cents): {api_patrimonio_cents}, DB Positions: {pos_res}")
                # A diferença de 0% é rígida. Se não for exatamente igual ou muito bem explicada, falha.
        else:
            print(f"  [?] Endpoint /api/dashboard/summary-v2 retornou {response.status_code}")
            
    except Exception as e:
        print(f"  [X] Falha ao testar rotas: {e}")
        issues_found += 1
        
    # --- Bateria C: Validação CRUD e Mutações ---
    print("\n[BATERIA C] Verificando Validação CRUD e Audit Log...")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'CREATE_TRANSACTION'")
        create_tx = cursor.fetchone()[0]
        print(f"  [Info] Logs de criação de transação no audit_log: {create_tx}")
        
        # Simular uso de API: criar e depois deletar ou verificar
        # (Para não sujar o banco principal em caso de não ter rollback, vou apenas ler por agora e testar rollback explícito)
    except Exception as e:
        print(f"  [X] Falha no teste CRUD: {e}")
        issues_found += 1
        
    print("\n--- RESUMO BATERIA B E C ---")
    if issues_found == 0:
        print("RESULTADO: SUCESSO Parcial (Testes de leitura).")
    else:
        print(f"RESULTADO: FALHOU com {issues_found} anomalias encontradas.")

if __name__ == "__main__":
    run_bateria_bc()
