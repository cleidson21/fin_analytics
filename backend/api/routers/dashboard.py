from datetime import date
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.auth import get_current_user
from backend.core.container import (
    get_categories_summary_use_case,
    get_pierre_import_service,
    get_installments_use_case,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.transaction import CategoryBreakdownDTO
from backend.application.use_cases.transactions import GetCategoriesSummaryUseCase
from backend.application.use_cases.get_installments import GetInstallmentsUseCase
from backend.application.services.pierre_import_service import PierreImportService
from backend.application.dtos.sync_result_dto import SyncResultDTO

# GovernedFinancialQuery e SessionLocal importados de forma lazy
# (dentro de cada endpoint) para evitar conflito de MetaData no reload do uvicorn.

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _current_month() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


@router.get("/summary-v2")
def get_dashboard_summary_v2(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    KPIs do Dashboard: receitas, despesas, saldo_líquido, patrimônio.

    Usa somente transações CLASSIFIED da camada Pierre/governança.
    Retorna variação percentual vs mês anterior.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    from backend.database.session import SessionLocal
    q = GovernedFinancialQuery()
    db = SessionLocal()
    try:
        result = q.get_monthly_kpis(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/pacing-v2")
def get_dashboard_pacing_v2(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Ritmo de Gastos diário — gráfico de linha mês atual vs mês anterior.

    Retorna gastos (SAIDA CLASSIFIED) dia a dia e totais para comparação.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    from backend.database.session import SessionLocal
    q = GovernedFinancialQuery()
    db = SessionLocal()
    try:
        result = q.get_pacing_data(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/heatmap")
def get_dashboard_heatmap(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Mapa de Calor de gastos diários.

    Retorna todos os dias do mês com valor total (SAIDA CLASSIFIED)
    e intensidade normalizada 0–1 para coloração do grid.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    from backend.database.session import SessionLocal
    q = GovernedFinancialQuery()
    db = SessionLocal()
    try:
        result = q.get_heatmap_data(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/categories", response_model=List[CategoryBreakdownDTO])
def get_categories_summary(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Retorna o breakdown de gastos por categoria para o Dashboard e Página de Categorias.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    from backend.database.session import SessionLocal
    
    q = GovernedFinancialQuery()
    db = SessionLocal()
    try:
        result = q.get_categories_breakdown(db, month=month)
        db.expunge_all()
    finally:
        db.close()
        
    return result


@router.post("/import-pierre", response_model=SyncResultDTO)
async def import_pierre_data(
    start_date: Optional[date] = Query(
        None,
        description="Data de início da importação (YYYY-MM-DD). Padrão: hoje − 90 dias.",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Data de fim da importação (YYYY-MM-DD). Padrão: hoje.",
    ),
    current_user: UserResponseDTO = Depends(get_current_user),
    service: PierreImportService = Depends(get_pierre_import_service),
):
    """Importa transações do Pierre Finance para o banco de dados local."""
    result = await service.import_transactions(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return result


@router.get("/import-status", response_model=dict)
async def get_import_status(
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Retorna informações básicas sobre o estado atual da importação Pierre."""
    from backend.core.config import settings
    has_key = bool(settings.PIERRE_API_KEY)
    return {
        "pierre_configured": has_key,
        "message": "Pierre API key configurada" if has_key else "PIERRE_API_KEY não definida",
    }



