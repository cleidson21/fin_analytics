import sqlite3
db = sqlite3.connect('database/fin_analytics.db')
db.execute('PRAGMA foreign_keys=OFF')  # off to test CHECK constraints independently

results = []

# 1. benchmark_prices.value type = REAL
for col in db.execute('PRAGMA table_info(benchmark_prices)').fetchall():
    if col[1] == 'value':
        results.append(('benchmark_prices.value is REAL', col[2] == 'REAL', col[2]))

# 2. fixed_income_events: CORRECTION accepted by CHECK
try:
    db.execute(
        'INSERT INTO fixed_income_events '
        '(id, asset_id, account_id, event_type, event_date, gross_amount, source) '
        "VALUES ('x1', 'a', 'b', 'CORRECTION', '2026-01-01', 100, 'MANUAL')"
    )
    results.append(('fixed_income_events: CORRECTION accepted', True, ''))
    db.execute("DELETE FROM fixed_income_events WHERE id='x1'")
except Exception as e:
    results.append(('fixed_income_events: CORRECTION accepted', False, str(e)))

# 3. fixed_income_events: original APPLICATION still accepted
try:
    db.execute(
        'INSERT INTO fixed_income_events '
        '(id, asset_id, account_id, event_type, event_date, gross_amount, source) '
        "VALUES ('x2', 'a', 'b', 'APPLICATION', '2026-01-01', 100, 'MANUAL')"
    )
    results.append(('fixed_income_events: APPLICATION still accepted', True, ''))
    db.execute("DELETE FROM fixed_income_events WHERE id='x2'")
except Exception as e:
    results.append(('fixed_income_events: APPLICATION still accepted', False, str(e)))

# 4. fixed_income_events: corrects_event_id column exists
cols = [c[1] for c in db.execute('PRAGMA table_info(fixed_income_events)').fetchall()]
results.append(('fixed_income_events.corrects_event_id exists', 'corrects_event_id' in cols, ''))

# 5. installments: CANCELLED accepted
try:
    db.execute(
        'INSERT INTO installments (id, installment_plan_id, installment_number, amount, expected_date, status) '
        "VALUES ('i1', 'plan_x', 1, 500, '2026-01-01', 'CANCELLED')"
    )
    results.append(('installments: CANCELLED accepted', True, ''))
    db.execute("DELETE FROM installments WHERE id='i1'")
except Exception as e:
    results.append(('installments: CANCELLED accepted', False, str(e)))

# 6. installments: PENDING still accepted
try:
    db.execute(
        'INSERT INTO installments (id, installment_plan_id, installment_number, amount, expected_date, status) '
        "VALUES ('i2', 'plan_x', 1, 500, '2026-01-01', 'PENDING')"
    )
    results.append(('installments: PENDING still accepted', True, ''))
    db.execute("DELETE FROM installments WHERE id='i2'")
except Exception as e:
    results.append(('installments: PENDING still accepted', False, str(e)))

# 7. installments: cancelled_at column
cols = [c[1] for c in db.execute('PRAGMA table_info(installments)').fetchall()]
results.append(('installments.cancelled_at exists', 'cancelled_at' in cols, ''))

# 8. installment_plans columns
cols = [c[1] for c in db.execute('PRAGMA table_info(installment_plans)').fetchall()]
for field in ('status', 'cancelled_at', 'renegotiated_to_plan_id'):
    results.append(('installment_plans.' + field + ' exists', field in cols, ''))

# 9. installment_plans: CANCELLED status accepted
try:
    db.execute(
        'INSERT INTO installment_plans '
        '(id, credit_card_id, description, purchase_date, total_amount, total_installments, status) '
        "VALUES ('pl1', 'card_x', 'Test', '2026-01-01', 1000, 3, 'CANCELLED')"
    )
    results.append(('installment_plans: CANCELLED accepted', True, ''))
    db.execute("DELETE FROM installment_plans WHERE id='pl1'")
except Exception as e:
    results.append(('installment_plans: CANCELLED accepted', False, str(e)))

# 10. benchmark_prices: value accepts REAL (float)
try:
    db.execute(
        'INSERT INTO benchmark_prices (ticker, date, value, source) '
        "VALUES ('CDI', '2026-01-01', 0.000467, 'BCB_SGS')"
    )
    val = db.execute("SELECT value FROM benchmark_prices WHERE ticker='CDI'").fetchone()[0]
    is_real = isinstance(val, float)
    results.append(('benchmark_prices.value stores REAL (float)', is_real, str(val)))
    db.execute("DELETE FROM benchmark_prices WHERE ticker='CDI'")
except Exception as e:
    results.append(('benchmark_prices.value stores REAL (float)', False, str(e)))

db.commit()
db.close()

print('\n=== MIGRATION 012 — FULL VALIDATION ===')
all_ok = True
for label, ok, detail in results:
    marker = 'OK  ' if ok else 'FAIL'
    if not ok:
        all_ok = False
    suffix = (' -> ' + str(detail)) if detail else ''
    print('  [' + marker + '] ' + label + suffix)

print()
print('RESULT: ' + ('ALL CHECKS PASSED — BANK READY TO FREEZE' if all_ok else 'SOME CHECKS FAILED'))
