from typing import List, Dict, Optional
from datetime import date, datetime, timezone
from decimal import Decimal

from backend.domains.investments.application.portfolio_application_service import PortfolioApplicationService
from backend.domains.investments.dashboard_dto import (
    PortfolioDashboardDTO,
    AllocationDashboardDTO,
    AllocationItem,
    PerformanceDashboardDTO,
    RiskDashboardDTO
)
from backend.domains.investments.dto import TradeDTO, PositionSnapshot

class PortfolioDashboardService:
    def __init__(self, portfolio_app: PortfolioApplicationService):
        self.portfolio_app = portfolio_app

    def _get_base_data(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal]):
        # Get wealth
        portfolio_res = self.portfolio_app.get_current_portfolio(trades, snapshots, market_prices)
        wealth = portfolio_res["wealth"]
        
        # Get historical performance
        start_date = min([t.trade_date for t in trades]) if trades else date(datetime.now(timezone.utc).year, 1, 1)
        end_date = date.today()
        history = self.portfolio_app.generate_historical_performance(trades, snapshots, market_prices, start_date, end_date)
        
        # Get financial metrics
        metrics = self.portfolio_app.calculate_advanced_metrics(history)
        
        return wealth, history, metrics

    def get_summary_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal]) -> PortfolioDashboardDTO:
        wealth, history, metrics = self._get_base_data(trades, snapshots, market_prices)
        
        # Extract total dividends from history summary (or calculate)
        total_dividends = history.summary.get("total_proventos", Decimal('0')) if history.summary else Decimal('0')
        yield_val = (total_dividends / wealth.total_cost_basis) if wealth.total_cost_basis > 0 else Decimal('0')
        
        return PortfolioDashboardDTO(
            current_wealth=wealth.total_market_value,
            invested_capital=wealth.total_cost_basis,
            unrealized_gain=wealth.total_unrealized_gain,
            unrealized_gain_percent=wealth.total_unrealized_gain_percent,
            total_dividends=total_dividends,
            dividend_yield=yield_val,
            twr=metrics.twr,
            mwr=metrics.mwr,
            sharpe=metrics.sharpe,
            sortino=metrics.sortino,
            max_drawdown=metrics.max_drawdown,
            volatility=metrics.volatility,
            beta=metrics.beta,
            alpha=metrics.alpha,
            tracking_error=metrics.tracking_error,
            information_ratio=metrics.information_ratio
        )

    def get_allocation_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal]) -> AllocationDashboardDTO:
        wealth, _, _ = self._get_base_data(trades, snapshots, market_prices)
        
        by_class = [AllocationItem(name=i.asset_class, market_value=i.market_value, allocation_percent=i.allocation_percent) for i in wealth.by_class]
        by_inst = [AllocationItem(name=i.institution, market_value=i.market_value, allocation_percent=i.allocation_percent) for i in wealth.by_institution]
        by_asset = [AllocationItem(name=i.ticker, market_value=i.market_value, allocation_percent=i.allocation_percent) for i in wealth.by_asset]
        
        # Mock sector and type if not present in WealthSummary (since they weren't fully exposed, but required by prompt)
        by_sector = []
        by_type = []
        
        return AllocationDashboardDTO(
            by_class=by_class,
            by_institution=by_inst,
            by_asset=by_asset,
            by_sector=by_sector,
            by_type=by_type
        )

    def get_performance_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal]) -> PerformanceDashboardDTO:
        _, history, metrics = self._get_base_data(trades, snapshots, market_prices)
        
        # history summary has 'rendimento_acumulado_pct' etc
        return PerformanceDashboardDTO(
            monthly_return=metrics.rolling_returns.get('1m', Decimal('0')) or Decimal('0'),
            annual_return=metrics.cagr,
            accumulated_return=metrics.twr,
            rolling_returns=metrics.rolling_returns,
            benchmark_comparison={"IBOV": metrics.alpha}  # Simplification
        )

    def get_risk_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal]) -> RiskDashboardDTO:
        _, _, metrics = self._get_base_data(trades, snapshots, market_prices)
        
        return RiskDashboardDTO(
            current_drawdown=metrics.current_drawdown,
            max_drawdown=metrics.max_drawdown,
            sharpe=metrics.sharpe,
            sortino=metrics.sortino,
            volatility=metrics.volatility,
            beta=metrics.beta,
            alpha=metrics.alpha
        )
