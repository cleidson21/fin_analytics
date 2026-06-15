import os

# 1. learning.py
with open('app/api/routes/learning.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.governance_repository import GovernanceRepository', 'from app.api.services.governance_service import GovernanceService')
c = c.replace('return GovernanceRepository()', 'return GovernanceService()')
c = c.replace('db: GovernanceRepository', 'db: GovernanceService')
with open('app/api/routes/learning.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 2. prompts.py
with open('app/api/routes/prompts.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.governance_repository import GovernanceRepository', 'from app.api.services.governance_service import GovernanceService')
c = c.replace('repository = GovernanceRepository()', 'service = GovernanceService()')
c = c.replace('repository.', 'service.')
with open('app/api/routes/prompts.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 3. audit.py
with open('app/api/routes/audit.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.governance_repository import GovernanceRepository', 'from app.api.services.governance_service import GovernanceService')
c = c.replace('repository = GovernanceRepository()', 'service = GovernanceService()')
c = c.replace('repository.', 'service.')
with open('app/api/routes/audit.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 4. database_admin.py
with open('app/api/routes/database_admin.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.financial_repository import FinancialRepository\nfrom database.governance_repository import GovernanceRepository', 
              'from app.api.services.financial_service import FinancialService\nfrom app.api.services.governance_service import GovernanceService')
c = c.replace('fin_repo = FinancialRepository()\ngov_repo = GovernanceRepository()',
              'fin_service = FinancialService()\ngov_service = GovernanceService()')

c = c.replace('''    with fin_repo._get_connection() as conn:
        cursor = conn.cursor()
        summary['total_transactions'] = cursor.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        summary['total_positions'] = cursor.execute('SELECT COUNT(*) FROM positions').fetchone()[0]
        summary['total_dividends'] = cursor.execute('SELECT COUNT(*) FROM dividends').fetchone()[0]
        summary['total_evolutions'] = cursor.execute('SELECT COUNT(*) FROM portfolio_evolution').fetchone()[0]''',
'''    fin_metrics = fin_service.get_admin_metrics()
    summary.update(fin_metrics)''')

c = c.replace('''    with gov_repo._get_connection() as conn:
        cursor = conn.cursor()
        summary['total_import_runs'] = cursor.execute('SELECT COUNT(*) FROM import_runs').fetchone()[0]
        summary['runs_confirmed'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status = 'CONFIRMED'").fetchone()[0]
        summary['runs_pending'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION')").fetchone()[0]''',
'''    gov_metrics = gov_service.get_admin_metrics()
    summary.update(gov_metrics)''')

c = c.replace('''    fin_tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution']
    gov_tables = ['import_runs', 'staging_imports', 'staging_positions', 'staging_dividends', 'staging_portfolio_evolution', 'governance_rules', 'governance_prompt_versions']
    
    results = []
    with fin_repo._get_connection() as conn:
        cursor = conn.cursor()
        for t in fin_tables:
            try:
                count = cursor.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                results.append({'table_name': t, 'row_count': count, 'status': 'OK' if count < 1000000 else 'WARNING'})
            except:
                results.append({'table_name': t, 'row_count': 0, 'status': 'ERROR'})
                
    with gov_repo._get_connection() as conn:
        cursor = conn.cursor()
        for t in gov_tables:
            try:
                count = cursor.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                results.append({'table_name': t, 'row_count': count, 'status': 'OK' if count < 1000000 else 'WARNING'})
            except:
                results.append({'table_name': t, 'row_count': 0, 'status': 'ERROR'})''',
'''    results = fin_service.get_table_counts() + gov_service.get_table_counts()''')

c = c.replace('''    integrity = {'orphan_runs': 0, 'pending_staging': 0, 'duplicate_transactions_suspects': 0}
    
    with fin_repo._get_connection() as conn:
        cursor = conn.cursor()
        # orphan runs are now checked by soft-links, but since we decoupled DBs, we can just check if import_run_id is not null
        # however, we cannot check against import_runs table anymore. 
        # For simplicity of migration and keeping payload, we set orphan_runs to 0 or fetch from both.
        # Actually, let's fetch unique import_run_id from transactions and check against governance.db
        run_ids = cursor.execute('SELECT DISTINCT import_run_id FROM transactions WHERE import_run_id IS NOT NULL').fetchall()
        fin_run_ids = set([r[0] for r in run_ids])
        
        integrity['duplicate_transactions_suspects'] = cursor.execute('SELECT COUNT(*) FROM (SELECT data, descricao_original, valor_cents, COUNT(*) as c FROM transactions GROUP BY data, descricao_original, valor_cents HAVING c > 1)').fetchone()[0]

    with gov_repo._get_connection() as conn:
        cursor = conn.cursor()
        integrity['pending_staging'] = cursor.execute("SELECT COUNT(*) FROM staging_imports WHERE status = 'PENDING'").fetchone()[0]
        gov_run_ids = set([r[0] for r in cursor.execute('SELECT id FROM import_runs').fetchall()])
        
    orphans = fin_run_ids - gov_run_ids
    integrity['orphan_runs'] = len(orphans)''',
'''    integrity = {'orphan_runs': 0, 'pending_staging': 0, 'duplicate_transactions_suspects': 0}
    
    fin_int = fin_service.get_integrity_metrics()
    gov_int = gov_service.get_integrity_metrics()
    
    integrity['duplicate_transactions_suspects'] = fin_int.get('duplicate_transactions_suspects', 0)
    integrity['pending_staging'] = gov_int.get('pending_staging', 0)
    
    orphans = fin_int.get('fin_run_ids', set()) - gov_int.get('gov_run_ids', set())
    integrity['orphan_runs'] = len(orphans)''')

c = c.replace('fin_repo.db_path', 'fin_service.get_database_path()')
c = c.replace('gov_repo.db_path', 'gov_service.get_database_path()')
c = c.replace('fin_repo.vacuum_database()', 'fin_service.vacuum_database()')
c = c.replace('''    with gov_repo._get_connection() as conn:
        conn.execute("VACUUM")''', '    gov_service.vacuum_database()')
c = c.replace('fin_repo.analyze_database()', 'fin_service.analyze_database()')
c = c.replace('''    with gov_repo._get_connection() as conn:
        conn.execute("ANALYZE")''', '    gov_service.analyze_database()')

with open('app/api/routes/database_admin.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 5. governance.py
with open('app/api/routes/governance.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('from database.financial_repository import FinancialRepository\nfrom database.governance_repository import GovernanceRepository', 
              'from app.api.services.import_service import ImportService')
c = c.replace('fin_repo = FinancialRepository()\ngov_repo = GovernanceRepository()',
              'import_service = ImportService()')

c = c.replace('fin_repo.', 'import_service.')
c = c.replace('gov_repo.', 'import_service.')

with open('app/api/routes/governance.py', 'w', encoding='utf-8') as f:
    f.write(c)
