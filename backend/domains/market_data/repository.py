import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.market_data.interfaces import AssetQuote

logger = logging.getLogger(__name__)

class MarketDataRepository:
    """
    Repository for persisting external market data (prices, dividends) into V3 schema.
    Table: asset_prices
    """
    def _resolve_asset_id(self, session: Session, ticker: str) -> Optional[str]:
        result = session.execute(
            text("SELECT id FROM assets WHERE ticker = :ticker LIMIT 1"),
            {"ticker": ticker}
        ).fetchone()
        if result:
            return result[0]
        return None

    def save_prices(self, session: Session, quotes: List[AssetQuote]) -> int:
        if not quotes:
            return 0
            
        query = text("""
            INSERT INTO asset_prices (
                asset_id, date, open_price, high_price, low_price, 
                close_price, adjusted_close_price, volume, currency, source, fetched_at
            ) VALUES (
                :asset_id, :date, :open_price, :high_price, :low_price,
                :close_price, :adjusted_close_price, :volume, :currency, :source, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            ) ON CONFLICT(asset_id, date) DO UPDATE SET
                open_price=excluded.open_price,
                high_price=excluded.high_price,
                low_price=excluded.low_price,
                close_price=excluded.close_price,
                adjusted_close_price=excluded.adjusted_close_price,
                volume=excluded.volume,
                fetched_at=excluded.fetched_at
        """)
        
        count = 0
        for quote in quotes:
            asset_id = self._resolve_asset_id(session, quote.ticker)
            if not asset_id:
                logger.warning(f"MarketDataRepository: Asset not found for ticker {quote.ticker}. Skipping save.")
                continue
                
            try:
                params = {
                    "asset_id": asset_id,
                    "date": quote.date.isoformat(),
                    "open_price": int(round(float(quote.open_price) * 100)) if quote.open_price else None,
                    "high_price": int(round(float(quote.high_price) * 100)) if quote.high_price else None,
                    "low_price": int(round(float(quote.low_price) * 100)) if quote.low_price else None,
                    "close_price": int(round(float(quote.close_price) * 100)),
                    "adjusted_close_price": int(round(float(quote.adjusted_close_price) * 100)) if quote.adjusted_close_price else None,
                    "volume": float(quote.volume) if quote.volume else None,
                    "currency": quote.currency,
                    "source": quote.source
                }
                session.execute(query, params)
                count += 1
            except Exception as e:
                logger.error(f"Failed to save price for {quote.ticker} on {quote.date}: {e}")
                
        session.commit()
        return count
