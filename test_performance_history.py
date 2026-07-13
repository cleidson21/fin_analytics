import pytest
from datetime import date
from decimal import Decimal
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.dto import TradeDTO, TradeType, PositionSnapshot

def test_performance_history_generation():
    engine = PerformanceEngine()
    
    # Mock data
    t1 = TradeDTO(
        ticker="PETR4",
        broker="XP",
        operation_type=TradeType.BUY,
        trade_date=date(2026, 1, 15),
        quantity=Decimal("100"),
        unit_price=Decimal("30.0"),
        total_value=Decimal("3000.0"),
        source="CEI",
        idempotency_hash="hash1"
    )
    
    t2 = TradeDTO(
        ticker="PETR4",
        broker="XP",
        operation_type=TradeType.SELL,
        trade_date=date(2026, 2, 20),
        quantity=Decimal("50"),
        unit_price=Decimal("35.0"),
        total_value=Decimal("1750.0"),
        source="CEI",
        idempotency_hash="hash2"
    )
    
    s1 = PositionSnapshot(
        source_system="CEI",
        reference_date=date(2026, 1, 31),
        ticker="PETR4",
        asset_type="STOCK",
        institution="XP",
        quantity=Decimal("100"),
        snapshot_hash="s_hash1"
    )
    
    market_prices = {"PETR4": Decimal("35.0")}
    
    history = engine.generate_history(
        trades=[t1, t2],
        snapshots=[s1],
        market_prices=market_prices,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        granularity="month"
    )
    
    assert history is not None
    assert len(history.points) == 3 # Jan, Feb, Mar
    
    pt_jan = history.points[0]
    assert pt_jan.compras_value == Decimal("3000.0")
    assert pt_jan.vendas_value == Decimal("0.0")
    
    pt_feb = history.points[1]
    assert pt_feb.compras_value == Decimal("0.0")
    assert pt_feb.vendas_value == Decimal("1750.0")
    
    assert history.summary["patrimonio_atual"] > 0
