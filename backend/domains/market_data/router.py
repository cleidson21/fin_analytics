from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.shared.db import get_db_connection
from backend.domains.identity.router import get_current_user
from backend.domains.market_data.providers.yahoo_finance import YahooFinanceProvider
from backend.domains.market_data.repository import MarketDataRepository
from backend.domains.market_data.service import MarketDataService
from backend.domains.market_data.scheduler import MarketDataScheduler
from backend.domains.market_data.scheduler import MarketDataScheduler
from backend.domains.market_data.providers.banco_central import BCProvider
from backend.domains.market_data.macro_repository import MacroIndicatorsRepository
from backend.domains.market_data.macro_service import MacroIndicatorsService

from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine
from backend.domains.investments.engines.financial_analytics_engine import FinancialAnalyticsEngine
from backend.domains.investments.services.history_service import HistoryService
from backend.domains.investments.repositories.valuation_repository import ValuationRepository
from backend.domains.investments.repositories.wealth_repository import WealthRepository
from backend.domains.investments.repositories.dividend_repository import DividendRepository
from backend.domains.investments.application.portfolio_application_service import PortfolioApplicationService

router = APIRouter(prefix="/market-data", tags=["Market Data"])

def get_market_data_scheduler():
    # Setup Portfolio dependencies
    position_engine = PositionEngine()
    valuation_engine = ValuationEngine()
    wealth_engine = WealthEngine()
    financial_engine = FinancialAnalyticsEngine()
    history_service = HistoryService(valuation_engine, wealth_engine)
    valuation_repo = ValuationRepository()
    wealth_repo = WealthRepository()
    dividend_repo = DividendRepository()
    
    portfolio_service = PortfolioApplicationService(
        position_engine=position_engine,
        valuation_engine=valuation_engine,
        wealth_engine=wealth_engine,
        financial_engine=financial_engine,
        history_service=history_service,
        valuation_repo=valuation_repo,
        wealth_repo=wealth_repo,
        dividend_repo=dividend_repo
    )
    
    provider = YahooFinanceProvider()
    repository = MarketDataRepository()
    service = MarketDataService(provider, repository, portfolio_service)
    
    macro_service = get_macro_indicators_service()
    
    return MarketDataScheduler(service, macro_service)


def get_macro_indicators_service():
    provider = BCProvider()
    repository = MacroIndicatorsRepository()
    return MacroIndicatorsService(provider, repository)

@router.post("/sync")
def sync_market_data(
    db: Session = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """
    Dispara a sincronização manual dos preços do Yahoo Finance
    e atualiza a tabela asset_valuations do usuário atual.
    """
    try:
        scheduler = get_market_data_scheduler()
        result = scheduler.run_sync()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro")
def get_macro_indicators(
    db: Session = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = get_macro_indicators_service()
        return service.get_latest_indicators(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/history")
def get_macro_history(
    indicator: str = None,
    db: Session = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = get_macro_indicators_service()
        return service.get_historical_indicators(db, indicator)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
