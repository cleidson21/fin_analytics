from typing import List, Optional, Any
from datetime import date
from fastapi import APIRouter, Depends, Query, BackgroundTasks

from backend.api.dependencies.auth import get_current_user
from backend.core.container import (
    get_categories_summary_use_case,
    get_dashboard_summary_v2_use_case,
    get_pierre_import_service,
    get_installments_use_case,
    get_subscriptions_use_case,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.transaction import CategoryBreakdownDTO, DashboardSummaryV2DTO
from backend.application.use_cases.transactions import GetCategoriesSummaryUseCase, GetDashboardSummaryV2UseCase
from backend.application.use_cases.get_installments import GetInstallmentsUseCase
from backend.application.use_cases.get_subscriptions import GetSubscriptionsUseCase
from backend.application.services.pierre_import_service import PierreImportService
from backend.application.dtos.sync_result_dto import SyncResultDTO

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary-v2", response_model=DashboardSummaryV2DTO)
async def get_dashboard_summary_v2(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetDashboardSummaryV2UseCase = Depends(get_dashboard_summary_v2_use_case)
):
    if not month:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"
    return await use_case.execute(month=month)

@router.get("/categories", response_model=List[CategoryBreakdownDTO])
async def get_categories_summary(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetCategoriesSummaryUseCase = Depends(get_categories_summary_use_case)
):
    if not month:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"
        
    return await use_case.execute(user_id=current_user.id, month=month)


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
    """Importa transações do Pierre Finance para o banco de dados local.

    - Requer autenticação JWT válida.
    - Operação idempotente: executar novamente não gera duplicatas.
    - `start_date` e `end_date` são opcionais; se omitidos, os últimos 90 dias serão importados.
    """
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
    """Retorna informações básicas sobre o estado atual da importação Pierre.

    Não há estado persistênte nesta versão; o endpoint serve para
    verificação de saúde da integração.
    """
    from backend.core.config import settings
    has_key = bool(settings.PIERRE_API_KEY)
    return {
        "pierre_configured": has_key,
        "message": "Pierre API key configurada" if has_key else "PIERRE_API_KEY não definida",
    }

@router.get("/installments", response_model=List[Any])
async def get_installments(
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetInstallmentsUseCase = Depends(get_installments_use_case)
):
    """Retorna os parcelamentos do usuário corrente."""
    return await use_case.execute(user_id=current_user.id)


@router.get("/subscriptions", response_model=List[Any])
async def get_subscriptions(
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetSubscriptionsUseCase = Depends(get_subscriptions_use_case)
):
    """Retorna as assinaturas do usuário corrente."""
    return await use_case.execute(user_id=current_user.id)

