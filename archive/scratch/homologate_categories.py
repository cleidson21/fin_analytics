import sqlite3
import requests
from app.api.deps import create_access_token
from database.repository import DatabaseManager

def homologate():
    conn = sqlite3.connect('database/fin_analytics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get total categories
    query = "SELECT macro_categoria as categoria, COUNT(*) as quantidade_transacoes FROM transactions WHERE macro_categoria IS NOT NULL AND macro_categoria != '' GROUP BY macro_categoria ORDER BY quantidade_transacoes DESC"
    res = cursor.execute(query).fetchall()
    
    total_categories = len(res)
    single_tx_categories = sum(1 for r in res if r['quantidade_transacoes'] == 1)
    
    print(f'Total de Categorias: {total_categories}')
    print(f'Categorias com apenas 1 transação (Possível Duplicidade): {single_tx_categories}')
    print('Categorias candidatas a merge identificadas visualmente:')
    for r in res:
        if r['quantidade_transacoes'] == 1:
            print(f"  - {r['categoria']}")

    # Create dummy merge to test Audit Log
    # Using 'Livros' and 'Educação' if they exist, or just check logic statically.
    token = create_access_token({'sub': 'admin', 'role': 'ADMIN'})
    headers = {'Authorization': f'Bearer {token}'}

    print('\nTesting GET Categories API')
    api_res = requests.get('http://localhost:8000/api/v1/governance/categories?limit=10', headers=headers).json()
    print(f"Items returned: {len(api_res.get('items', []))} (limit 10)")
    
if __name__ == '__main__':
    homologate()
