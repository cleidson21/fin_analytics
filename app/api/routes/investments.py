from typing import List

from fastapi import APIRouter

from app.api.schemas.investments import (
    AssetAllocation,
    DividendBreakdown,
    DividendHistory,
    NetWorthEvolution,
    PositionDetail,
    PortfolioEvolutionPoint,
    PortfolioEvolutionSummary,
)
from app.api.services.wealth import WealthAnalyticsService


router = APIRouter()
wealth_service = WealthAnalyticsService()


@router.get("/dividends/history", response_model=List[DividendHistory])
def get_dividend_history():
    """Retorna o histórico mensal de dividendos recebidos."""
    return wealth_service.get_dividend_history()


@router.get("/allocation", response_model=List[AssetAllocation])
def get_portfolio_allocation():
    """Retorna a alocação atual do portfólio por classe de ativo."""
    return wealth_service.get_portfolio_allocation()


@router.get("/evolution", response_model=List[NetWorthEvolution])
def get_net_worth_evolution():
    """Retorna a evolução histórica do património (fecho de cada mês)."""
    return wealth_service.get_net_worth_evolution()


@router.get("/positions", response_model=List[PositionDetail])
def get_detailed_positions():
    """Retorna posições detalhadas do último snapshot disponível."""
    return wealth_service.get_detailed_positions()


@router.get("/dividends/breakdown", response_model=List[DividendBreakdown])
def get_dividends_breakdown():
    """Retorna o detalhamento histórico de dividendos agrupado por ativo."""
    return wealth_service.get_dividends_by_asset()


@router.get("/evolution/history", response_model=List[PortfolioEvolutionPoint])
def get_portfolio_evolution_history():
    """Retorna o histórico detalhado de evolução da carteira (compras, vendas, rentabilidade)."""
    return wealth_service.get_portfolio_evolution_history()


@router.get("/evolution/summary", response_model=PortfolioEvolutionSummary)
def get_portfolio_evolution_summary():
    """Retorna os KPIs consolidados da evolução da carteira."""
    return wealth_service.get_portfolio_evolution_summary()

@router.get("/asset/{ticker}")
def get_asset_details(ticker: str):
    """Retorna todas as informações consolidadas de um ativo (Asset Detail)."""
    return wealth_service.get_asset_details(ticker)