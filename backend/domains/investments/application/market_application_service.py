from datetime import date
from decimal import Decimal
from typing import List, Tuple
from backend.domains.investments.services.market_data_service import MarketDataService
from backend.domains.investments.services.historical_price_service import HistoricalPriceService
from backend.domains.investments.dto import MarketDataPoint

class MarketApplicationService:
    def __init__(self, market_data_service: MarketDataService, historical_price_service: HistoricalPriceService):
        self.market_data_service = market_data_service
        self.historical_price_service = historical_price_service

    def get_market_data(self, target_date: date) -> MarketDataPoint:
        return self.market_data_service.get_market_data(target_date)

    def get_historical_price(self, ticker: str, target_date: date) -> Decimal:
        val = self.historical_price_service.get_price_for_date(ticker, target_date)
        return val if val is not None else Decimal('0')
