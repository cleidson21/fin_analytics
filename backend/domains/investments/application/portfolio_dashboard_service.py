from typing import List, Dict, Optional
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

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
        # portfolio_app is kept for backwards compatibility in ApplicationFactory
        # but will no longer be used for dashboard reads.
        pass

    def get_summary_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal], session: Optional[Session] = None) -> PortfolioDashboardDTO:
        if not session:
            raise ValueError("A valid DB session is required for Dashboard queries.")
            
        # Get the latest snapshot
        query = text("""
            SELECT 
                total_equity, cost_basis, cumulative_twr, mwr, 
                sharpe_ratio, sortino_ratio, max_drawdown, volatility_annual, 
                beta_ibov, alpha_ibov, dividends_total
            FROM portfolio_snapshots 
            ORDER BY date DESC 
            LIMIT 1
        """)
        row = session.execute(query).fetchone()
        
        if not row:
            return PortfolioDashboardDTO(
                current_wealth=Decimal('0'), invested_capital=Decimal('0'),
                unrealized_gain=Decimal('0'), unrealized_gain_percent=Decimal('0'),
                total_dividends=Decimal('0'), dividend_yield=Decimal('0'),
                twr=Decimal('0'), mwr=Decimal('0'),
                sharpe=Decimal('0'), sortino=Decimal('0'), max_drawdown=Decimal('0'),
                volatility=Decimal('0'), beta=Decimal('0'), alpha=Decimal('0'),
                tracking_error=Decimal('0'), information_ratio=Decimal('0')
            )
            
        wealth = Decimal(row[0]) / Decimal('100')
        cost_basis = Decimal(row[1]) / Decimal('100')
        total_dividends = Decimal(row[10]) / Decimal('100')
        
        unrealized_gain = wealth - cost_basis
        unrealized_gain_pct = (unrealized_gain / cost_basis) if cost_basis > 0 else Decimal('0')
        yield_val = (total_dividends / cost_basis) if cost_basis > 0 else Decimal('0')
        
        return PortfolioDashboardDTO(
            current_wealth=wealth,
            invested_capital=cost_basis,
            unrealized_gain=unrealized_gain,
            unrealized_gain_percent=unrealized_gain_pct,
            total_dividends=total_dividends,
            dividend_yield=yield_val,
            twr=Decimal(str(row[2] * 100)) if row[2] else Decimal('0'),
            mwr=Decimal(str(row[3] * 100)) if row[3] else Decimal('0'),
            sharpe=Decimal(str(row[4])) if row[4] else Decimal('0'),
            sortino=Decimal(str(row[5])) if row[5] else Decimal('0'),
            max_drawdown=Decimal(str(row[6] * 100)) if row[6] else Decimal('0'),
            volatility=Decimal(str(row[7] * 100)) if row[7] else Decimal('0'),
            beta=Decimal(str(row[8])) if row[8] else Decimal('0'),
            alpha=Decimal(str(row[9])) if row[9] else Decimal('0'),
            tracking_error=Decimal('0'),  # Not stored yet
            information_ratio=Decimal('0') # Not stored yet
        )

    def get_allocation_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal], session: Optional[Session] = None) -> AllocationDashboardDTO:
        if not session:
            raise ValueError("A valid DB session is required for Dashboard queries.")
            
        # Get the latest valuation records
        query = text("""
            SELECT 
                a.ticker, a.asset_class, acc.name as broker, v.market_value, v.portfolio_weight
            FROM asset_valuations v
            JOIN assets a ON v.asset_id = a.id
            JOIN accounts acc ON v.account_id = acc.id
            WHERE v.price_date = (SELECT MAX(price_date) FROM asset_valuations)
            AND v.market_value > 0
        """)
        rows = session.execute(query).fetchall()
        
        by_class_map = {}
        by_inst_map = {}
        by_asset_map = {}
        
        for r in rows:
            ticker = r[0]
            asset_class = r[1] or 'OUTROS'
            broker = r[2]
            market_value = Decimal(r[3]) / Decimal('100')
            weight = Decimal(str(r[4]))
            
            # Asset
            if ticker not in by_asset_map:
                by_asset_map[ticker] = AllocationItem(name=ticker, market_value=Decimal('0'), allocation_percent=Decimal('0'))
            by_asset_map[ticker].market_value += market_value
            by_asset_map[ticker].allocation_percent += weight
            
            # Class
            if asset_class not in by_class_map:
                by_class_map[asset_class] = AllocationItem(name=asset_class, market_value=Decimal('0'), allocation_percent=Decimal('0'))
            by_class_map[asset_class].market_value += market_value
            by_class_map[asset_class].allocation_percent += weight
            
            # Institution
            if broker not in by_inst_map:
                by_inst_map[broker] = AllocationItem(name=broker, market_value=Decimal('0'), allocation_percent=Decimal('0'))
            by_inst_map[broker].market_value += market_value
            by_inst_map[broker].allocation_percent += weight
            
        return AllocationDashboardDTO(
            by_class=list(by_class_map.values()),
            by_institution=list(by_inst_map.values()),
            by_asset=list(by_asset_map.values()),
            by_sector=[],
            by_type=[]
        )

    def get_performance_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal], session: Optional[Session] = None) -> PerformanceDashboardDTO:
        if not session:
            raise ValueError("A valid DB session is required for Dashboard queries.")
            
        query = text("""
            SELECT monthly_twr, cumulative_twr, alpha_ibov
            FROM portfolio_snapshots 
            ORDER BY date DESC 
            LIMIT 1
        """)
        row = session.execute(query).fetchone()
        
        monthly_ret = Decimal(str(row[0] * 100)) if (row and row[0]) else Decimal('0')
        cum_ret = Decimal(str(row[1] * 100)) if (row and row[1]) else Decimal('0')
        alpha = Decimal(str(row[2])) if (row and row[2]) else Decimal('0')
        
        return PerformanceDashboardDTO(
            monthly_return=monthly_ret,
            annual_return=Decimal('0'),  # Calculate later or store in db
            accumulated_return=cum_ret,
            rolling_returns={'1m': monthly_ret},
            benchmark_comparison={"IBOV": alpha}
        )

    def get_risk_dashboard(self, trades: List[TradeDTO], snapshots: List[PositionSnapshot], market_prices: Dict[str, Decimal], session: Optional[Session] = None) -> RiskDashboardDTO:
        if not session:
            raise ValueError("A valid DB session is required for Dashboard queries.")
            
        query = text("""
            SELECT max_drawdown, sharpe_ratio, sortino_ratio, volatility_annual, beta_ibov, alpha_ibov
            FROM portfolio_snapshots 
            ORDER BY date DESC 
            LIMIT 1
        """)
        row = session.execute(query).fetchone()
        
        return RiskDashboardDTO(
            current_drawdown=Decimal('0'), # Calculate from history if needed
            max_drawdown=Decimal(str(row[0] * 100)) if (row and row[0]) else Decimal('0'),
            sharpe=Decimal(str(row[1])) if (row and row[1]) else Decimal('0'),
            sortino=Decimal(str(row[2])) if (row and row[2]) else Decimal('0'),
            volatility=Decimal(str(row[3] * 100)) if (row and row[3]) else Decimal('0'),
            beta=Decimal(str(row[4])) if (row and row[4]) else Decimal('0'),
            alpha=Decimal(str(row[5])) if (row and row[5]) else Decimal('0')
        )

