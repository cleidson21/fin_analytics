from backend.domains.investments.application_factory import ApplicationFactory
from backend.domains.investments.services.historical_price_service import HistoricalPriceService

import sys, os
from decimal import Decimal
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.engines.financial_analytics_engine import FinancialAnalyticsEngine
from backend.domains.investments.dto import PerformanceHistory, PerformanceHistoryPoint

def make_point(d, pat, comp):
    return PerformanceHistoryPoint(
        date=str(d), month=d.strftime('%b/%y'), patrimonio='', patrimonio_value=Decimal(pat),
        compras='', compras_value=Decimal(comp), vendas='', vendas_value=Decimal('0'), proventos='', proventos_value=Decimal('0'),
        rentabilidade_mensal_pct=Decimal('0'), rentabilidade_acumulada_pct=Decimal('0'), ibov_mensal_pct=Decimal('0'), ibov_acumulado_pct=Decimal('0'),
        cdi_mensal_pct=Decimal('0'), cdi_acumulado_pct=Decimal('0'), ipca_mensal_pct=Decimal('0'), ipca_acumulado_pct=Decimal('0'),
        ifix_mensal_pct=Decimal('0'), ifix_acumulado_pct=Decimal('0'), sp500_mensal_pct=Decimal('0'), sp500_acumulado_pct=Decimal('0'), idiv_mensal_pct=Decimal('0'), idiv_acumulado_pct=Decimal('0')
    )

def test_sharpe_calculation():
    engine = ApplicationFactory.get_financial_analytics_engine()
    history = PerformanceHistory(summary={}, points=[
        make_point(date(2020,1,1), '1000', '1000'),
        make_point(date(2021,1,1), '1500', '0'),
    ])
    res = engine.calculate_metrics(history)
    assert res.sharpe is not None
