"""
test_dashboard_contracts.py — Gate 10.5
Garante que nenhum DTO público utilizado pelo Frontend foi quebrado.
Estes testes valem como snapshot/contrato dos shapes esperados.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from decimal import Decimal
from datetime import date, datetime
from backend.domains.investments.dto import (
    PerformanceHistory,
    PerformanceHistoryPoint,
    ImportLogDTO,
    ReconciliationResult,
    ReconciliationStatus,
    ReconciliationRecommendation,
    MarketDataPoint,
)
from backend.domains.investments.engines.valuation_engine import ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthSummary
from backend.domains.investments.engines.performance_dto import PerformanceSummary, PerformanceMetrics


def test_performance_summary_contract():
    """PerformanceSummary deve ter todos os campos exigidos pelo frontend."""
    metrics = PerformanceMetrics(
        unrealized_gain=Decimal("2930"),
        realized_gain=Decimal("0"),
        total_gain=Decimal("2930"),
        dividends_received=Decimal("0"),
        total_return=Decimal("2930"),
        unrealized_return_pct=Decimal("14.65"),
        realized_return_pct=Decimal("0"),
        total_return_pct=Decimal("14.65"),
        yield_on_cost=Decimal("0"),
        cagr=Decimal("13.82"),
        annualized_return_pct=Decimal("13.82"),
        monthly_return_pct=Decimal("1.09"),
        daily_return_pct=Decimal("0.036"),
        mwr=Decimal("13.82"),
        twr=Decimal("0")
    )
    summary = PerformanceSummary(
        cost_basis=Decimal("20000"),
        market_value=Decimal("22930"),
        metrics=metrics,
        holding_days=365
    )
    # Verificar todos os campos que o hook usePerformanceData.ts usa
    assert hasattr(summary, "cost_basis")
    assert hasattr(summary, "market_value")
    assert hasattr(summary, "metrics")
    assert hasattr(summary.metrics, "unrealized_gain")
    assert hasattr(summary.metrics, "realized_gain")
    assert hasattr(summary.metrics, "total_gain")
    assert hasattr(summary.metrics, "dividends_received")
    assert hasattr(summary.metrics, "total_return")
    assert hasattr(summary.metrics, "unrealized_return_pct")
    assert hasattr(summary.metrics, "realized_return_pct")
    assert hasattr(summary.metrics, "total_return_pct")
    assert hasattr(summary.metrics, "yield_on_cost")
    assert hasattr(summary.metrics, "cagr")
    assert hasattr(summary.metrics, "annualized_return_pct")
    assert hasattr(summary.metrics, "monthly_return_pct")
    assert hasattr(summary.metrics, "daily_return_pct")
    assert hasattr(summary.metrics, "mwr")
    assert hasattr(summary.metrics, "twr")
    assert hasattr(summary, "holding_days")


def test_performance_history_contract():
    """PerformanceHistoryPoint deve ter todos os campos exigidos pelo useAlphaData.ts."""
    pt = PerformanceHistoryPoint(
        date="2025-12-31",
        month="Dec 2025",
        patrimonio="R$ 22,930.00",
        patrimonio_value=Decimal("22930.00"),
        compras="R$ 3,000.00",
        compras_value=Decimal("3000.00"),
        vendas="R$ 0.00",
        vendas_value=Decimal("0"),
        proventos="R$ 0.00",
        proventos_value=Decimal("0"),
        rentabilidade_mensal_pct=Decimal("1.2"),
        rentabilidade_acumulada_pct=Decimal("14.65"),
        ibov_mensal_pct=Decimal("4.68"),
        ibov_acumulado_pct=Decimal("20.48"),
        cdi_mensal_pct=Decimal("0.93"),
        cdi_acumulado_pct=Decimal("10.86"),
        ipca_mensal_pct=Decimal("0.25"),
        ipca_acumulado_pct=Decimal("3.63"),
        ifix_mensal_pct=Decimal("0.72"),
        ifix_acumulado_pct=Decimal("11.44"),
        sp500_mensal_pct=Decimal("0.88"),
        sp500_acumulado_pct=Decimal("14.49"),
        idiv_mensal_pct=Decimal("0.91"),
        idiv_acumulado_pct=Decimal("12.57")
    )

    # Verificar todos os campos que o PortfolioEvolutionPoint do frontend precisa
    required_fields = [
        "month", "patrimonio", "patrimonio_value",
        "compras", "compras_value", "vendas", "vendas_value",
        "proventos", "proventos_value",
        "rentabilidade_mensal_pct", "rentabilidade_acumulada_pct",
        "ibov_mensal_pct", "ibov_acumulado_pct",
        "cdi_mensal_pct", "cdi_acumulado_pct",
        "ipca_mensal_pct", "ipca_acumulado_pct",
        "ifix_mensal_pct", "ifix_acumulado_pct",
        "sp500_mensal_pct", "sp500_acumulado_pct",
        "idiv_mensal_pct", "idiv_acumulado_pct",
    ]
    for field in required_fields:
        assert hasattr(pt, field), f"Campo '{field}' ausente no PerformanceHistoryPoint"


def test_valuation_result_contract():
    """ValuationResult deve ter todos os campos exigidos pelo frontend."""
    val = ValuationResult(
        ticker="PETR4",
        institution="XP",
        quantity=Decimal("200"),
        cost_basis=Decimal("6300"),
        average_cost=Decimal("31.50"),
        current_price=Decimal("34.50"),
        market_value=Decimal("6900"),
        unrealized_gain=Decimal("600"),
        unrealized_gain_percent=Decimal("9.52")
    )
    assert hasattr(val, "ticker")
    assert hasattr(val, "institution")
    assert hasattr(val, "quantity")
    assert hasattr(val, "cost_basis")
    assert hasattr(val, "market_value")
    assert hasattr(val, "unrealized_gain")
    assert hasattr(val, "unrealized_gain_percent")


def test_import_log_dto_contract():
    """ImportLogDTO deve ter todos os campos exigidos pela tela de importação."""
    dto = ImportLogDTO(
        id="uuid-test-1",
        user_id="user-1",
        created_at=datetime.utcnow(),
        filename="trades.csv",
        file_type="CSV",
        file_size=2048,
        checksum="abc123",
        parser="CSVTradeParser",
        rows_read=10,
        rows_imported=8,
        rows_duplicated=2,
        rows_failed=0,
        processing_time_ms=150,
        status="SUCCESS"
    )
    assert hasattr(dto, "id")
    assert hasattr(dto, "checksum")
    assert hasattr(dto, "rows_imported")
    assert hasattr(dto, "rows_duplicated")
    assert hasattr(dto, "status")


def test_reconciliation_result_contract():
    """ReconciliationResult deve ter todos os campos de conciliação."""
    result = ReconciliationResult(
        ticker="PETR4",
        broker="XP",
        ledger_quantity=Decimal("200"),
        snapshot_quantity=Decimal("205"),
        difference=Decimal("5"),
        difference_percent=Decimal("2.5"),
        status=ReconciliationStatus.WARNING,
        recommendation=ReconciliationRecommendation.REVIEW_IMPORT
    )
    assert result.ticker == "PETR4"
    assert result.difference == Decimal("5")
    assert result.status == ReconciliationStatus.WARNING
