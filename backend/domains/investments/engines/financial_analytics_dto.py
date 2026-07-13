from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel

class FinancialPerformanceDTO(BaseModel):
    twr: Decimal
    mwr: Decimal
    cagr: Decimal
    volatility: Decimal
    max_drawdown: Decimal
    current_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal
    alpha: Decimal
    beta: Decimal
    tracking_error: Decimal
    information_ratio: Decimal
    rolling_returns: Dict[str, Optional[Decimal]]  # '3m', '6m', '12m', '24m', 'inception'
    metadata: Dict[str, str]
