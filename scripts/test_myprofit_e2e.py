import os
import sys
import httpx
from datetime import datetime

# Adicionar raiz no path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.reset_db import reset_database

API_BASE = "http://localhost:8000/api/v1"

def run_e2e():
    print("===================================")
    print("H1.4: Homologação E2E - MyProfit")
    print("===================================")
    
    # 1. Banco Limpo
    reset_database()
    
    # Fake CSV content for MyProfit Proventos
    csv_content = """Ativo,Recebido,Data pgto.,Cotas,Preço
MXRF11,"R$ 2,59",15/05/2026,"0,094","R$ 10,00"
HGLG11,"R$ 15,00",15/05/2026,"1,0","R$ 150,00"
"""
    
    with httpx.Client(base_url=API_BASE) as client:
        print("\n[Login] Autenticando admin...")
        login_resp = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        if login_resp.status_code != 200:
            print(f"Erro no Login: {login_resp.status_code} - {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Upload
        print("\n[Upload] Enviando CSV...")
        resp = client.post("/governance/imports/upload", data={
            "source_type": "MYPROFIT_PROVENTOS",
            "raw_text": csv_content
        }, headers=headers)
        
        if resp.status_code != 200:
            print(f"Erro no Upload: {resp.status_code} - {resp.text}")
            return
            
        data = resp.json()
        run_id = data["run_id"]
        print(f" -> Sucesso! run_id = {run_id}")
        
        # 3. Preview
        print("\n[Preview] Analisando staging...")
        staging_resp = client.get(f"/governance/imports/{run_id}/staging-items", headers=headers)
        if staging_resp.status_code == 200:
            print(f" -> Staging Items: {len(staging_resp.json()['items'])}")
        else:
            print(f"Erro no Staging: {staging_resp.status_code}")
            
        # 4. Confirmação
        print("\n[Confirmação] Processando para o Banco...")
        confirm_resp = client.post(f"/governance/imports/{run_id}/confirm", headers=headers)
        if confirm_resp.status_code == 200:
            print(f" -> Confirmado! Linhas processadas: {confirm_resp.json()['rows_processed']}")
        else:
            print(f"Erro na Confirmação: {confirm_resp.status_code} - {confirm_resp.text}")

        # 5. Verificação nas Telas (Dividendos)
        print("\n[Verificação] Checando Posições e Dividendos...")
        div_resp = client.get("/governance/dividends?limit=10", headers=headers)
        if div_resp.status_code == 200:
            divs = div_resp.json()["items"]
            print(f" -> Encontrados {len(divs)} dividendos salvos.")
            for d in divs:
                print(f"    - {d['ticker']}: {d.get('valor_bruto', d.get('valor', d.get('valor_total', '???')))}")
                
        # 6. Auditoria
        print("\n[Auditoria] Verificando log de auditoria...")
        audit_resp = client.get("/governance/audit", headers=headers)
        if audit_resp.status_code == 200:
            print(f" -> Auditoria retornou {len(audit_resp.json())} itens.")
            
        # 7. Rollback
        print("\n[Rollback] Executando Rollback do run_id...")
        rb_resp = client.post(f"/governance/imports/{run_id}/rollback", headers=headers)
        if rb_resp.status_code == 200:
            print(" -> Rollback com sucesso.")
        else:
            print(f"Erro no Rollback: {rb_resp.status_code}")
            
        # Verificar limpeza
        div_resp2 = client.get("/governance/dividends?limit=10", headers=headers)
        if div_resp2.status_code == 200 and len(div_resp2.json()["items"]) == 0:
            print(" -> Rollback confirmado (zero dividendos).")
        else:
            print(" -> Rollback falhou ou não limpou dividendos.")

if __name__ == "__main__":
    run_e2e()
