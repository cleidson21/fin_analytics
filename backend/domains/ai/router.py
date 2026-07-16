from fastapi import APIRouter
from backend.domains.ai.orchestration.ai_service import AIService
from backend.domains.ai.schemas import AIHealthcheckDTO

router = APIRouter(prefix="/ai", tags=["Artificial Intelligence"])
service = AIService()

@router.get("/health", response_model=AIHealthcheckDTO)
def get_ai_health():
    """
    Retorna o status de integridade do provedor Gemini.
    """
    return service.check_health()

from backend.domains.ai.advisor.advisor_router import router as advisor_router
from backend.domains.ai.insights.insight_router import router as insight_router
from backend.domains.ai.planning.planning_router import router as planning_router
from backend.domains.ai.executive.executive_router import router as executive_router
router.include_router(advisor_router)
router.include_router(insight_router)
router.include_router(planning_router)
router.include_router(executive_router)
