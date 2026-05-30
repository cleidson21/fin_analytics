from pathlib import Path

from fastapi import APIRouter

from app.api.schemas.catalog import CatalogResponse
from database.queries import FinancialQueries
from services.categorizer import SmartCategorizer
from taxonomy.categories import Natureza


router = APIRouter()
queries = FinancialQueries()
categorizer = SmartCategorizer(Path(__file__).resolve().parents[3] / "taxonomy" / "rules.csv")


@router.get("", response_model=CatalogResponse)
def get_catalog():
    """Retorna listas canónicas de categorias, naturezas e contas."""
    accounts_df = queries.get_account_catalog()
    accounts = accounts_df["account"].dropna().tolist() if not accounts_df.empty else []

    return CatalogResponse(
        categories=categorizer.available_categories(),
        natures=[nature.value for nature in Natureza],
        accounts=accounts,
    )