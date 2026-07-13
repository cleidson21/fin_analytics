import math
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from backend.domains.investments.dto import PerformanceHistory, PerformanceHistoryPoint
from backend.domains.investments.engines.financial_analytics_dto import FinancialPerformanceDTO
from backend.domains.investments.services.historical_price_service import HistoricalPriceService

class FinancialAnalyticsEngine:
    """
    Motor analítico para cálculos financeiros avançados baseados em uma série histórica.
    """
    
    def __init__(self, historical_price_service=None):
        self.hist_service = historical_price_service
        
    def _xirr(self, cashflows: List[Tuple[date, Decimal]], guess: float = 0.1) -> float:
        """
        Calcula a Taxa Interna de Retorno (XIRR) usando o método de Newton-Raphson.
        """
        if not cashflows:
            return 0.0
            
        def npv(rate: float) -> float:
            total = 0.0
            t0 = cashflows[0][0]
            for t, amt in cashflows:
                days = (t - t0).days
                total += float(amt) / ((1 + rate) ** (days / 365.0))
            return total
            
        def npv_derivative(rate: float) -> float:
            total = 0.0
            t0 = cashflows[0][0]
            for t, amt in cashflows:
                days = (t - t0).days
                total -= (days / 365.0) * float(amt) / ((1 + rate) ** ((days / 365.0) + 1))
            return total
            
        x0 = guess
        for _ in range(100):
            fx = npv(x0)
            dfx = npv_derivative(x0)
            if abs(dfx) < 1e-8:
                break
            x1 = x0 - fx / dfx
            
            # Prevent negative base for fractional exponent which creates complex numbers
            if x1 <= -1.0:
                x1 = -0.9999
                
            if abs(x1 - x0) < 1e-8:
                return x1.real if isinstance(x1, complex) else x1
            x0 = x1
            
        return x0.real if isinstance(x0, complex) else x0
        
    def _covariance(self, xs: List[float], ys: List[float]) -> float:
        if len(xs) != len(ys) or len(xs) < 2: return 0.0
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / (n - 1)

    def _variance(self, xs: List[float]) -> float:
        if len(xs) < 2: return 0.0
        n = len(xs)
        mean_x = sum(xs) / n
        return sum((x - mean_x) ** 2 for x in xs) / (n - 1)

    def _std_dev(self, xs: List[float]) -> float:
        return math.sqrt(self._variance(xs))

    def calculate_metrics(self, history: PerformanceHistory, benchmark_ticker: str = "IBOV") -> FinancialPerformanceDTO:
        points = history.points
        if not points:
            return FinancialPerformanceDTO(
                twr=Decimal('0'), mwr=Decimal('0'), cagr=Decimal('0'), volatility=Decimal('0'),
                max_drawdown=Decimal('0'), current_drawdown=Decimal('0'), sharpe=Decimal('0'), sortino=Decimal('0'),
                alpha=Decimal('0'), beta=Decimal('0'), tracking_error=Decimal('0'), information_ratio=Decimal('0'),
                rolling_returns={'3m': None, '6m': None, '12m': None, '24m': None, 'inception': None},
                metadata={"status": "no_data"}
            )
            
        n = len(points)
        
        # 1. TWR (Time Weighted Return) e Retornos Periódicos
        twr = 1.0
        periodic_returns = [] # Portfolio Returns
        benchmark_returns = [] # Benchmark Returns
        risk_free_returns = [] # CDI proxy ou 0
        
        # Para MWR
        cashflows_mwr: List[Tuple[date, Decimal]] = []
        
        # Para Drawdown
        peak = 0.0
        max_dd = 0.0
        current_dd = 0.0
        
        # Busca o primeiro preco do benchmark no start date
        start_date_obj = date.fromisoformat(points[0].date)
        bm_start_price = float(self.hist_service.get_price_for_date(benchmark_ticker, start_date_obj) or 1.0)
        if bm_start_price == 0: bm_start_price = 1.0
        
        # Primeiro patrimonio pro MWR
        if points[0].patrimonio_value > 0:
            cashflows_mwr.append((start_date_obj, -points[0].patrimonio_value))
            
        last_pat = 0.0
        
        for i, pt in enumerate(points):
            pat = float(pt.patrimonio_value)
            compras = float(pt.compras_value)
            vendas = float(pt.vendas_value)
            proventos = float(pt.proventos_value)
            
            # Cashflows do mes atual = aportes - retiradas (vendas/proventos nao reinvestidos dependem do cenario, 
            # para MWR vamos assumir compras = aporte, vendas = retirada se for pro bolso, mas geralmente num
            # fechado o fluxo eh compras - vendas_liquidas. Simplificando: compras sao fluxos negativos, vendas/proventos positivos).
            # Para TWR: net_flow = aportes externos.
            net_flow = compras - vendas - proventos
            
            if i > 0:
                last_pat = float(points[i-1].patrimonio_value)
                
                # TWR Periodico: R_t = (Pat_t - Fluxos_t) / Pat_{t-1} - 1
                if last_pat > 0:
                    r_t = (pat - net_flow) / last_pat - 1.0
                else:
                    # Se last_pat era 0 e houve aporte, rentabilidade periodica do aporte = 0.
                    # Mas se o aporte foi ao longo do mes e cresceu, pode ter. Assumimos 0 para o delta puro s/ last pat.
                    r_t = 0.0
                    
                twr *= (1 + r_t)
                periodic_returns.append(r_t)
                
                # MWR
                current_date_obj = date.fromisoformat(pt.date)
                if net_flow != 0:
                    cashflows_mwr.append((current_date_obj, Decimal(-net_flow)))
                    
                # Benchmark Return
                bm_price = float(self.hist_service.get_price_for_date(benchmark_ticker, current_date_obj) or bm_start_price)
                if i == 1:
                    bm_prev = bm_start_price
                else:
                    prev_date_obj = date.fromisoformat(points[i-1].date)
                    bm_prev = float(self.hist_service.get_price_for_date(benchmark_ticker, prev_date_obj) or bm_start_price)
                    
                if bm_prev > 0:
                    r_b = (bm_price / bm_prev) - 1.0
                else:
                    r_b = 0.0
                benchmark_returns.append(r_b)
                
                # Risk Free (vamos usar 1% ao mes como mock provisorio, ou extrair do CDI real se disponivel)
                # O DTO tem cdi_accumulated mas vamos fixar 0.008 p/ simplificacao ou extrair delta
                # Se tivessemos a curva de CDI dariamos append
                risk_free_returns.append(0.008) # Mock 0.8% am
                
            # Drawdowns
            if pat > peak:
                peak = pat
            if peak > 0:
                current_dd = (pat - peak) / peak
                if current_dd < max_dd:
                    max_dd = current_dd
                    
        # Valor final para MWR
        final_date_obj = start_date_obj
        if n > 0:
            final_date_obj = date.fromisoformat(points[-1].date)
            if points[-1].patrimonio_value > 0:
                cashflows_mwr.append((final_date_obj, points[-1].patrimonio_value))
            
        twr_final = twr - 1.0
        
        # MWR final (calculando XIRR)
        mwr_final = 0.0
        try:
            mwr_final = self._xirr(cashflows_mwr, guess=0.1)
        except Exception:
            mwr_final = 0.0
            
        # CAGR (assumindo anual)
        days_total = (final_date_obj - start_date_obj).days
        years = days_total / 365.25 if days_total > 0 else 0
        cagr = 0.0
        if years > 0 and twr > 0:
            cagr = (twr ** (1 / years)) - 1.0
            
        # Volatilidade (anualizada, assumindo serie mensal)
        vol = self._std_dev(periodic_returns) * math.sqrt(12) if len(periodic_returns) > 1 else 0.0
        
        # Sharpe e Sortino
        ann_rf = 0.10 # 10% aa mock
        sharpe = (cagr - ann_rf) / vol if vol > 0 else 0.0
        
        neg_returns = [r for r in periodic_returns if r < 0]
        downside_vol = self._std_dev(neg_returns) * math.sqrt(12) if len(neg_returns) > 1 else 0.0
        sortino = (cagr - ann_rf) / downside_vol if downside_vol > 0 else 0.0
        
        # Beta & Alpha & Tracking Error & IR
        beta = 0.0
        alpha = 0.0
        te = 0.0
        ir = 0.0
        
        if len(periodic_returns) > 1 and len(benchmark_returns) == len(periodic_returns):
            cov = self._covariance(periodic_returns, benchmark_returns)
            var_b = self._variance(benchmark_returns)
            beta = cov / var_b if var_b > 0 else 0.0
            
            # Anualizando o benchmark
            bm_cum = 1.0
            for r in benchmark_returns: bm_cum *= (1+r)
            bm_cagr = (bm_cum ** (1 / years)) - 1.0 if years > 0 else 0.0
            
            alpha = cagr - (ann_rf + beta * (bm_cagr - ann_rf))
            
            diffs = [p - b for p, b in zip(periodic_returns, benchmark_returns)]
            te = self._std_dev(diffs) * math.sqrt(12)
            
            ir = (cagr - bm_cagr) / te if te > 0 else 0.0

        # Rolling Returns
        rolling = {'3m': None, '6m': None, '12m': None, '24m': None, 'inception': Decimal(str(round(twr_final, 4)))}
        def _get_rolling(m: int) -> Optional[Decimal]:
            if len(periodic_returns) >= m:
                cum = 1.0
                for r in periodic_returns[-m:]: cum *= (1+r)
                return Decimal(str(round(cum - 1.0, 4)))
            return None
            
        rolling['3m'] = _get_rolling(3)
        rolling['6m'] = _get_rolling(6)
        rolling['12m'] = _get_rolling(12)
        rolling['24m'] = _get_rolling(24)

        return FinancialPerformanceDTO(
            twr=Decimal(str(round(twr_final, 6))),
            mwr=Decimal(str(round(mwr_final, 6))),
            cagr=Decimal(str(round(cagr, 6))),
            volatility=Decimal(str(round(vol, 6))),
            max_drawdown=Decimal(str(round(max_dd, 6))),
            current_drawdown=Decimal(str(round(current_dd, 6))),
            sharpe=Decimal(str(round(sharpe, 6))),
            sortino=Decimal(str(round(sortino, 6))),
            alpha=Decimal(str(round(alpha, 6))),
            beta=Decimal(str(round(beta, 6))),
            tracking_error=Decimal(str(round(te, 6))),
            information_ratio=Decimal(str(round(ir, 6))),
            rolling_returns=rolling,
            metadata={"processed_months": str(n), "benchmark": benchmark_ticker}
        )
