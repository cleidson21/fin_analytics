"""
test_performance_benchmark.py — Gate 10.5
Benchmark de performance das Engines sob diferentes volumes de trades.
Mede tempo de execução, uso de RAM e complexidade observada.
"""
import sys
import os
import time
import tracemalloc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from datetime import date
from decimal import Decimal

from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine
from backend.domains.investments.engines.performance_engine import PerformanceEngine


def _generate_trades(n: int):
    tickers = ["PETR4", "VALE3", "MXRF11", "KNRI11", "ITUB4"]
    trades = []
    for i in range(n):
        ticker = tickers[i % len(tickers)]
        op = TradeType.BUY if i % 5 != 4 else TradeType.SELL
        d = date(2020 + (i // 1000), ((i // 83) % 12) + 1, (i % 28) + 1)
        trades.append(TradeDTO(
            ticker=ticker,
            broker="XP",
            operation_type=op,
            trade_date=d,
            quantity=Decimal("10"),
            unit_price=Decimal("30.00"),
            total_value=Decimal("300.00"),
            source="BENCH",
            idempotency_hash=f"h_{i}"
        ))
    return trades


def _run_bench(n: int):
    trades = _generate_trades(n)
    market_prices = {
        "PETR4": Decimal("35.0"),
        "VALE3": Decimal("87.0"),
        "MXRF11": Decimal("11.5"),
        "KNRI11": Decimal("144.0"),
        "ITUB4": Decimal("26.0"),
    }

    tracemalloc.start()
    t0 = time.perf_counter()

    pos_engine = PositionEngine()
    positions = pos_engine.calculate_position(trades, [])

    val_engine = ValuationEngine()
    valuations = val_engine.calculate_valuation(positions, market_prices)

    wealth_engine = WealthEngine()
    wealth = wealth_engine.calculate(valuations)

    perf_engine = PerformanceEngine()
    summary = perf_engine.calculate(
        cost_basis=wealth.total_cost_basis,
        market_value=wealth.total_market_value,
        realized_gain=Decimal("0"),
        dividends_received=Decimal("0"),
        start_date=date(2020, 1, 1),
        end_date=date(2025, 12, 31)
    )

    elapsed = (time.perf_counter() - t0) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "trades": n,
        "time_ms": round(elapsed, 2),
        "peak_ram_kb": round(peak / 1024, 2),
        "positions": len(positions),
        "wealth": float(wealth.total_market_value),
    }


def test_benchmark_10():
    result = _run_bench(10)
    assert result["time_ms"] < 5000
    print(f"\n[Benchmark 10 trades] {result}")


def test_benchmark_100():
    result = _run_bench(100)
    assert result["time_ms"] < 5000
    print(f"\n[Benchmark 100 trades] {result}")


def test_benchmark_1000():
    result = _run_bench(1000)
    assert result["time_ms"] < 10000
    print(f"\n[Benchmark 1000 trades] {result}")


def test_benchmark_10000():
    result = _run_bench(10000)
    assert result["time_ms"] < 30000
    print(f"\n[Benchmark 10000 trades] {result}")
