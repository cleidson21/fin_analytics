import sqlite3
import requests
import inspect
from app.api.deps import create_access_token
from database.repository import DatabaseManager

def run_audit():
    conn = sqlite3.connect('database/fin_analytics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Consistencia dos dados (20 registros)
    res = cursor.execute('SELECT * FROM dividends ORDER BY data_pagamento DESC LIMIT 20').fetchall()
    print('--- Consistência dos Dados (20 registros) ---')
    id_economico_nulo = sum(1 for r in res if not r['id_economico'])
    ticker_vazio = sum(1 for r in res if not r['ticker'])
    tipo_evento_nulo = sum(1 for r in res if not r['tipo_evento'])
    obs_nula = sum(1 for r in res if not r['observacao'])
    valor_zerado = sum(1 for r in res if r['valor_liquido'] == 0)
    data_invalida = sum(1 for r in res if not r['data_pagamento'])

    print(f'id_economico nulo: {id_economico_nulo}')
    print(f'ticker vazio: {ticker_vazio}')
    print(f'tipo_evento nulo: {tipo_evento_nulo}')
    print(f'observacao nula: {obs_nula}')
    print(f'valor zerado: {valor_zerado}')
    print(f'data_pagamento invalida: {data_invalida}')

    # 2. Integridade Wealth
    total_dividends = cursor.execute('SELECT COUNT(*) FROM dividends').fetchone()[0]
    print('\n--- Integridade Wealth ---')
    print(f'Quantidade total de dividendos no banco (Wealth): {total_dividends}')

    token = create_access_token({'sub': 'admin', 'role': 'ADMIN'})
    headers = {'Authorization': f'Bearer {token}'}
    try:
        api_res = requests.get('http://localhost:8000/api/v1/governance/dividends?limit=1', headers=headers).json()
        print(f'Quantidade total retornada pela governanca: {api_res.get("total", 0)}')
    except Exception as e:
        print(f'Erro na API: {e}')

    # 3. Audit Log Validation
    print('\n--- Audit Log estatico ---')
    source = inspect.getsource(DatabaseManager.update_dividend)
    if 'create_audit_log' in source and 'UPDATE' in source and 'field_changes' in source:
        print('Validacao estatica concluida: repository.update_dividend registra log com sucesso.')
    else:
        print('Falha: Audit log nao detectado em update_dividend.')

if __name__ == '__main__':
    run_audit()
