from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class AllocationItem(BaseModel):
    name: str
    market_value: Decimal
    allocation_percent: Decimal

class AllocationDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "by_asset": [{"ticker": "PETR4", "percentage": 25.0}],
                "by_class": [{"asset_class": "STOCK", "percentage": 60.0}],
                "by_institution": [{"institution": "XP", "percentage": 100.0}]
            }
        }
    }
    by_class: List[AllocationItem]
    by_institution: List[AllocationItem]
    by_asset: List[AllocationItem]
    by_sector: List[AllocationItem]
    by_type: List[AllocationItem]

class PerformanceDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "monthly_return": 1.2,
                "annual_return": 14.5,
                "benchmark_comparison": {"ibov": 0.8},
                "rolling_returns": {"12m": 12.0}
            }
        }
    }
    monthly_return: Decimal
    annual_return: Decimal
    accumulated_return: Decimal
    rolling_returns: Dict[str, Optional[Decimal]]
    benchmark_comparison: Dict[str, Decimal]

class RiskDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "volatility": 15.2,
                "current_drawdown": -2.1,
                "sharpe": 1.2,
                "sortino": 1.5,
                "beta": 0.9
            }
        }
    }
    current_drawdown: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal
    volatility: Decimal
    beta: Decimal
    alpha: Decimal

class PortfolioDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_wealth": 22930.00,
                "unrealized_gain": 2930.00,
                "unrealized_gain_percent": 14.65,
                "twr": 12.5,
                "mwr": 13.82,
                "sharpe": 1.2,
                "max_drawdown": -5.4
            }
        }
    }
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

class DashboardFullDTO(BaseModel):
    summary: PortfolioDashboardDTO
    allocation: AllocationDashboardDTO
    performance: PerformanceDashboardDTO
    risk: RiskDashboardDTO
