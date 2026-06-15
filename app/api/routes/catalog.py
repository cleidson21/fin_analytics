from pathlib import Path

from fastapi import APIRouter

from app.api.schemas.catalog import CatalogResponse
from app.api.services.financial_service import FinancialService
from services.categorizer import SmartCategorizer
from taxonomy.categories import Natureza


router = APIRouter()
service = FinancialService()
categorizer = SmartCategorizer(Path(__file__).resolve().parents[3] / "taxonomy" / "rules.csv")


@router.get("", response_model=CatalogResponse)
def get_catalog():
    """Retorna listas canónicas de categorias, naturezas e contas."""
    accounts = service.get_account_catalog()

    return CatalogResponse(
        categories=categorizer.available_categories(),
        natures=[nature.value for nature in Natureza],
        accounts=accounts,
    )