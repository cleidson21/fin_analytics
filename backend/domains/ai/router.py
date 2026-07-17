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
from backend.domains.ai.profile.profile_router import router as profile_router
from backend.domains.ai.coach.coach_router import router as coach_router
from backend.domains.ai.memory.memory_router import router as memory_router
from backend.domains.ai.personalization.personalization_router import router as personalization_router
from backend.domains.ai.orchestrator.orchestrator_router import router as orchestrator_router
from backend.domains.ai.workflow.workflow_router import router as workflow_router
router.include_router(advisor_router)
router.include_router(insight_router)
router.include_router(planning_router)
router.include_router(executive_router)
router.include_router(profile_router)
router.include_router(coach_router)
router.include_router(memory_router)
router.include_router(personalization_router)
router.include_router(orchestrator_router)
router.include_router(workflow_router)
