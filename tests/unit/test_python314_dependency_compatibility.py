"""Synthetic canaries for the pandas/SQLAlchemy Python 3.14 reconciliation."""

from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import Column, Integer, MetaData, Numeric, Table, create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from backend.integrations.yfinance.yfinance_provider import YFinanceProvider


def _amounts_table():
    metadata = MetaData()
    table = Table(
        "synthetic_amounts", metadata,
        Column("id", Integer, primary_key=True),
        Column("amount", Numeric(18, 4), nullable=False),
    )
    return metadata, table


def test_sync_sqlite_preserves_decimal_and_rolls_back_uncommitted_write():
    metadata, table = _amounts_table()
    engine = create_engine("sqlite:///:memory:")
    try:
        metadata.create_all(engine)
        statement = table.insert().values(id=1, amount=Decimal("12.3400"))
        assert statement.compile(engine).params["amount"] == Decimal("12.3400")
        with Session(engine) as session:
            session.execute(statement)
            session.commit()
        with Session(engine) as session:
            amount = session.scalar(select(table.c.amount))
            assert isinstance(amount, Decimal)
            assert str(amount) == "12.3400"
            session.execute(table.insert().values(id=2, amount=Decimal("99.9900")))
            session.rollback()
        with Session(engine) as session:
            assert session.scalars(select(table.c.id)).all() == [1]
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_async_sqlite_preserves_decimal_and_rolls_back_uncommitted_write(tmp_path):
    metadata, table = _amounts_table()
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'synthetic.db').as_posix()}")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        factory = async_sessionmaker(engine)
        async with factory() as session:
            await session.execute(table.insert().values(id=1, amount=Decimal("12.3400")))
            await session.commit()
        async with factory() as session:
            amount = await session.scalar(select(table.c.amount))
            assert isinstance(amount, Decimal)
            assert str(amount) == "12.3400"
            await session.execute(table.insert().values(id=2, amount=Decimal("99.9900")))
            await session.rollback()
        async with factory() as session:
            assert (await session.scalars(select(table.c.id))).all() == [1]
    finally:
        await engine.dispose()


def test_pandas_history_preserves_dates_order_and_numeric_output(monkeypatch):
    history = pd.DataFrame(
        {"Open": [10.0, 11.0], "High": [12.0, 13.0], "Low": [9.0, 10.0],
         "Close": [11.0, 12.0], "Volume": [100, 200]},
        index=pd.to_datetime(["2026-01-02", "2026-01-05"], utc=True),
    )
    ticker = MagicMock()
    ticker.history.return_value = history
    ticker_factory = MagicMock(return_value=ticker)
    monkeypatch.setattr("backend.integrations.yfinance.yfinance_provider.yf.Ticker", ticker_factory)
    result = YFinanceProvider().get_history("SYNTH3", "STOCK", period="1mo")
    assert result == [
        {"date": "2026-01-02", "open": 10.0, "high": 12.0, "low": 9.0,
         "close": 11.0, "volume": 100},
        {"date": "2026-01-05", "open": 11.0, "high": 13.0, "low": 10.0,
         "close": 12.0, "volume": 200},
    ]
    assert all(type(row["volume"]) is int for row in result)
    ticker_factory.assert_called_once_with("SYNTH3.SA")
    ticker.history.assert_called_once_with(period="1mo")


def test_pandas_empty_history_preserves_unavailable_result(monkeypatch):
    ticker = MagicMock()
    ticker.history.return_value = pd.DataFrame()
    monkeypatch.setattr("backend.integrations.yfinance.yfinance_provider.yf.Ticker", lambda _: ticker)
    assert YFinanceProvider().get_history("SYNTH3", "STOCK") == []
