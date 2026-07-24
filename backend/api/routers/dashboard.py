from typing import List
from datetime import date
from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.auth import get_current_user
from backend.core.container import get_categories_summary_use_case, get_dashboard_summary_v2_use_case
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.transaction import CategoryBreakdownDTO, DashboardSummaryV2DTO
from backend.application.use_cases.transactions import GetCategoriesSummaryUseCase, GetDashboardSummaryV2UseCase

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
