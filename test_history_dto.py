import pytest
from decimal import Decimal
from backend.domains.investments.dto import PerformanceHistoryPoint, PerformanceHistory

def test_performance_history_dto():
    pt = PerformanceHistoryPoint(
        date="2026-07-31",
        month="Jul 2026",
        patrimonio="R$ 10,000.00",
        patrimonio_value=Decimal("10000.0"),
        compras="R$ 1,000.00",
        compras_value=Decimal("1000.0"),
        vendas="R$ 0.00",
        vendas_value=Decimal("0"),
        proventos="R$ 50.00",
        proventos_value=Decimal("50.0"),
        rentabilidade_mensal_pct=Decimal("1.5"),
        rentabilidade_acumulada_pct=Decimal("15.0"),
        ibov_mensal_pct=Decimal("1.2"),
        ibov_acumulado_pct=Decimal("10.0"),
        cdi_mensal_pct=Decimal("0.9"),
        cdi_acumulado_pct=Decimal("9.0"),
        ipca_mensal_pct=Decimal("0.4"),
        ipca_acumulado_pct=Decimal("4.0"),
        ifix_mensal_pct=Decimal("0.5"),
        ifix_acumulado_pct=Decimal("5.0"),
        sp500_mensal_pct=Decimal("1.1"),
        sp500_acumulado_pct=Decimal("11.0"),
        idiv_mensal_pct=Decimal("1.0"),
        idiv_acumulado_pct=Decimal("10.0")
    )
    
    assert pt.patrimonio_value == Decimal("10000.0")
    assert pt.rentabilidade_mensal_pct == Decimal("1.5")
    
    history = PerformanceHistory(points=[pt], summary={"total": 1})
    assert len(history.points) == 1
    assert history.summary["total"] == 1
