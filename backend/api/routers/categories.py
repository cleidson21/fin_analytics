from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from backend.api.dependencies.auth import get_current_user
from backend.core.container import get_get_categories_use_case
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.category_response_dto import CategoryResponseDTO
from backend.application.use_cases.get_categories import GetCategoriesUseCase

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponseDTO])
async def get_categories(
    include_system: bool = Query(True),
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetCategoriesUseCase = Depends(get_get_categories_use_case)
):
    return await use_case.execute(include_system=include_system)
