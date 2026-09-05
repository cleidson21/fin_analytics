from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

@dataclass
class MarketQuote:
    """
    Representa uma cotação de mercado obtida de um provider externo.
    """
    provider: str
    source_ticker: str
    price: Decimal
    price_date: Optional[datetime]
    timestamp: datetime
    is_stale: bool = False
