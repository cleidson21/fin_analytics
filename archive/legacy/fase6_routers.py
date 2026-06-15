import os

# 1. accounts.py
with open('app/api/routes/accounts.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.queries import FinancialQueries', 'from app.api.services.financial_service import FinancialService')
c = c.replace('queries = FinancialQueries()', 'service = FinancialService()')
c = c.replace('queries.get_accounts_summary()', 'service.get_accounts_summary()')
with open('app/api/routes/accounts.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 2. catalog.py
with open('app/api/routes/catalog.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.queries import FinancialQueries', 'from app.api.services.financial_service import FinancialService')
c = c.replace('queries = FinancialQueries()', 'service = FinancialService()')
c = c.replace('queries.get_account_catalog()', 'service.get_account_catalog()')
with open('app/api/routes/catalog.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 3. dashboard.py
with open('app/api/routes/dashboard.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.queries import FinancialQueries', 'from app.api.services.financial_service import FinancialService')
c = c.replace('queries = FinancialQueries()', 'service = FinancialService()')
c = c.replace('queries.', 'service.')
with open('app/api/routes/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 4. transactions.py
with open('app/api/routes/transactions.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.queries import FinancialQueries', 'from app.api.services.financial_service import FinancialService')
c = c.replace('queries = FinancialQueries()', 'service = FinancialService()')
c = c.replace('queries.', 'service.')
with open('app/api/routes/transactions.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 5. auth.py
with open('app/api/routes/auth.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.repository import DatabaseManager', 'from app.api.services.auth_service import AuthService')
c = c.replace('db: DatabaseManager', 'service: AuthService')
c = c.replace('db.get_user_by_username', 'service.get_user_by_username')
c = c.replace('db.create_user', 'service.create_user')
with open('app/api/routes/auth.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 6. deps.py (auth dependency)
with open('app/api/deps.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from database.repository import DatabaseManager', 'from app.api.services.auth_service import AuthService')
c = c.replace('def get_db():', 'def get_auth_service():')
c = c.replace('return DatabaseManager()', 'return AuthService()')
c = c.replace('db: DatabaseManager = Depends(get_db)', 'service: AuthService = Depends(get_auth_service)')
c = c.replace('db.get_user_by_username', 'service.get_user_by_username')
with open('app/api/deps.py', 'w', encoding='utf-8') as f:
    f.write(c)

# Update auth.py to use get_auth_service instead of get_db
with open('app/api/routes/auth.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('Depends(get_db)', 'Depends(get_auth_service)')
c = c.replace('from app.api.deps import get_db', 'from app.api.deps import get_auth_service')
with open('app/api/routes/auth.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Routers updated.')
