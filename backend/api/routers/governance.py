from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.use_cases.governance import GetGovernanceDashboardUseCase, GetGovernanceImportsUseCase

router = APIRouter(prefix="/governance", tags=["Governance"])

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_governance_dashboard(
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    use_case = GetGovernanceDashboardUseCase(session)
    return await use_case.execute()

@router.get("/imports", response_model=Dict[str, Any])
async def get_governance_imports(
    limit: int = Query(10),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    use_case = GetGovernanceImportsUseCase(session)
    return await use_case.execute(limit=limit)
