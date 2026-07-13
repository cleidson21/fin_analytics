from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class AllocationItem(BaseModel):
    name: str
    market_value: Decimal
    allocation_percent: Decimal

class AllocationDashboardDTO(BaseModel):
    by_class: List[AllocationItem]
    by_institution: List[AllocationItem]
    by_asset: List[AllocationItem]
    by_sector: List[AllocationItem]
    by_type: List[AllocationItem]

class PerformanceDashboardDTO(BaseModel):
    monthly_return: Decimal
    annual_return: Decimal
    accumulated_return: Decimal
    rolling_returns: Dict[str, Optional[Decimal]]
    benchmark_comparison: Dict[str, Decimal]

class RiskDashboardDTO(BaseModel):
    current_drawdown: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal
    volatility: Decimal
    beta: Decimal
    alpha: Decimal

class PortfolioDashboardDTO(BaseModel):
    # Resumo Geral
    current_wealth: Decimal
    invested_capital: Decimal
    unrealized_gain: Decimal
    unrealized_gain_percent: Decimal
    
    # Dividendos (proventos recebidos ao longo do tempo ou YOC, mas o WealthEngine ainda nao expoem isso diretamente
    # Entao pegaremos do history summary
    total_dividends: Decimal
    dividend_yield: Decimal
    
    # Retornos Avancados
    twr: Decimal
    mwr: Decimal
    
    # Risco 
    sharpe: Decimal
    sortino: Decimal
    max_drawdown: Decimal
    volatility: Decimal
    beta: Decimal
    alpha: Decimal
    tracking_error: Decimal
    information_ratio: Decimal
