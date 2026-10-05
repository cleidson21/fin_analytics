from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.dependencies.profile_context import (
    CurrentProfileUser,
    ProfileContextSession,
)
from backend.api.profile_context_errors import raise_profile_context_error
from backend.api.profile_context_mapping import map_profile_context_response
from backend.application.dtos.profile_context_dto import (
    ProfileDeclaredContextPatchDTO,
    ProfileDeclaredContextResponseDTO,
)
from backend.application.services.profile_declared_context_service import (
    ProfileDeclaredContextService,
)


router = APIRouter(prefix="/profile", tags=["Profile"])


def get_profile_declared_context_service() -> ProfileDeclaredContextService:
    return ProfileDeclaredContextService()


ProfileDeclaredContextServiceDependency = Annotated[
    ProfileDeclaredContextService,
    Depends(get_profile_declared_context_service),
]


@router.get("/context", response_model=ProfileDeclaredContextResponseDTO)
def get_profile_declared_context(
    current_user: CurrentProfileUser,
    db: ProfileContextSession,
    service: ProfileDeclaredContextServiceDependency,
) -> ProfileDeclaredContextResponseDTO:
    try:
        context = service.get_context(db, current_user.id)
        return map_profile_context_response(current_user, context)
    except Exception as error:
        raise_profile_context_error(error)


@router.patch("/context", response_model=ProfileDeclaredContextResponseDTO)
def update_profile_declared_context(
    request: ProfileDeclaredContextPatchDTO,
    current_user: CurrentProfileUser,
    db: ProfileContextSession,
    service: ProfileDeclaredContextServiceDependency,
) -> ProfileDeclaredContextResponseDTO:
    try:
        context = service.update_context(
            db,
            current_user.id,
            declared_monthly_gross_income=request.declared_monthly_gross_income,
            income_as_of_date=request.income_as_of_date,
        )
        return map_profile_context_response(current_user, context)
    except Exception as error:
        raise_profile_context_error(error)
