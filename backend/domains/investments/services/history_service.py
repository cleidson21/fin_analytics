import calendar
from typing import List, Dict, Optional
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from backend.domains.investments.engines.position_engine import PositionEngine, PositionResult
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine
from backend.domains.investments.services.market_data_service import MarketDataService
from backend.domains.investments.dto import PerformanceHistory, PerformanceHistoryPoint, TradeDTO, TradeType, PositionSnapshot
from backend.domains.investments.repositories.valuation_repository import ValuationRepository
from backend.domains.investments.repositories.wealth_repository import WealthRepository
from sqlalchemy.orm import Session

class HistoryService:
    """
    Serviço orquestrador para construção do histórico temporal de performance.
    Resolve a dívida técnica DT-01, atingindo complexidade O(N + M) ao
    processar de forma incremental as posições do portfólio.
    """
    def __init__(
        self,
        pos_engine: PositionEngine,
        val_engine: ValuationEngine,
        wealth_engine: WealthEngine,
        market_service: MarketDataService,
        valuation_repo: Optional[ValuationRepository] = None,
        wealth_repo: Optional[WealthRepository] = None
    ):
        self.pos_engine = pos_engine
        self.val_engine = val_engine
        self.wealth_engine = wealth_engine
        self.market_service = market_service
        self.valuation_repo = valuation_repo
        self.wealth_repo = wealth_repo

    def generate_history(
        self,
        trades: List[TradeDTO],
        snapshots: List[PositionSnapshot],
        market_prices: Dict[str, Decimal],
        start_date: date,
        end_date: date,
        granularity: str = "month",
        session: Optional[Session] = None
    ) -> PerformanceHistory:
        
        trades_sorted = sorted(trades, key=lambda t: t.trade_date)
        points = []
        
        current_date = start_date.replace(day=1)
        last_date = end_date
        
        # Acumuladores de benchmark
        cumulative_cdi = Decimal('0')
        cumulative_ibov = Decimal('0')
        cumulative_ipca = Decimal('0')
        cumulative_ifix = Decimal('0')
        cumulative_sp500 = Decimal('0')
        cumulative_idiv = Decimal('0')
        
        previous_market_value = Decimal('0')
        previous_cost_basis = Decimal('0')
        
        # Estado corrente O(1) repassado mês a mês
        current_positions_result: List[PositionResult] = []
        
        idx_trade = 0
        total_trades = len(trades_sorted)
        
        while current_date <= last_date:
            _, last_day = calendar.monthrange(current_date.year, current_date.month)
            month_end = current_date.replace(day=last_day)
            if month_end > last_date:
                month_end = last_date
                
            month_start = current_date.replace(day=1)
            
            # Extrair trades apenas deste mês
            current_month_trades = []
            while idx_trade < total_trades and trades_sorted[idx_trade].trade_date <= month_end:
                t = trades_sorted[idx_trade]
                if t.trade_date >= month_start:
                    current_month_trades.append(t)
                idx_trade += 1
                
            # Converter posições do mês anterior em trades iniciais para o PositionEngine
            initial_trades = []
            for pos in current_positions_result:
                if pos.quantity > 0:
                    initial_trades.append(TradeDTO(
                        ticker=pos.ticker,
                        broker=pos.institution,
                        operation_type=TradeType.INITIAL_POSITION,
                        trade_date=month_start,
                        quantity=pos.quantity,
                        unit_price=pos.average_price,
                        total_value=pos.invested_value,
                        source="HISTORY_INCREMENTAL",
                        idempotency_hash=f"hist_{pos.ticker}_{pos.institution}_{month_start}"
                    ))
            
            current_snapshots = [s for s in snapshots if month_start <= s.reference_date <= month_end]
            
            # Position Engine calcula apenas O Delta do Mês (O(T_m + P))
            current_positions_result = self.pos_engine.calculate_position(initial_trades + current_month_trades, current_snapshots)
            
            valuations = self.val_engine.calculate_valuation(
                positions=current_positions_result, 
                market_prices=market_prices,
                reference_date=month_end
            )
            wealth = self.wealth_engine.calculate(valuations)
            
            if session and self.valuation_repo and self.wealth_repo:
                try:
                    self.valuation_repo.save_valuations(session, valuations, month_end)
                    self.wealth_repo.save_snapshot(session, month_end, wealth)
                except Exception:
                    pass # Evitar falha total caso um ativo falhe no DB
            
            patrimonio = wealth.total_market_value
            cost_basis = wealth.total_cost_basis
            
            compras_val = sum(t.total_value for t in current_month_trades if t.operation_type == TradeType.BUY)
            vendas_val = sum(t.total_value for t in current_month_trades if t.operation_type == TradeType.SELL)
            proventos_val = sum(t.total_value for t in current_month_trades if t.operation_type in (TradeType.AMORTIZATION, TradeType.BONUS_SHARE))
            
            rent_mensal = Decimal('0')
            if previous_market_value > Decimal('0'):
                ganho = patrimonio - compras_val + vendas_val - previous_market_value
                rent_mensal = (ganho / previous_market_value) * Decimal('100')
                
            rent_acum = Decimal('0')
            if cost_basis > Decimal('0'):
                rent_acum = ((patrimonio - cost_basis) / cost_basis) * Decimal('100')
                
            market_data = self.market_service.get_market_data(month_end)
            
            cumulative_ibov += market_data.ibov
            cumulative_cdi += market_data.cdi
            cumulative_ipca += market_data.ipca
            cumulative_ifix += market_data.ifix
            cumulative_sp500 += market_data.sp500
            cumulative_idiv += market_data.idiv
            
            pt = PerformanceHistoryPoint(
                date=month_end.isoformat(),
                month=month_end.strftime("%b %Y"), 
                patrimonio=f"R$ {patrimonio:,.2f}",
                patrimonio_value=patrimonio,
                compras=f"R$ {compras_val:,.2f}",
                compras_value=compras_val,
                vendas=f"R$ {vendas_val:,.2f}",
                vendas_value=vendas_val,
                proventos=f"R$ {proventos_val:,.2f}",
                proventos_value=proventos_val,
                rentabilidade_mensal_pct=rent_mensal,
                rentabilidade_acumulada_pct=rent_acum,
                ibov_mensal_pct=market_data.ibov,
                ibov_acumulado_pct=cumulative_ibov,
                cdi_mensal_pct=market_data.cdi,
                cdi_acumulado_pct=cumulative_cdi,
                ipca_mensal_pct=market_data.ipca,
                ipca_acumulado_pct=cumulative_ipca,
                ifix_mensal_pct=market_data.ifix,
                ifix_acumulado_pct=cumulative_ifix,
                sp500_mensal_pct=market_data.sp500,
                sp500_acumulado_pct=cumulative_sp500,
                idiv_mensal_pct=market_data.idiv,
                idiv_acumulado_pct=cumulative_idiv
            )
            
            points.append(pt)
            
            previous_market_value = patrimonio
            previous_cost_basis = cost_basis
            
            current_date += relativedelta(months=1)
            
        summary = {
            "patrimonio_atual": float(previous_market_value) if points else 0.0,
            "rentabilidade_acumulada": float(points[-1].rentabilidade_acumulada_pct) if points else 0.0,
        }
        
        return PerformanceHistory(points=points, summary=summary)
