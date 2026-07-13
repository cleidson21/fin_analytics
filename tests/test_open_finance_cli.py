import os
import sys
import json
import sqlite3
import tempfile
from unittest import mock
import contextlib
import io

from backend.domains.investments.open_finance_cli import main

def setup_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    
    conn.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT);
        CREATE TABLE assets (id TEXT PRIMARY KEY, ticker TEXT NOT NULL UNIQUE);
        
        CREATE TABLE broker_notes (id TEXT PRIMARY KEY);
        
        CREATE TABLE trades (
            id TEXT PRIMARY KEY,
            broker_note_id TEXT,
            asset_id TEXT NOT NULL REFERENCES assets(id),
            account_id TEXT NOT NULL REFERENCES accounts(id),
            type TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price INTEGER NOT NULL,
            gross_value INTEGER,
            fees_allocated INTEGER NOT NULL DEFAULT 0,
            net_value INTEGER,
            source TEXT NOT NULL,
            run_id TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );
        
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
    conn.execute("INSERT INTO assets (id, ticker) VALUES ('asset-001', 'PETR4')")
    conn.commit()
    conn.close()

def run_cli_with_file(db_path, payload_dict, expect_exit_code=0):
    os.environ["TEST_DB_URL"] = f"sqlite:///{os.path.abspath(db_path)}"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(payload_dict, f)
        temp_path = f.name
        
    def mock_exit(code):
        raise Exception(f"Exit {code}")
        
    f_out = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(f_out):
            with mock.patch('sys.exit', side_effect=mock_exit):
                try:
                    main(["--file", temp_path])
                except Exception as e:
                    if str(e) == "Exit 1":
                        exit_code = 1
                    else:
                        raise e
    finally:
        os.remove(temp_path)
        
    output = f_out.getvalue()
    if exit_code != expect_exit_code:
        print(f"Failed. Expected exit {expect_exit_code}, got {exit_code}")
        print("CLI Output:\n", output)
        assert False
    return output

def run_tests():
    db_path = "test_of_cli.db"
    
    # 1. Payload somente posições
    setup_db(db_path)
    payload_pos = {
        "positions": [{
            "reference_date": "2024-01-01",
            "ticker": "PETR4",
            "institution": "NUBANK",
            "quantity": 100,
            "unit_price": 30.50,
            "total_value": 3050.00
        }]
    }
    out = run_cli_with_file(db_path, payload_pos, expect_exit_code=0)
    assert "SUCESSO" in out
    
    # 2. Payload somente trades
    setup_db(db_path)
    payload_trades = {
        "trades": [{
            "trade_date": "2024-01-02",
            "ticker": "PETR4",
            "broker": "NUBANK",
            "operation_type": "BUY",
            "quantity": 50,
            "unit_price": 30.00,
            "total_value": 1500.00
        }]
    }
    out = run_cli_with_file(db_path, payload_trades, expect_exit_code=0)
    assert "SUCESSO" in out
    assert "Quantidade persistida (Upsert Banco): 1" in out

    # 3. Payload misto
    setup_db(db_path)
    payload_mixed = {
        "positions": payload_pos["positions"],
        "trades": payload_trades["trades"]
    }
    out = run_cli_with_file(db_path, payload_mixed, expect_exit_code=0)
    assert "SUCESSO" in out
    assert "Quantidade persistida (Upsert Banco): 2" in out

    # 4. Payload vazio
    setup_db(db_path)
    out = run_cli_with_file(db_path, {"positions": [], "trades": []}, expect_exit_code=0)
    assert "SUCESSO" in out
    assert "Quantidade persistida (Upsert Banco): 0" in out

    # 5. Erro de adapter (campos faltando) - Testa Fail Fast
    setup_db(db_path)
    payload_bad = {
        "trades": [{"ticker": "PETR4"}]
    }
    out = run_cli_with_file(db_path, payload_bad, expect_exit_code=1)
    assert "FALHA" in out
    assert "Missing required key" in out

    # 6. Erro de repository (Conta inexistente) -> Rollback
    setup_db(db_path)
    payload_bad_repo = {
        "trades": [{
            "trade_date": "2024-01-02",
            "ticker": "PETR4",
            "broker": "CORRETORA_FANTASMA",
            "operation_type": "BUY",
            "quantity": 50,
            "unit_price": 30.00,
            "total_value": 1500.00
        }]
    }
    out = run_cli_with_file(db_path, payload_bad_repo, expect_exit_code=1)
    assert "FALHA" in out
    assert "Account (Broker) not found" in out

    # 7. Rollback & Commit parcial
    # Testaremos enviando uma posição válida e um trade com corretora inválida.
    # O pipeline deve falhar e NADA deve ser persistido.
    setup_db(db_path)
    payload_partial = {
        "positions": payload_pos["positions"],
        "trades": payload_bad_repo["trades"]
    }
    out = run_cli_with_file(db_path, payload_partial, expect_exit_code=1)
    
    # Check DB to ensure rollback was atomic
    conn = sqlite3.connect(db_path)
    cnt = conn.execute("SELECT COUNT(*) FROM position_snapshots").fetchone()[0]
    conn.close()
    assert cnt == 0, "Rollback falhou! Posição foi persistida ignorando o erro do Trade."

    # 8. KeyboardInterrupt (simulação forçada via mock do repository)
    setup_db(db_path)
    with mock.patch('backend.domains.investments.repositories.trade_repository.TradeRepository.save_many', side_effect=KeyboardInterrupt):
        out = run_cli_with_file(db_path, payload_mixed, expect_exit_code=1)
        assert "KeyboardInterrupt" in out
        assert "FALHA" in out

    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ TODOS OS TESTES DA CLI DE OPEN FINANCE PASSARAM!")

if __name__ == "__main__":
    run_tests()
