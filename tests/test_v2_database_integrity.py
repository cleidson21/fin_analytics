import sqlite3
import pytest
import os
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'fin_analytics_v2.db')

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.rollback()
    conn.close()

def test_cascade_delete_import_runs(db_conn):
    cursor = db_conn.cursor()
    
    # 1. Create a dummy import_run
    run_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO import_runs (id, source_type) VALUES (?, ?)", (run_id, 'PIERRE'))
    
    # 2. Create child records
    cursor.execute("""
        INSERT INTO raw_events (id, import_run_id, source, event_type, semantic_id)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), run_id, 'PIERRE', 'TRANSACTION', 'SEM_123'))
    
    cursor.execute("""
        INSERT INTO positions (ticker, data_snapshot, source, quantidade, preco_medio, total_investido, preco_atual, total_atual, ganho, import_run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('AAPL', '2026-06-15', 'PIERRE', 10, 100, 1000, 150, 1500, 500, run_id))
    
    db_conn.commit()
    
    # Verify records exist
    assert cursor.execute("SELECT COUNT(*) FROM raw_events WHERE import_run_id = ?", (run_id,)).fetchone()[0] == 1
    assert cursor.execute("SELECT COUNT(*) FROM positions WHERE import_run_id = ?", (run_id,)).fetchone()[0] == 1
    
    # 3. Delete import_run
    cursor.execute("DELETE FROM import_runs WHERE id = ?", (run_id,))
    db_conn.commit()
    
    # 4. Verify cascade deletion
    assert cursor.execute("SELECT COUNT(*) FROM raw_events WHERE import_run_id = ?", (run_id,)).fetchone()[0] == 0
    assert cursor.execute("SELECT COUNT(*) FROM positions WHERE import_run_id = ?", (run_id,)).fetchone()[0] == 0


def test_unique_constraints(db_conn):
    cursor = db_conn.cursor()
    run_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO import_runs (id) VALUES (?)", (run_id,))
    
    # Test raw_events.semantic_id
    cursor.execute("""
        INSERT INTO raw_events (id, import_run_id, source, event_type, semantic_id)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), run_id, 'SRC', 'TX', 'UNIQUE_1'))
    
    with pytest.raises(sqlite3.IntegrityError) as exc:
        cursor.execute("""
            INSERT INTO raw_events (id, import_run_id, source, event_type, semantic_id)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), run_id, 'SRC', 'TX', 'UNIQUE_1'))
    assert "UNIQUE constraint failed" in str(exc.value)

    # Test portfolio_evolution.reference_month
    cursor.execute("""
        INSERT INTO portfolio_evolution (reference_month, import_run_id)
        VALUES (?, ?)
    """, ('2026-06-01', run_id))
    
    with pytest.raises(sqlite3.IntegrityError) as exc:
        cursor.execute("""
            INSERT INTO portfolio_evolution (reference_month, import_run_id)
            VALUES (?, ?)
        """, ('2026-06-01', run_id))
    assert "UNIQUE constraint failed" in str(exc.value)

def test_foreign_keys_category_id(db_conn):
    cursor = db_conn.cursor()
    run_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO import_runs (id) VALUES (?)", (run_id,))
    
    # Insert category
    cat_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO categories (id, name, category_type) VALUES (?, ?, ?)", (cat_id, 'Alimentação', 'OUT'))
    
    # Insert valid transaction
    cursor.execute("""
        INSERT INTO transactions (id_economico, source, import_run_id, data, descricao_original, descricao_normalizada, valor, subnatureza, natureza, perfil, category_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('T1', 'SRC', run_id, '2026-06-15', 'IFOOD', 'IFOOD', 50, 'IND', 'NAT', 'PER', cat_id))
    
    # Try inserting with invalid category_id
    with pytest.raises(sqlite3.IntegrityError) as exc:
        cursor.execute("""
            INSERT INTO transactions (id_economico, source, import_run_id, data, descricao_original, descricao_normalizada, valor, subnatureza, natureza, perfil, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('T2', 'SRC', run_id, '2026-06-15', 'IFOOD', 'IFOOD', 50, 'IND', 'NAT', 'PER', 'FAKE_CAT_ID'))
    assert "FOREIGN KEY constraint failed" in str(exc.value)
