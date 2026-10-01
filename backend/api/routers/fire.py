"""Authenticated transient FIRE analysis endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.dependencies.planning import CurrentPlanningUser, PlanningReadSession
from backend.api.fire_errors import raise_fire_error
from backend.api.fire_mapping import (
    map_fire_analysis_request,
    map_fire_analysis_result,
)
from backend.application.dtos.fire_dto import (
    FireAnalysisRequestDTO,
    FireAnalysisResponseDTO,
)
from backend.application.services.fire_analysis_service import FireAnalysisService


router = APIRouter(prefix="/fire", tags=["FIRE"])


def get_fire_analysis_service() -> FireAnalysisService:
    """Provide one stateless FIRE application service per request."""

    return FireAnalysisService()


FireAnalysisServiceDependency = Annotated[
    FireAnalysisService,
    Depends(get_fire_analysis_service),
]


@router.post("/analysis", response_model=FireAnalysisResponseDTO)
async def analyze_fire(
    request: FireAnalysisRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    service: FireAnalysisServiceDependency,
) -> FireAnalysisResponseDTO:
    """Map one request through D2 without HTTP-side financial orchestration."""

    try:
        command = map_fire_analysis_request(request)
        result = service.analyze(command, db, current_user.id)
        return map_fire_analysis_result(result)
    except Exception as error:
        raise_fire_error(error)
