from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.advisor.advisor_models import AdvisorRequestDTO, AdvisorResponseDTO
from backend.domains.ai.advisor.advisor_service import AIAdvisorService
from backend.domains.ai.advisor.advisor_repository import AdvisorRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/advisor", tags=["Artificial Intelligence"])

def get_advisor_service():
    provider = GeminiProvider()
    repository = AdvisorRepository()
    return AIAdvisorService(provider, repository)

@router.post("", response_model=AdvisorResponseDTO)
def ask_advisor(
    request: AdvisorRequestDTO,
    db: Session = Depends(get_db_connection),
    service: AIAdvisorService = Depends(get_advisor_service)
):
    """
    Endpoint para perguntas ao Assistente Financeiro Inteligente (Portfolio Advisor).
    A IA atua de forma consultiva em cima dos read models do sistema.
    """
    return service.answer_question(db, request)
