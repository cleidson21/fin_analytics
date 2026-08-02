import sys
import os
import time
import tracemalloc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from datetime import date
from decimal import Decimal
from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.services.history_service import HistoryService

def _generate_trades(n: int, months: int):
    tickers = ["PETR4", "VALE3", "MXRF11", "KNRI11", "ITUB4"]
    trades = []
    
    start_year = 2020
    # Distribui N trades ao longo de `months` meses
    for i in range(n):
        ticker = tickers[i % len(tickers)]
        op = TradeType.BUY if i % 5 != 4 else TradeType.SELL
        
        m_offset = i % months
        y = start_year + (m_offset // 12)
        m = (m_offset % 12) + 1
        d = (i % 28) + 1
        
        trades.append(TradeDTO(
            ticker=ticker,
            broker="XP",
            operation_type=op,
            trade_date=date(y, m, d),
            quantity=Decimal("10"),
            unit_price=Decimal("30.00"),
            total_value=Decimal("300.00"),
            source="BENCH",
            idempotency_hash=f"h_{i}"
        ))
    return trades

def _run_bench(n: int, months: int):
    trades = _generate_trades(n, months)
    market_prices = {
        "PETR4": Decimal("35.0"),
        "VALE3": Decimal("87.0"),
        "MXRF11": Decimal("11.5"),
        "KNRI11": Decimal("144.0"),
        "ITUB4": Decimal("26.0"),
    }

    start_d = date(2020, 1, 1)
    end_d = date(2020 + (months // 12), (months % 12) + 1 if months % 12 != 0 else 12, 28)

    tracemalloc.start()
    t0 = time.perf_counter()

    from backend.domains.investments.engines.position_engine import PositionEngine
    from backend.domains.investments.engines.valuation_engine import ValuationEngine
    from backend.domains.investments.engines.wealth_engine import WealthEngine
    from backend.domains.investments.services.market_data_service import MarketDataService
    from backend.domains.investments.repositories.market_data_repository import MarketDataRepository
    
    pe = PositionEngine()
    ve = ValuationEngine()
    we = WealthEngine()
    
    mdr = MarketDataRepository()
    mds = MarketDataService(mdr)
    
    service = HistoryService(pe, ve, we, mds)
    history = service.generate_history(
        trades=trades,
        snapshots=[],
        market_prices=market_prices,
        start_date=start_d,
        end_date=end_d,
        granularity="month"
    )

    elapsed = (time.perf_counter() - t0) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "trades": n,
        "months": months,
        "time_ms": round(elapsed, 2),
        "peak_ram_kb": round(peak / 1024, 2),
        "points": len(history.points),
    }

def test_scalability_100():
    res = _run_bench(100, 12)
    assert res["time_ms"] < 1000
    print(f"\n[Bench Incremental 100 trades, 12 meses] {res}")

def test_scalability_1000():
    res = _run_bench(1000, 60)
    assert res["time_ms"] < 2000
    print(f"\n[Bench Incremental 1000 trades, 60 meses] {res}")

def test_scalability_10000():
    res = _run_bench(10000, 120)
    assert res["time_ms"] < 10000
    print(f"\n[Bench Incremental 10000 trades, 120 meses] {res}")
