from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.personalization.personalization_models import PersonalizationDTO
from backend.domains.ai.personalization.personalization_service import AIPersonalizationService
from backend.domains.ai.personalization.personalization_repository import PersonalizationRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/personalization", tags=["Artificial Intelligence"])

def get_personalization_service():
    provider = GeminiProvider()
    repository = PersonalizationRepository()
    return AIPersonalizationService(provider, repository)

@router.get("", response_model=PersonalizationDTO)
def get_ai_personalization(
    db: Session = Depends(get_db_connection),
    service: AIPersonalizationService = Depends(get_personalization_service)
):
    """
    Retorna as preferências ideais de experiência de usuário e interface
    baseadas no perfil comportamental (DNA) do investidor.
    """
    return service.get_personalization(db)
