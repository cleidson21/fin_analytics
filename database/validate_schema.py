import sqlite3

db = sqlite3.connect('database/fin_analytics_v3.db')
db.execute('PRAGMA foreign_keys=ON;')

# 1. Foreign key integrity check
fk_check = db.execute('PRAGMA foreign_key_check;').fetchall()
print('=== FOREIGN KEY CHECK ===')
if fk_check:
    for row in fk_check:
        print('  VIOLATION:', row)
else:
    print('  OK - zero violations')

# 2. Integrity check
ic = db.execute('PRAGMA integrity_check;').fetchall()
print('\n=== INTEGRITY CHECK ===')
for row in ic:
    print(' ', row[0])

# 3. New tables confirmation
new_tables = ['fixed_income_events', 'transaction_events', 'ai_prompt_versions']
print('\n=== NEW TABLES ===')
for t in new_tables:
    cols = db.execute('PRAGMA table_info(' + t + ');').fetchall()
    idxs = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='" + t + "';").fetchall()
    print('  ' + t + ': ' + str(len(cols)) + ' columns, ' + str(len(idxs)) + ' indexes')

# 4. ai_runs.prompt_version_id column check
print('\n=== ai_runs.prompt_version_id column ===')
cols = {c[1]: c for c in db.execute('PRAGMA table_info(ai_runs);').fetchall()}
if 'prompt_version_id' in cols:
    print('  OK - column exists')
else:
    print('  MISSING - column not found')

# 5. All indexes on new tables
print('\n=== INDEX DETAIL (new tables) ===')
for t in new_tables:
    idxs = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='" + t + "';").fetchall()
    for idx in idxs:
        print('  [' + t + '] ' + idx[0])

# 6. Total table count
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_schema%' ORDER BY name").fetchall()
print('\n=== TOTAL TABLES: ' + str(len(tables)) + ' ===')

db.close()
print('\nValidation complete.')
