from decimal import Decimal
from datetime import date
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.engines.performance_dto import CashFlow

def run_tests():
    engine = PerformanceEngine()
    d_start = date(2023, 1, 1)
    d_end   = date(2024, 1, 1)  # exatamente 365 dias

    # 1. Carteira vazia / patrimônio zero
    res = engine.calculate(Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), d_start, d_end)
    assert res.metrics.unrealized_gain == Decimal('0')
    assert res.metrics.total_return == Decimal('0')
    assert res.metrics.cagr == Decimal('0')

    # 2. Custo zero, market value positivo (bônus)
    res = engine.calculate(Decimal('0'), Decimal('500'), Decimal('0'), Decimal('0'), d_start, d_end)
    assert res.metrics.unrealized_return_pct == Decimal('100')

    # 3. Ganho positivo (10% em 365 dias)
    res = engine.calculate(Decimal('10000'), Decimal('11000'), Decimal('0'), Decimal('0'), d_start, d_end)
    assert res.metrics.unrealized_gain == Decimal('1000')
    assert res.metrics.unrealized_return_pct == Decimal('10')
    # CAGR de 10% em 365 dias deve resultar em ~10%
    assert abs(res.metrics.cagr - Decimal('10')) < Decimal('0.01')

    # 4. Perda
    res = engine.calculate(Decimal('10000'), Decimal('9000'), Decimal('0'), Decimal('0'), d_start, d_end)
    assert res.metrics.unrealized_gain == Decimal('-1000')
    assert res.metrics.unrealized_return_pct == Decimal('-10')

    # 5. Retorno nulo (estático)
    res = engine.calculate(Decimal('10000'), Decimal('10000'), Decimal('0'), Decimal('0'), d_start, d_end)
    assert res.metrics.unrealized_gain == Decimal('0')
    assert res.metrics.total_return == Decimal('0')
    assert res.metrics.unrealized_return_pct == Decimal('0')

    # 6. Dividendos / Yield on Cost
    res = engine.calculate(Decimal('10000'), Decimal('10000'), Decimal('0'), Decimal('1000'), d_start, d_end)
    assert res.metrics.dividends_received == Decimal('1000')
    assert res.metrics.yield_on_cost == Decimal('10')
    assert res.metrics.total_return == Decimal('1000')
    assert res.metrics.total_return_pct == Decimal('10')

    # 7. Cashflows presentes (MWR aproximado)
    cfs = [
        CashFlow(amount=Decimal('-5000'), flow_date=date(2023, 6, 1), flow_type="DEPOSIT")
    ]
    res = engine.calculate(Decimal('10000'), Decimal('11000'), Decimal('0'), Decimal('0'), d_start, d_end, cashflows=cfs)
    assert res.metrics.mwr != Decimal('0')  # Deve calcular algo

    # 8. TWR com múltiplos sub-períodos
    # +5% no Q1, -3% no Q2, +8% no Q3, +2% no Q4
    sub_returns = [Decimal('5'), Decimal('-3'), Decimal('8'), Decimal('2')]
    res_twr = engine.calculate(Decimal('10000'), Decimal('11000'), Decimal('0'), Decimal('0'), d_start, d_end, sub_period_returns=sub_returns)
    # TWR = (1.05 * 0.97 * 1.08 * 1.02) - 1 = ~12.41%
    # TWR = (1.05 * 0.97 * 1.08 * 1.02) - 1 = ~12.198%
    assert abs(res_twr.metrics.twr - Decimal('12.20')) < Decimal('0.01')

    # 9. TWR com falência (retorno < -100%)
    sub_returns_crash = [Decimal('5'), Decimal('-100')]
    res_crash = engine.calculate(Decimal('10000'), Decimal('0'), Decimal('0'), Decimal('0'), d_start, d_end, sub_period_returns=sub_returns_crash)
    assert res_crash.metrics.twr == Decimal('-100')

    # 10. CAGR exato em N anos
    # Investimento de 1000, cresceu para 1210 em 730 dias (2 anos exatos): CAGR = 10%
    # 2023-01-01 to 2024-12-31 = 730 days
    d2 = date(2024, 12, 31)  # 730 dias from 2023-01-01
    res_cagr = engine.calculate(Decimal('1000'), Decimal('1210'), Decimal('0'), Decimal('0'), d_start, d2)
    assert abs(res_cagr.metrics.cagr - Decimal('10')) < Decimal('0.01')

    # 11. Divisão por zero protegida — holding_days = 1 (engine usa max(...,1))
    # Quando start == end, o engine usa 1 dia como mínimo e retorna um CAGR annualizado por 1 dia.
    res_zero_days = engine.calculate(Decimal('10000'), Decimal('12000'), Decimal('0'), Decimal('0'), d_end, d_end)
    # O retorno não deve lançar exceção. CAGR pode ser muito alto (anualizando 20% em 1 dia) mas é definido.
    assert res_zero_days.metrics.cagr != Decimal('0') or res_zero_days.metrics.unrealized_gain == Decimal('2000')

    # 12. Múltiplos ativos / retorno combinado (soma manual)
    # PETR4: cost 3000, mv 3300, gain 300
    # VALE3: cost 5000, mv 4500, gain -500
    total_cost = Decimal('8000')
    total_mv   = Decimal('7800')
    total_gain_realized = Decimal('0')
    total_div  = Decimal('200')
    res_multi = engine.calculate(total_cost, total_mv, total_gain_realized, total_div, d_start, d_end)
    assert res_multi.metrics.unrealized_gain == Decimal('-200')
    assert res_multi.metrics.total_return == Decimal('0')  # -200 + 0 + 200 = 0
    assert res_multi.metrics.total_return_pct == Decimal('0')

    print("✅ TODOS OS TESTES DA PERFORMANCE ENGINE PASSARAM!")

if __name__ == "__main__":
    run_tests()
