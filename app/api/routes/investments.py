from typing import List

from fastapi import APIRouter

from app.api.schemas.investments import AssetAllocation, DividendHistory, NetWorthEvolution
from app.core.formatters import format_money
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("/dividends/history", response_model=List[DividendHistory])
def get_dividend_history():
    """Retorna o histórico mensal de dividendos recebidos."""
    df = queries.get_dividend_history()
    if df.empty:
        return []

    records = df.to_dict(orient="records")

    return [
        DividendHistory(
            month=r["month"],
            amount_received=format_money(r["amount_received"]),
        )
        for r in records
    ]


@router.get("/allocation", response_model=List[AssetAllocation])
def get_portfolio_allocation():
    """Retorna a alocação atual do portfólio por classe de ativo."""
    df = queries.get_portfolio_allocation()
    if df.empty:
        return []

    records = df.to_dict(orient="records")

    return [
        AssetAllocation(
            asset_class=r["asset_class"],
            current_total=format_money(r["current_total"]),
        )
        for r in records
    ]


@router.get("/evolution", response_model=List[NetWorthEvolution])
def get_net_worth_evolution():
    """Retorna a evolução histórica do património (fecho de cada mês)."""
    df = queries.get_net_worth_history()
    if df.empty:
        return []

    records = df.to_dict(orient="records")

    return [
        NetWorthEvolution(
            month=r["month"],
            net_worth=format_money(r["net_worth"]),
        )
        for r in records
    ]