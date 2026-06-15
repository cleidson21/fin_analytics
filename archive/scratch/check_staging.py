from database.repository import DatabaseManager
import sys

db = DatabaseManager('database/fin_analytics.db')
run_id = '3ff84951a4fb435ea17669841e95db80'

run = db.get_import_run(run_id)
print('Run:', run)

with db.get_connection() as conn:
    print('Tables with staging data:')
    for t in ['staging_transactions', 'staging_dividends', 'staging_positions', 'staging_portfolio_evolution']:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE import_run_id = ?", (run_id,)).fetchone()[0]
            print(f'{t}: {count}')
        except Exception as e:
            print(f'{t}: Error - {e}')
