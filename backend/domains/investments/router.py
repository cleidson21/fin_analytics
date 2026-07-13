import logging
from typing import List, Dict
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.shared.db import get_db_connection
from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine, ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthEngine, WealthSummary, AssetSummary, InstitutionSummary
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.engines.performance_dto import PerformanceSummary
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory
from backend.domains.investments.repositories.import_log_repository import ImportLogRepository
from backend.domains.investments.services.reconciliation_service import ReconciliationService
from backend.domains.investments.services.import_service import ImportService
from fastapi import UploadFile, File, Depends

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Investments"])

def get_dummy_market_prices() -> Dict[str, Decimal]:
    # TODO: Implement MarketPriceService
    return {}

@router.get("/portfolio", response_model=WealthSummary)
def get_portfolio(db: Session = Depends(get_db_connection)):
    """Retorna o patrimônio global consolidado."""
    trade_repo = TradeRepository()
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    pos_engine = PositionEngine()
    val_engine = ValuationEngine()
    wealth_engine = WealthEngine()
    
    positions = pos_engine.calculate_position(trades, snapshots)
    valuations = val_engine.calculate_valuation(positions, get_dummy_market_prices())
    wealth = wealth_engine.calculate(valuations)
    
    return wealth

@router.get("/positions", response_model=List[ValuationResult])
def get_positions(db: Session = Depends(get_db_connection)):
    """Retorna a lista de posições avaliadas a mercado (MTM)."""
    trade_repo = TradeRepository()
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    pos_engine = PositionEngine()
    val_engine = ValuationEngine()
    
    positions = pos_engine.calculate_position(trades, snapshots)
    valuations = val_engine.calculate_valuation(positions, get_dummy_market_prices())
    
    return valuations

@router.get("/performance", response_model=PerformanceSummary)
def get_performance(db: Session = Depends(get_db_connection)):
    """Retorna as métricas de desempenho temporal da carteira."""
    wealth = get_portfolio(db)
    
    perf_engine = PerformanceEngine()
    # TODO: Fetch real realized_gain, dividends, cashflows, and dates
    start_date = date(datetime.now(timezone.utc).year, 1, 1)
    end_date = date.today()
    
    perf_summary = perf_engine.calculate(
        cost_basis=wealth.total_cost_basis,
        market_value=wealth.total_market_value,
        realized_gain=Decimal('0'),
        dividends_received=Decimal('0'),
        start_date=start_date,
        end_date=end_date,
        cashflows=[],
        sub_period_returns=[]
    )
    return perf_summary

@router.get("/performance/history", response_model=PerformanceHistory)
def get_performance_history(db: Session = Depends(get_db_connection)):
    """Retorna a série temporal histórica real."""
    trade_repo = TradeRepository()
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    if not trades and not snapshots:
        return PerformanceHistory(points=[], summary={})
        
    perf_engine = PerformanceEngine()
    
    # Se existirem trades, pegamos a data mais antiga
    start_date = min([t.trade_date for t in trades]) if trades else date(datetime.now(timezone.utc).year, 1, 1)
    end_date = date.today()
    
    # market_prices mock for now
    market_prices = get_dummy_market_prices()
    
    history = perf_engine.generate_history(
        trades=trades,
        snapshots=snapshots,
        market_prices=market_prices,
        start_date=start_date,
        end_date=end_date,
        granularity="month"
    )
    
    return history

@router.get("/allocation", response_model=List[AssetSummary])
def get_allocation(db: Session = Depends(get_db_connection)):
    """Retorna a alocação por ativo."""
    wealth = get_portfolio(db)
    return wealth.by_asset

@router.get("/institutions", response_model=List[InstitutionSummary])
def get_institutions(db: Session = Depends(get_db_connection)):
    """Retorna a alocação por corretora/instituição."""
    wealth = get_portfolio(db)
    return wealth.by_institution

@router.post("/import/cei", response_model=ImportReport)
async def import_cei(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    """Recebe arquivos CEI (CSV, XLSX) ou planilhas de corretoras e os processa com idempotência."""
    content = await file.read()
    service = ImportService(db)
    # Detects extension or uses file name
    # We pass it as CEI, meaning it will attempt XLSX/CSV B3 parsing
    report = service.process_import(content, file.filename, "CEI")
    return report

@router.post("/import/open-finance", response_model=ImportReport)
async def import_open_finance(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    """Recebe payload JSON do Open Finance e processa transações para o Ledger."""
    content = await file.read()
    service = ImportService(db)
    
    # Simple heuristic to determine if it is OFX by filename, or pass OPEN_FINANCE
    import_type = "OFX" if file.filename.lower().endswith(".ofx") else "OPEN_FINANCE"
    report = service.process_import(content, file.filename, import_type)
    return report

@router.get("/import/history", response_model=List[ImportLogDTO])
def get_import_history(
    status: str = None,
    parser: str = None,
    checksum: str = None,
    filename: str = None,
    db: Session = Depends(get_db_connection)
):
    """Histórico de importações (Logs)."""
    repo = ImportLogRepository()
    filters = {}
    if status: filters["status"] = status
    if parser: filters["parser"] = parser
    if checksum: filters["checksum"] = checksum
    if filename: filters["filename"] = filename
    
    logs = repo.list_history(db, filters)
    return logs

@router.get("/import/{log_id}", response_model=ImportLogDTO)
def get_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    """Detalhes de uma importação específica."""
    repo = ImportLogRepository()
    log = repo.get_by_id(db, log_id)
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log de importação não encontrado")
    return log

@router.delete("/import/{log_id}")
def delete_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    """Deleta um registro do histórico de importação (Apenas Administrador/Manual)."""
    repo = ImportLogRepository()
    success = repo.delete(db, log_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log de importação não encontrado")
    db.commit()
    return {"message": "Deletado com sucesso"}

@router.get("/reconciliation", response_model=List[ReconciliationResult])
def get_reconciliation(db: Session = Depends(get_db_connection)):
    """Retorna o resultado da conciliação inteligente entre o Ledger e os Snapshots (Open Finance)."""
    service = ReconciliationService(db)
    return service.reconcile()
