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
