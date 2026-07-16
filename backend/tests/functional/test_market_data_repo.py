import unittest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.domains.market_data.interfaces import AssetQuote
from backend.domains.market_data.repository import MarketDataRepository

class TestMarketDataRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE assets (
                    id TEXT PRIMARY KEY,
                    ticker TEXT UNIQUE NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE asset_prices (
                    asset_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open_price INTEGER,
                    high_price INTEGER,
                    low_price INTEGER,
                    close_price INTEGER NOT NULL,
                    adjusted_close_price INTEGER,
                    volume REAL,
                    currency TEXT,
                    source TEXT,
                    fetched_at TEXT,
                    PRIMARY KEY (asset_id, date)
                )
            """))
            conn.execute(text("INSERT INTO assets (id, ticker) VALUES ('123', 'PETR4')"))
            
        self.repo = MarketDataRepository()

    def test_save_prices_upsert(self):
        with Session(self.engine) as session:
            quote1 = AssetQuote(
                ticker="PETR4",
                date=date(2026, 7, 15),
                close_price=Decimal("35.50"),
                source="YFINANCE"
            )
            # Insert new
            self.repo.save_prices(session, [quote1])
            
            result = session.execute(text("SELECT close_price FROM asset_prices WHERE asset_id='123'")).fetchone()
            self.assertEqual(result[0], 3550) # Stored as integer cents
            
            # Update existing (UPSERT)
            quote2 = AssetQuote(
                ticker="PETR4",
                date=date(2026, 7, 15),
                close_price=Decimal("36.00"),
                source="YFINANCE"
            )
            self.repo.save_prices(session, [quote2])
            
            result2 = session.execute(text("SELECT close_price FROM asset_prices WHERE asset_id='123'")).fetchall()
            self.assertEqual(len(result2), 1) # Still 1 row (No duplication)
            self.assertEqual(result2[0][0], 3600) # Updated correctly

if __name__ == '__main__':
    unittest.main()
