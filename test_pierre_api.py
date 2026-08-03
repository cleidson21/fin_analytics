import asyncio
import os
from dotenv import load_dotenv

# Load from root .env
load_dotenv(dotenv_path=".env")

from backend.domains.pierre.connector import PierreConnector

async def main():
    connector = PierreConnector()
    print("API Key loaded:", bool(os.getenv("PIERRE_API_KEY")))

    print("\n--- Caso 1: Sem parâmetros ---")
    try:
        res1 = await connector.get_transactions()
        print(f"Sucesso: {res1.get('success')}, Total Registros: {len(res1.get('data', []))}")
    except Exception as e:
        print("Erro Caso 1:", e)

    print("\n--- Caso 2: startDate (2026-07-01) ---")
    try:
        res2 = await connector.get_transactions(start_date="2026-07-01")
        print(f"Sucesso: {res2.get('success')}, Total Registros: {len(res2.get('data', []))}")
    except Exception as e:
        print("Erro Caso 2:", e)

    print("\n--- Caso 3: endDate (2026-07-31) ---")
    try:
        res3 = await connector.get_transactions(end_date="2026-07-31")
        print(f"Sucesso: {res3.get('success')}, Total Registros: {len(res3.get('data', []))}")
    except Exception as e:
        print("Erro Caso 3:", e)

    print("\n--- Caso 4: startDate + endDate ---")
    try:
        res4 = await connector.get_transactions(start_date="2026-07-01", end_date="2026-07-31")
        print(f"Sucesso: {res4.get('success')}, Total Registros: {len(res4.get('data', []))}")
    except Exception as e:
        print("Erro Caso 4:", e)

    print("\n--- Caso 5: clientMessage (usando connector via HTTP client direto) ---")
    try:
        res5 = await connector.client.get("/get-transactions", params={"clientMessage": "compras de supermercado"})
        print(f"Sucesso: {res5.get('success')}, Total Registros: {len(res5.get('data', []))}")
        if res5.get('data'):
            print("Exemplo desc:", res5['data'][0].get('description'))
    except Exception as e:
        print("Erro Caso 5:", e)

    print("\n--- Caso 6: format=raw ---")
    try:
        res6 = await connector.get_transactions(start_date="2026-07-01", format_type="raw")
        if res6.get('data'):
            print("Raw Keys:", list(res6['data'][0].keys())[:15])
    except Exception as e:
        print("Erro Caso 6:", e)

    print("\n--- Caso 7: format=structured ---")
    try:
        res7 = await connector.get_transactions(start_date="2026-07-01", format_type="structured")
        if res7.get('data'):
            print("Structured Keys:", list(res7['data'][0].keys())[:15])
    except Exception as e:
        print("Erro Caso 7:", e)

    print("\n--- Etapa 3: Payload Real (Caso 4) ---")
    try:
        if res4.get('data'):
            print("Payload Keys Completo:", res4['data'][0].keys())
            print("Valores de um registro extra:")
            for k, v in res4['data'][0].items():
                if k not in ['id', 'account_id', 'description', 'amount', 'date', 'status', 'type', 'category']:
                    print(f"  {k}: {type(v).__name__}")
    except Exception as e:
        print("Erro Payload:", e)

if __name__ == "__main__":
    asyncio.run(main())
