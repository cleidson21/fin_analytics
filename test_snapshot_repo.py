import sqlite3
import os
import sys
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from backend.domains.investments.dto import PositionSnapshot, AssetTypeEnum
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver

def setup_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    
    conn.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT);
        CREATE TABLE assets (id TEXT PRIMARY KEY, ticker TEXT NOT NULL UNIQUE);
        CREATE TABLE position_snapshots (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(id),
            asset_id TEXT NOT NULL REFERENCES assets(id),
            reference_date TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price INTEGER,
            total_value INTEGER,
            source_system TEXT NOT NULL,
            metadata TEXT,
            run_id TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            UNIQUE(account_id, asset_id, reference_date)
        );
    """)
    conn.execute("INSERT INTO accounts (id, name) VALUES ('acc1', 'NUBANK')")
    conn.execute("INSERT INTO accounts (id, name) VALUES ('acc2', 'XP INVESTIMENTOS')")
    conn.execute("INSERT INTO assets (id, ticker) VALUES ('asset-001', 'PETR4')")
    conn.execute("INSERT INTO assets (id, ticker) VALUES ('asset-002', 'VALE3')")
    conn.commit()
    conn.close()

def run_tests():
    db_path = "test_snapshot_repo.db"
    setup_db(db_path)
    
    engine = create_engine(f"sqlite:///{os.path.abspath(db_path)}")
    repo = SnapshotRepository()

    # Helpers
    def make_snapshot(h, ticker, inst, qty, p=None, t=None):
        return PositionSnapshot(
            source_system="OPEN_FINANCE",
            reference_date=date(2024, 1, 1),
            ticker=ticker,
            asset_type=AssetTypeEnum.STOCK,
            institution=inst,
            quantity=Decimal(str(qty)),
            unit_price=Decimal(str(p)) if p else None,
            total_value=Decimal(str(t)) if t else None,
            snapshot_hash=h
        )

    with Session(engine) as session:
        session.begin()
        
        # 1. Snapshot novo
        snap1 = make_snapshot("h1", "PETR4", "NUBANK", 100, 30.50, 3050.00)
        repo.save(session, snap1)
        
        # 2. Snapshot duplicado (Upsert - Atualização)
        snap1_update = make_snapshot("h1", "PETR4", "NUBANK", 150, 30.00, 4500.00)
        repo.save(session, snap1_update)
        
        # 3. Account inexistente
        snap_bad_acc = make_snapshot("h2", "PETR4", "CORRETORA_FANTASMA", 100)
        try:
            repo.save(session, snap_bad_acc)
            print("ERROR: Account inexistente passou!")
            sys.exit(1)
        except ValueError as e:
            assert "Account (Broker) not found" in str(e)

        # 4. Asset inexistente
        snap_bad_asset = make_snapshot("h3", "TICKER_FALSO", "NUBANK", 100)
        try:
            repo.save(session, snap_bad_asset)
            print("ERROR: Asset inexistente passou!")
            sys.exit(1)
        except ValueError as e:
            assert "Asset not found" in str(e)
            
        # 5. save_many()
        snap2 = make_snapshot("h4", "VALE3", "XP INVESTIMENTOS", 50, 60.00, 3000.00)
        snap3 = make_snapshot("h5", "PETR4", "XP INVESTIMENTOS", 10, 30.00, 300.00)
        count = repo.save_many(session, [snap2, snap3])
        assert count == 2
        
        session.commit()
        
    # Check results
    with Session(engine) as session:
        rows = session.execute(text("SELECT id, quantity, total_value FROM position_snapshots ORDER BY id")).fetchall()
        assert len(rows) == 3
        # h1 should be updated to 150 qty, 4500.00 (450000 cents)
        assert rows[0][0] == 'h1'
        assert rows[0][1] == 150.0
        assert rows[0][2] == 450000
        
    # 6. Rollback test
    with Session(engine) as session:
        session.begin()
        snap4 = make_snapshot("h6", "VALE3", "NUBANK", 200)
        repo.save(session, snap4)
        session.rollback()
        
    with Session(engine) as session:
        rows = session.execute(text("SELECT id FROM position_snapshots WHERE id='h6'")).fetchall()
        assert len(rows) == 0

    engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ TODOS OS TESTES PASSARAM!")

if __name__ == "__main__":
    run_tests()
