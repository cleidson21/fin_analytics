from backend.domains.investments.application_factory import ApplicationFactory
"""
test_full_pipeline.py — Gate 10.5
Teste de integração end-to-end do pipeline completo:
    TradeDTO → PositionEngine → ValuationEngine → WealthEngine → PerformanceEngine → MarketDataEngine
"""
import sys
import os
from datetime import date
from decimal import Decimal

# Adicionar raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.domains.investments.dto import (
    TradeDTO, TradeType, PositionSnapshot, AssetTypeEnum
)
from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.repositories.market_data_repository import MarketDataRepository
from backend.domains.investments.services.market_data_service import MarketDataService


# === MASSA DE DADOS ===

def _make_trade(ticker, op, trade_date, qty, price, source="TEST", broker="XP"):
    total = qty * price
    return TradeDTO(
        ticker=ticker,
        broker=broker,
        operation_type=op,
        trade_date=trade_date,
        quantity=Decimal(str(qty)),
        unit_price=Decimal(str(price)),
        total_value=Decimal(str(total)),
        source=source,
        idempotency_hash=f"h_{ticker}_{trade_date}_{op}"
    )


SAMPLE_TRADES = [
    _make_trade("PETR4", TradeType.BUY, date(2025, 1, 10), 100, 30.00),
    _make_trade("VALE3", TradeType.BUY, date(2025, 1, 15), 50, 80.00),
    _make_trade("MXRF11", TradeType.BUY, date(2025, 2, 5), 200, 10.50),
    _make_trade("PETR4", TradeType.BUY, date(2025, 3, 12), 50, 32.00),
    _make_trade("VALE3", TradeType.SELL, date(2025, 4, 20), 20, 88.00),
    _make_trade("PETR4", TradeType.SELL, date(2025, 6, 15), 30, 35.00),
    _make_trade("KNRI11", TradeType.BUY, date(2025, 7, 8), 60, 140.00),
    _make_trade("VALE3", TradeType.BUY, date(2025, 8, 22), 30, 85.00),
    _make_trade("PETR4", TradeType.BUY, date(2025, 10, 1), 80, 33.50),
]

MARKET_PRICES = {
    "PETR4": Decimal("34.50"),
    "VALE3": Decimal("86.50"),
    "MXRF11": Decimal("11.30"),
    "KNRI11": Decimal("143.00"),
}


# === TESTES ===

def test_position_engine_pipeline():
    """Posição correta após sequência de trades com compras e vendas."""
    engine = PositionEngine()
    positions = engine.calculate_position(SAMPLE_TRADES, [])

    petr4 = next((p for p in positions if p.ticker == "PETR4"), None)
    assert petr4 is not None
    assert petr4.quantity == Decimal("200")  # 100 + 50 - 30 + 80

    vale3 = next((p for p in positions if p.ticker == "VALE3"), None)
    assert vale3 is not None
    assert vale3.quantity == Decimal("60")  # 50 - 20 + 30

    mxrf11 = next((p for p in positions if p.ticker == "MXRF11"), None)
    assert mxrf11 is not None
    assert mxrf11.quantity == Decimal("200")


def test_valuation_engine_pipeline():
    """Valuation marca a mercado corretamente com preços reais."""
    pos_engine = PositionEngine()
    val_engine = ApplicationFactory.get_valuation_engine()

    positions = pos_engine.calculate_position(SAMPLE_TRADES, [])
    valuations = val_engine.calculate_valuation(positions, MARKET_PRICES)

    petr4_val = next((v for v in valuations if v.ticker == "PETR4"), None)
    assert petr4_val is not None
    # 200 shares * 34.50 = 6900
    assert petr4_val.market_value == Decimal("6900.00")
    assert petr4_val.quantity == Decimal("200")


def test_wealth_engine_pipeline():
    """WealthEngine consolida corretamente o patrimônio total."""
    pos_engine = PositionEngine()
    val_engine = ApplicationFactory.get_valuation_engine()
    wealth_engine = WealthEngine()

    positions = pos_engine.calculate_position(SAMPLE_TRADES, [])
    valuations = val_engine.calculate_valuation(positions, MARKET_PRICES)
    wealth = wealth_engine.calculate(valuations)

    assert wealth.total_market_value > Decimal("0")
    assert wealth.asset_count >= 4
    assert wealth.total_cost_basis > Decimal("0")

    # Total esperado: PETR4 6900 + VALE3 5190 + MXRF11 2260 + KNRI11 8580 = 22930
    assert wealth.total_market_value == Decimal("6900.00") + Decimal("5190.00") + Decimal("2260.00") + Decimal("8580.00")


def test_performance_engine_pipeline():
    """PerformanceEngine calcula métricas corretas sobre o portfólio consolidado."""
    pos_engine = PositionEngine()
    val_engine = ApplicationFactory.get_valuation_engine()
    wealth_engine = WealthEngine()
    perf_engine = PerformanceEngine()

    positions = pos_engine.calculate_position(SAMPLE_TRADES, [])
    valuations = val_engine.calculate_valuation(positions, MARKET_PRICES)
    wealth = wealth_engine.calculate(valuations)

    summary = perf_engine.calculate(
        cost_basis=wealth.total_cost_basis,
        market_value=wealth.total_market_value,
        realized_gain=Decimal("0"),
        dividends_received=Decimal("0"),
        start_date=date(2025, 1, 10),
        end_date=date(2025, 12, 31)
    )

    assert summary.cost_basis == wealth.total_cost_basis
    assert summary.market_value == wealth.total_market_value
    assert summary.metrics is not None
    assert summary.holding_days > 0


def test_market_data_pipeline():
    """MarketDataService fornece benchmarks reais para uma data específica."""
    service = ApplicationFactory.get_market_data_service()
    pt = service.get_market_data(date(2026, 1, 15))

    assert pt.date == date(2026, 1, 15)
    assert isinstance(pt.ibov, Decimal)
    assert isinstance(pt.cdi, Decimal)


def test_generate_history_pipeline():
    """Valida a integração HistoryService."""
    from backend.domains.investments.services.history_service import HistoryService
    
    history_service = ApplicationFactory.get_history_service()

    history = history_service.generate_history(
        trades=SAMPLE_TRADES,
        snapshots=[],
        market_prices=MARKET_PRICES,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        granularity="month"
    )

    assert len(history.points) == 12
    assert history.summary["patrimonio_atual"] > 0

    # Janeiro deve ter compras (PETR4 e VALE3 comprados em jan)
    jan = history.points[0]
    assert jan.compras_value > Decimal("0")

    # Verificar que benchmarks são Decimals
    assert isinstance(jan.ibov_mensal_pct, Decimal)
    assert isinstance(jan.cdi_mensal_pct, Decimal)

    # Acumulado do último ponto deve ser maior que o primeiro
    last = history.points[-1]
    assert last.ibov_acumulado_pct > Decimal("0")


def test_position_with_snapshot_reconciliation():
    """PositionEngine reconcilia posição de Ledger com Snapshot de custódia."""
    snap = PositionSnapshot(
        source_system="B3",
        reference_date=date(2025, 12, 31),
        ticker="PETR4",
        asset_type=AssetTypeEnum.STOCK,
        institution="XP",
        quantity=Decimal("205"),  # Diferença de 5 vs ledger (200)
        snapshot_hash="snap_petr4"
    )

    engine = PositionEngine()
    positions = engine.calculate_position(SAMPLE_TRADES, [snap])
    petr4 = next((p for p in positions if p.ticker == "PETR4"), None)

    assert petr4 is not None
    assert petr4.snapshot_quantity == Decimal("205")
    assert petr4.divergence_quantity == Decimal("5")  # 205 - 200
