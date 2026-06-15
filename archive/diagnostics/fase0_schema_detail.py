"""
FASE 0 COMPLEMENTAR — Inventário detalhado do banco
Gera governance_inventory_raw.txt com:
- Colunas de cada tabela
- Foreign Keys
- Índices
- Views
- Triggers
"""
import sqlite3
import json
import os

DB_PATH = os.path.join("database", "fin_analytics.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

output = []

# 1. Tabelas
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
).fetchall()
table_names = [t[0] for t in tables]

for tname in table_names:
    output.append(f"\n{'='*60}")
    output.append(f"TABLE: {tname}")
    output.append('='*60)

    # Contagem
    count = cursor.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
    output.append(f"  rows: {count}")

    # Colunas
    cols = cursor.execute(f"PRAGMA table_info([{tname}])").fetchall()
    output.append("  columns:")
    for col in cols:
        cid, name, ctype, notnull, dflt, pk = col
        pk_str = " [PK]" if pk else ""
        nn_str = " NOT NULL" if notnull else ""
        df_str = f" DEFAULT={dflt}" if dflt is not None else ""
        output.append(f"    {name} {ctype}{pk_str}{nn_str}{df_str}")

    # Foreign Keys
    fks = cursor.execute(f"PRAGMA foreign_key_list([{tname}])").fetchall()
    if fks:
        output.append("  foreign_keys:")
        for fk in fks:
            fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
            output.append(f"    {from_col} -> {ref_table}({to_col}) ON DELETE {on_delete}")

    # Índices
    idxs = cursor.execute(f"PRAGMA index_list([{tname}])").fetchall()
    if idxs:
        output.append("  indexes:")
        for idx in idxs:
            idx_seq, idx_name, unique, origin, partial = idx
            u_str = " UNIQUE" if unique else ""
            output.append(f"    {idx_name}{u_str}")

# 2. Views
views = cursor.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name"
).fetchall()
output.append(f"\n{'='*60}")
output.append("VIEWS")
output.append('='*60)
for vname, vsql in views:
    output.append(f"  {vname}")
    if vsql:
        for line in vsql.split('\n'):
            output.append(f"    {line}")

# 3. Triggers
triggers = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
).fetchall()
output.append(f"\n{'='*60}")
output.append("TRIGGERS")
output.append('='*60)
if triggers:
    for t in triggers:
        output.append(f"  {t[0]}")
else:
    output.append("  (none)")

conn.close()

with open("scripts/fase0_schema_raw.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: scripts/fase0_schema_raw.txt")
print("\n".join(output))
