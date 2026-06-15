import sqlite3
import requests
from app.api.deps import create_access_token
from database.repository import DatabaseManager

def run_bateria_3_5():
    conn = sqlite3.connect('database/fin_analytics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- Bateria 3.5: Consistência Wealth x Governança ---")

    # Wealth Total Positions
    wealth_positions = cursor.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
    
    # Wealth Total Dividends
    wealth_dividends = cursor.execute("SELECT COUNT(*) FROM dividends").fetchone()[0]

    # API Admin (Governance)
    token = create_access_token({'sub': 'admin', 'role': 'ADMIN'})
    headers = {'Authorization': f'Bearer {token}'}

    try:
        gov_pos = requests.get('http://localhost:8000/api/v1/governance/positions?limit=1', headers=headers).json().get('total', 0)
        gov_div = requests.get('http://localhost:8000/api/v1/governance/dividends?limit=1', headers=headers).json().get('total', 0)
    except Exception as e:
        print(f"API Error: {e}")
        return

    print(f"Posições: Wealth = {wealth_positions} | Governança = {gov_pos}")
    print(f"Dividendos: Wealth = {wealth_dividends} | Governança = {gov_div}")

    if wealth_positions == gov_pos and wealth_dividends == gov_div:
        print("RESULTADO: Sincronia 100% perfeita.")
    else:
        print("RESULTADO: DIVERGÊNCIA DETECTADA!")

if __name__ == '__main__':
    run_bateria_3_5()
