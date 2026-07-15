from typing import List, Dict, Optional
from datetime import date
from decimal import Decimal

from backend.domains.investments.engines.position_engine import PositionEngine, PositionResult
from backend.domains.investments.engines.valuation_engine import ValuationEngine, ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthEngine, WealthSummary
from backend.domains.investments.engines.financial_analytics_engine import FinancialAnalyticsEngine
from backend.domains.investments.services.history_service import HistoryService
from backend.domains.investments.dto import TradeDTO, PositionSnapshot, PerformanceHistory
from backend.domains.investments.engines.financial_analytics_dto import FinancialPerformanceDTO

from backend.domains.investments.repositories.valuation_repository import ValuationRepository
from backend.domains.investments.repositories.wealth_repository import WealthRepository
from backend.domains.investments.repositories.dividend_repository import DividendRepository
from sqlalchemy.orm import Session

class PortfolioApplicationService:
    def __init__(
        self,
        position_engine: PositionEngine,
        valuation_engine: ValuationEngine,
        wealth_engine: WealthEngine,
        financial_engine: FinancialAnalyticsEngine,
        history_service: HistoryService,
        valuation_repo: ValuationRepository,
        wealth_repo: WealthRepository,
        dividend_repo: DividendRepository
    ):
        self.position_engine = position_engine
        self.valuation_engine = valuation_engine
        self.wealth_engine = wealth_engine
        self.financial_engine = financial_engine
        self.history_service = history_service
        self.valuation_repo = valuation_repo
        self.wealth_repo = wealth_repo
        self.dividend_repo = dividend_repo

    def get_current_portfolio(
        self,
        trades: List[TradeDTO],
        snapshots: List[PositionSnapshot],
        market_prices: Dict[str, Decimal],
        session: Optional[Session] = None
    ) -> Dict:
        # Posições atuais
        positions = self.position_engine.calculate_position(trades, snapshots)
        
        # Valuation (sempre com preço live)
        valuations = self.valuation_engine.calculate_valuation(positions, market_prices, reference_date=None)
        
        # Consolidação patrimonial
        wealth = self.wealth_engine.calculate(valuations)
        
        if session:
            try:
                today = date.today()
                self.valuation_repo.save_valuations(session, valuations, today)
                self.wealth_repo.save_snapshot(session, today, wealth, performance=None)
            except Exception as e:
                pass # Em caso de erro de persistência, não quebrar a API
        
        return {
            "positions": positions,
            "valuations": valuations,
            "wealth": wealth
        }

    def generate_historical_performance(
        self,
        trades: List[TradeDTO],
        snapshots: List[PositionSnapshot],
        market_prices: Dict[str, Decimal],
        start_date: date,
        end_date: date,
        session: Optional[Session] = None
    ) -> PerformanceHistory:
        return self.history_service.generate_history(
            trades=trades,
            snapshots=snapshots,
            market_prices=market_prices,
            start_date=start_date,
            end_date=end_date,
            session=session
        )

    def calculate_advanced_metrics(self, history: PerformanceHistory) -> FinancialPerformanceDTO:
        return self.financial_engine.calculate_metrics(history)
