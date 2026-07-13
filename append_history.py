import sys
from decimal import Decimal

with open('backend/domains/investments/engines/performance_engine.py', 'a', encoding='utf-8') as f:
    f.write('''
    def generate_history(
        self,
        trades: list,
        snapshots: list,
        market_prices: dict,
        start_date,
        end_date,
        granularity: str = "month"
    ):
        """
        Gera a série temporal de performance para o portfólio.
        Utiliza a PositionEngine, ValuationEngine e WealthEngine para
        calcular o patrimônio iterativamente (mes a mes).
        O(N log N) complexidade temporal otimizada.
        """
        from backend.domains.investments.engines.position_engine import PositionEngine
        from backend.domains.investments.engines.valuation_engine import ValuationEngine
        from backend.domains.investments.engines.wealth_engine import WealthEngine
        from backend.domains.investments.services.market_data_service import MarketDataService
        from backend.domains.investments.dto import PerformanceHistory, PerformanceHistoryPoint, TradeType
        import calendar
        from dateutil.relativedelta import relativedelta
        from decimal import Decimal
        
        pos_engine = PositionEngine()
        val_engine = ValuationEngine()
        wealth_engine = WealthEngine()
        market_service = MarketDataService()
        
        # Helper para agrupar trades cronologicamente (Otimização)
        trades_sorted = sorted(trades, key=lambda t: t.trade_date)
        
        points = []
        
        # Define ranges
        current_date = start_date.replace(day=1)
        last_date = end_date
        
        # Acumuladores
        cumulative_cdi = Decimal('0')
        cumulative_ibov = Decimal('0')
        cumulative_ipca = Decimal('0')
        cumulative_ifix = Decimal('0')
        cumulative_sp500 = Decimal('0')
        cumulative_idiv = Decimal('0')
        
        previous_market_value = Decimal('0')
        previous_cost_basis = Decimal('0')
        
        while current_date <= last_date:
            # End of month
            _, last_day = calendar.monthrange(current_date.year, current_date.month)
            month_end = current_date.replace(day=last_day)
            if month_end > last_date:
                month_end = last_date
                
            # Filter trades up to month_end
            current_trades = [t for t in trades_sorted if t.trade_date <= month_end]
            
            # Snapshots up to month_end
            current_snapshots = [s for s in snapshots if s.reference_date <= month_end]
            
            # 1. Posição
            positions = pos_engine.calculate_position(current_trades, current_snapshots)
            
            # 2. Valuation
            valuations = val_engine.calculate_valuation(positions, market_prices)
            
            # 3. Wealth
            wealth = wealth_engine.calculate(valuations)
            
            patrimonio = wealth.total_market_value
            cost_basis = wealth.total_cost_basis
            
            # Compras e Vendas do mês
            compras_val = Decimal('0')
            vendas_val = Decimal('0')
            proventos_val = Decimal('0')
            
            # Calcula fluxo do mes atual
            month_start = current_date.replace(day=1)
            for t in current_trades:
                if month_start <= t.trade_date <= month_end:
                    if t.operation_type == TradeType.BUY:
                        compras_val += t.total_value
                    elif t.operation_type == TradeType.SELL:
                        vendas_val += t.total_value
                    elif t.operation_type in (TradeType.AMORTIZATION, TradeType.BONUS_SHARE):
                        proventos_val += t.total_value
            
            # Rentabilidade do Mês
            rent_mensal = Decimal('0')
            if previous_market_value > Decimal('0'):
                ganho = patrimonio - compras_val + vendas_val - previous_market_value
                rent_mensal = (ganho / previous_market_value) * Decimal('100')
                
            # Rentabilidade Acumulada Absoluta
            rent_acum = Decimal('0')
            if cost_basis > Decimal('0'):
                rent_acum = ((patrimonio - cost_basis) / cost_basis) * Decimal('100')
                
            # Benchmarks Reais
            market_data = market_service.get_market_data(month_end)
            
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
''')
