from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies.database import get_db_session
from backend.api.dependencies.auth import get_current_user
from backend.core.container import get_get_accounts_use_case
from backend.application.queries.get_accounts import GetAccountsQuery
from backend.domain.enums.account_type import AccountType
from backend.domain.enums.provider_type import ProviderType
from backend.application.dtos.account_response_dto import AccountResponseDTO
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.use_cases.get_accounts import GetAccountsUseCase

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("", response_model=List[AccountResponseDTO])
async def get_accounts(
    type: Optional[AccountType] = Query(None),
    is_active: Optional[bool] = Query(None),
    provider: Optional[ProviderType] = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetAccountsUseCase = Depends(get_get_accounts_use_case)
):
    query = GetAccountsQuery(
        user_id=current_user.id,
        type=type,
        is_active=is_active,
        provider=provider
    )
    return await use_case.execute(query)
