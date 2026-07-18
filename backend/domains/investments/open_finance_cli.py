import sys
import os
import time
import json
import argparse
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from backend.domains.investments.adapters.open_finance_adapter import OpenFinanceAdapter
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.import_report import ImportReport, ImportError as ImpError

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def main(args_list=None):
    parser = argparse.ArgumentParser(description="Open Finance Ingestion CLI")
    parser.add_argument("--file", required=True, help="Path to the Open Finance JSON payload")
    
    # Allows passing args for testing
    args = parser.parse_args(args_list)

    file_path = args.file

    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)

    # Note: Em produção ou testes end-to-end reais a variável de ambiente DB_URL poderia ser usada, 
    # mas mantemos o padrão hardcoded estrito para respeitar a arquitetura do projeto.
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "fin_analytics.db")
    db_url = os.environ.get("TEST_DB_URL", f"sqlite:///{os.path.abspath(db_path)}")
    
    start_time_perf = time.perf_counter()
    
    report = ImportReport(
        source="OPEN_FINANCE",
        file_name=os.path.basename(file_path)
    )
    
    engine = create_engine(db_url)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
            
        if not isinstance(payload, dict):
            raise ValueError("Root payload must be a JSON object containing 'positions' and/or 'trades'")

        raw_positions = payload.get("positions", [])
        raw_trades = payload.get("trades", [])
        
        report.rows_read = len(raw_positions) + len(raw_trades)

        with Session(engine) as session:
            try:
                session.begin()
                
                adapter = OpenFinanceAdapter()
                
                # Parsing (Fail-Fast)
                snapshots = adapter.parse_positions(raw_positions) if raw_positions else []
                trades = adapter.parse_trades(raw_trades) if raw_trades else []
                
                report.rows_parsed = len(snapshots) + len(trades)
                report.rows_normalized = report.rows_parsed 
                
                # Persistence
                snapshot_repo = SnapshotRepository()
                trade_repo = TradeRepository()
                
                persisted_snapshots = snapshot_repo.save_many(session, snapshots) if snapshots else 0
                persisted_trades = trade_repo.save_many(session, trades) if trades else 0
                
                report.rows_persisted = persisted_snapshots + persisted_trades
                
                session.commit()
                report.success = True
                
            except KeyboardInterrupt:
                session.rollback()
                report.errors.append(ImpError(message="Operação cancelada pelo usuário (KeyboardInterrupt)"))
            except Exception as e:
                session.rollback()
                report.errors.append(ImpError(message=f"Erro no pipeline: {str(e)}"))
                
    except Exception as e:
        report.errors.append(ImpError(message=f"Erro ao ler/processar JSON: {str(e)}"))
    finally:
        engine.dispose()
        end_time_perf = time.perf_counter()
        report.elapsed_ms = int((end_time_perf - start_time_perf) * 1000)
        report.finished_at = datetime.now(timezone.utc)
        
        print("\n" + "="*50)
        print("RELATÓRIO DE IMPORTAÇÃO OPEN FINANCE")
        print("="*50)
        print(f"Arquivo: {report.file_name}")
        print(f"Tempo da execução: {report.elapsed_ms}ms")
        print(f"Quantidade lida no JSON: {report.rows_read}")
        print(f"Quantidade validada e convertida (DTOs): {report.rows_parsed}")
        print(f"Quantidade persistida (Upsert Banco): {report.rows_persisted}")
        print(f"Errors: {len(report.errors)}")
        for err in report.errors:
            print(f" - {err.message}")
        print(f"Status final: {'SUCESSO' if report.success else 'FALHA'}")
        print("="*50 + "\n")
        
        if not report.success:
            sys.exit(1)

if __name__ == "__main__":
    main()
