import logging
import uuid
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from backend.domains.investments.engines.wealth_engine import WealthSummary
from backend.domains.investments.engines.financial_analytics_dto import FinancialPerformanceDTO

logger = logging.getLogger(__name__)

class WealthRepository:
    """
    Repositório para persistir os consolidadores de portfólio (Wealth + Performance) 
    na tabela portfolio_snapshots do V3.
    """
    def __init__(self):
        self._default_user_id: Optional[str] = None
        
    def _get_default_user_id(self, session: Session) -> str:
        if self._default_user_id:
            return self._default_user_id
        result = session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if not result:
            return "00000000-0000-0000-0000-000000000000"
        self._default_user_id = result[0]
        return self._default_user_id

    def save_snapshot(
        self, 
        session: Session, 
        snapshot_date: date, 
        wealth: WealthSummary,
        performance: Optional[FinancialPerformanceDTO] = None
    ) -> None:
        """
        Salva ou atualiza a fotografia patrimonial global de um dia específico.
        """
        user_id = self._get_default_user_id(session)
        
        query = text("""
            INSERT INTO portfolio_snapshots (
                id, user_id, date, total_equity, cost_basis, total_deposits, total_withdrawals,
                quota_value, daily_twr, monthly_twr, cumulative_twr, mwr,
                sharpe_ratio, sortino_ratio, beta_ibov, alpha_ibov, max_drawdown, volatility_annual,
                ibov_cumulative, cdi_cumulative, ifix_cumulative, spx_cumulative,
                dividends_month, dividends_year, dividends_total
            ) VALUES (
                :id, :user_id, :date, :total_equity, :cost_basis, :total_deposits, :total_withdrawals,
                :quota_value, :daily_twr, :monthly_twr, :cumulative_twr, :mwr,
                :sharpe_ratio, :sortino_ratio, :beta_ibov, :alpha_ibov, :max_drawdown, :volatility_annual,
                :ibov_cumulative, :cdi_cumulative, :ifix_cumulative, :spx_cumulative,
                :dividends_month, :dividends_year, :dividends_total
            ) ON CONFLICT(user_id, date) DO UPDATE SET
                total_equity=excluded.total_equity,
                cost_basis=excluded.cost_basis,
                total_deposits=excluded.total_deposits,
                total_withdrawals=excluded.total_withdrawals,
                quota_value=excluded.quota_value,
                daily_twr=excluded.daily_twr,
                monthly_twr=excluded.monthly_twr,
                cumulative_twr=excluded.cumulative_twr,
                mwr=excluded.mwr,
                sharpe_ratio=excluded.sharpe_ratio,
                sortino_ratio=excluded.sortino_ratio,
                beta_ibov=excluded.beta_ibov,
                alpha_ibov=excluded.alpha_ibov,
                max_drawdown=excluded.max_drawdown,
                volatility_annual=excluded.volatility_annual,
                ibov_cumulative=excluded.ibov_cumulative,
                cdi_cumulative=excluded.cdi_cumulative,
                ifix_cumulative=excluded.ifix_cumulative,
                spx_cumulative=excluded.spx_cumulative,
                dividends_month=excluded.dividends_month,
                dividends_year=excluded.dividends_year,
                dividends_total=excluded.dividends_total,
                computed_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        """)
        
        # Mapeamento do Wealth
        total_equity = int(round(float(wealth.total_market_value) * 100))
        cost_basis = int(round(float(wealth.total_cost_basis) * 100))
        
        # Valores de performance defauls
        params = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "date": snapshot_date.isoformat(),
            "total_equity": total_equity,
            "cost_basis": cost_basis,
            "total_deposits": 0,       # Requer cashflow engine separado (pendente)
            "total_withdrawals": 0,    # Requer cashflow engine separado (pendente)
            "quota_value": 1.0,
            "daily_twr": 0.0,
            "monthly_twr": 0.0,
            "cumulative_twr": 0.0,
            "mwr": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "beta_ibov": 0.0,
            "alpha_ibov": 0.0,
            "max_drawdown": 0.0,
            "volatility_annual": 0.0,
            "ibov_cumulative": 0.0,
            "cdi_cumulative": 0.0,
            "ifix_cumulative": 0.0,
            "spx_cumulative": 0.0,
            "dividends_month": 0,
            "dividends_year": 0,
            "dividends_total": 0
        }

        # Override se tiver performance data
        if performance:
            params.update({
                "cumulative_twr": float(performance.twr) / 100.0 if performance.twr else 0.0,
                "mwr": float(performance.mwr) / 100.0 if performance.mwr else 0.0,
                "sharpe_ratio": float(performance.sharpe) if performance.sharpe else 0.0,
                "sortino_ratio": float(performance.sortino) if performance.sortino else 0.0,
                "beta_ibov": float(performance.beta) if performance.beta else 0.0,
                "alpha_ibov": float(performance.alpha) if performance.alpha else 0.0,
                "max_drawdown": float(performance.max_drawdown) / 100.0 if performance.max_drawdown else 0.0,
                "volatility_annual": float(performance.volatility) / 100.0 if performance.volatility else 0.0,
            })
            
        session.execute(query, params)
        session.commit()
