import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Dict

from fastapi import APIRouter
from sqlalchemy.orm import Session

from backend.shared.db import get_db_connection
from backend.domains.investments.engines.valuation_engine import ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthSummary, AssetSummary, InstitutionSummary
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.engines.performance_dto import PerformanceSummary
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory
from backend.domains.investments.engines.financial_analytics_dto import FinancialPerformanceDTO
from backend.domains.investments.application_factory import ApplicationFactory
from backend.domains.investments.dashboard_dto import PortfolioDashboardDTO, AllocationDashboardDTO, PerformanceDashboardDTO, RiskDashboardDTO
from fastapi import UploadFile, File, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Investments"])

def get_dummy_market_prices() -> Dict[str, Decimal]:
    return {}

@router.get("/portfolio", response_model=WealthSummary)
def get_portfolio(db: Session = Depends(get_db_connection)):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
        
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    res = portfolio_app.get_current_portfolio(trades, snapshots, get_dummy_market_prices())
    return res['wealth']

@router.get("/positions", response_model=List[ValuationResult])
def get_positions(db: Session = Depends(get_db_connection)):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    res = portfolio_app.get_current_portfolio(trades, snapshots, get_dummy_market_prices())
    return res['valuations']

@router.get("/performance", response_model=PerformanceSummary)
def get_performance(db: Session = Depends(get_db_connection)):
    wealth = get_portfolio(db)
    perf_engine = PerformanceEngine()
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
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    if not trades and not snapshots:
        return PerformanceHistory(points=[], summary={})
        
    start_date = min([t.trade_date for t in trades]) if trades else date(datetime.now(timezone.utc).year, 1, 1)
    end_date = date.today()
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    history = portfolio_app.generate_historical_performance(
        trades=trades,
        snapshots=snapshots,
        market_prices=get_dummy_market_prices(),
        start_date=start_date,
        end_date=end_date
    )
    return history

@router.get("/performance/analytics", response_model=FinancialPerformanceDTO)
def get_performance_analytics(db: Session = Depends(get_db_connection)):
    history = get_performance_history(db)
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    return portfolio_app.calculate_advanced_metrics(history)

@router.get("/allocation", response_model=List[AssetSummary])
def get_allocation(db: Session = Depends(get_db_connection)):
    wealth = get_portfolio(db)
    return wealth.by_asset

@router.get("/institutions", response_model=List[InstitutionSummary])
def get_institutions(db: Session = Depends(get_db_connection)):
    wealth = get_portfolio(db)
    return wealth.by_institution

@router.post("/import/cei", response_model=ImportReport)
async def import_cei(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    content = await file.read()
    import_app = ApplicationFactory.get_import_application_service()
    return import_app.execute_import(db, content, file.filename, "CEI")

@router.post("/import/open-finance", response_model=ImportReport)
async def import_open_finance(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    content = await file.read()
    import_app = ApplicationFactory.get_import_application_service()
    import_type = "OFX" if file.filename.lower().endswith(".ofx") else "OPEN_FINANCE"
    return import_app.execute_import(db, content, file.filename, import_type)

@router.get("/import/history", response_model=List[ImportLogDTO])
def get_import_history(
    status: str = None,
    parser: str = None,
    checksum: str = None,
    filename: str = None,
    db: Session = Depends(get_db_connection)
):
    repo = ApplicationFactory.get_import_log_repository()
    filters = {}
    if status: filters["status"] = status
    if parser: filters["parser"] = parser
    if checksum: filters["checksum"] = checksum
    if filename: filters["filename"] = filename
    return repo.list_history(db, filters)

@router.get("/import/{log_id}", response_model=ImportLogDTO)
def get_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    repo = ApplicationFactory.get_import_log_repository()
    log = repo.get_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado")
    return log

@router.delete("/import/{log_id}")
def delete_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    repo = ApplicationFactory.get_import_log_repository()
    if not repo.delete(db, log_id):
        raise HTTPException(status_code=404, detail="Log não encontrado")
    db.commit()
    return {"message": "Deletado"}

@router.get("/reconciliation", response_model=List[ReconciliationResult])
def get_reconciliation(db: Session = Depends(get_db_connection)):
    import_app = ApplicationFactory.get_import_application_service()
    return import_app.execute_reconciliation(db)

def _get_base_data_for_dashboard(db: Session):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    # We use empty market prices for now
    return trades, snapshots, {}

@router.get("/dashboard/summary", response_model=PortfolioDashboardDTO)
def get_dashboard_summary(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_summary_dashboard(trades, snapshots, prices)

@router.get("/dashboard/allocation", response_model=AllocationDashboardDTO)
def get_dashboard_allocation(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_allocation_dashboard(trades, snapshots, prices)

@router.get("/dashboard/performance", response_model=PerformanceDashboardDTO)
def get_dashboard_performance(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_performance_dashboard(trades, snapshots, prices)

@router.get("/dashboard/risk", response_model=RiskDashboardDTO)
def get_dashboard_risk(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_risk_dashboard(trades, snapshots, prices)

@router.get("/dashboard")
def get_dashboard_full(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return {
        "summary": service.get_summary_dashboard(trades, snapshots, prices),
        "allocation": service.get_allocation_dashboard(trades, snapshots, prices),
        "performance": service.get_performance_dashboard(trades, snapshots, prices),
        "risk": service.get_risk_dashboard(trades, snapshots, prices)
    }
