from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.coach.coach_models import CoachDTO
from backend.domains.ai.coach.coach_service import AICoachService
from backend.domains.ai.coach.coach_repository import CoachRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/coach", tags=["Artificial Intelligence"])

def get_coach_service():
    provider = GeminiProvider()
    repository = CoachRepository()
    return AICoachService(provider, repository)

@router.get("", response_model=CoachDTO)
def get_financial_coach(
    db: Session = Depends(get_db_connection),
    service: AICoachService = Depends(get_coach_service)
):
    """
    Retorna o Plano de Ação Inteligente e personalizado gerado pelo Coach
    com base no perfil financeiro e nas observações do portfólio.
    """
    return service.get_financial_coach_plan(db)
