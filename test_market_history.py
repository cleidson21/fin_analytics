import pytest
from datetime import date
from decimal import Decimal
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.dto import TradeDTO, TradeType, PositionSnapshot

def test_market_history_integration():
    engine = PerformanceEngine()
    
    t1 = TradeDTO(
        ticker="PETR4",
        broker="XP",
        operation_type=TradeType.BUY,
        trade_date=date(2026, 1, 15),
        quantity=Decimal("100"),
        unit_price=Decimal("30.0"),
        total_value=Decimal("3000.0"),
        source="CEI",
        idempotency_hash="h1"
    )
    
    history = engine.generate_history(
        trades=[t1],
        snapshots=[],
        market_prices={},
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 28),
        granularity="month"
    )
    
    assert len(history.points) == 2
    
    pt_jan = history.points[0]
    # Check if real benchmarks from market service were injected
    assert pt_jan.ibov_mensal_pct == Decimal("1.2")
    assert pt_jan.cdi_mensal_pct == Decimal("0.9")
