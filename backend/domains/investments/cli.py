import sys
import os
import time
import logging
import argparse
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from backend.domains.investments.readers.cei_reader import B3MovementsReader
from backend.domains.investments.parsers.cei_parser import B3MovementsParser
from backend.domains.investments.normalizers.cei_normalizer import B3MovementsNormalizer
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.import_report import ImportReport, ImportError as ImpError, ImportWarning
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("investments_cli")

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def main():
    parser = argparse.ArgumentParser(description="CEI Import Pipeline CLI")
    parser.add_argument("--file", required=True, help="Path to the B3 Negociação XLSX file")
    args = parser.parse_args()

    file_path = args.file

    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)

    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "fin_analytics.db")
    db_url = f"sqlite:///{os.path.abspath(db_path)}"
    
    logger.info("Iniciando importação do CEI...")
    start_time_perf = time.perf_counter()
    
    report = ImportReport(
        source="B3_CEI",
        file_name=os.path.basename(file_path)
    )
    
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as session:
            try:
                session.begin()
                
                # 1. Reader
                reader = B3MovementsReader()
                df = reader.read(file_path)
                qtd_lida = len(df)
                report.rows_read = qtd_lida
                logger.info(f"Quantidade lida (DataFrame): {qtd_lida}")
                
                # 2. Parser
                parser_cei = B3MovementsParser()
                raw_movements = parser_cei.parse(df)
                qtd_parseada = len(raw_movements)
                report.rows_parsed = qtd_parseada
                logger.info(f"Quantidade parseada (RawB3Movement): {qtd_parseada}")
                
                # 3. Normalizer
                normalizer = B3MovementsNormalizer()
                trades = normalizer.normalize(raw_movements)
                qtd_normalizada = len(trades)
                report.rows_normalized = qtd_normalizada
                logger.info(f"Quantidade normalizada (TradeDTO): {qtd_normalizada}")
                
                # 4. Repository
                repository = TradeRepository()
                qtd_persistida = repository.save_many(session, trades)
                report.rows_persisted = qtd_persistida
                logger.info(f"Quantidade persistida/upserted no banco: {qtd_persistida}")
                
                # Commit
                session.commit()
                report.success = True
                logger.info("Transação confirmada (Commit) com sucesso.")
                
            except KeyboardInterrupt:
                logger.warning("Operação cancelada pelo usuário (KeyboardInterrupt). Desfazendo transação...")
                session.rollback()
                report.errors.append(ImpError(message="Operação cancelada pelo usuário (KeyboardInterrupt)"))
            except Exception as e:
                logger.error(f"Erro no pipeline: {str(e)}")
                logger.warning("Desfazendo transação (Rollback)...")
                session.rollback()
                report.errors.append(ImpError(message=f"Erro no pipeline: {str(e)}"))
                
    finally:
        engine.dispose()
        end_time_perf = time.perf_counter()
        report.elapsed_ms = int((end_time_perf - start_time_perf) * 1000)
        report.finished_at = datetime.now(timezone.utc)
        
        print("\n" + "="*50)
        print("RELATÓRIO DE IMPORTAÇÃO")
        print("="*50)
        print(f"Arquivo: {report.file_name}")
        print(f"Tempo da execução: {report.elapsed_ms}ms")
        print(f"Quantidade lida: {report.rows_read}")
        print(f"Quantidade parseada: {report.rows_parsed}")
        print(f"Quantidade normalizada: {report.rows_normalized}")
        print(f"Quantidade persistida: {report.rows_persisted}")
        print(f"Duplicidades: {report.duplicates_detected}")
        print(f"Warnings: {len(report.warnings)}")
        for w in report.warnings:
            print(f" - {w.message}")
        print(f"Errors: {len(report.errors)}")
        for err in report.errors:
            print(f" - {err.message}")
        print(f"Status final: {'SUCESSO' if report.success else 'FALHA'}")
        print("="*50 + "\n")
        
        if not report.success:
            sys.exit(1)

if __name__ == "__main__":
    main()
