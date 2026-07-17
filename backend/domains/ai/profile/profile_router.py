from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.profile.profile_models import ProfileDTO
from backend.domains.ai.profile.profile_service import AIProfileService
from backend.domains.ai.profile.profile_repository import ProfileRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/profile", tags=["Artificial Intelligence"])

def get_profile_service():
    provider = GeminiProvider()
    repository = ProfileRepository()
    return AIProfileService(provider, repository)

@router.get("", response_model=ProfileDTO)
def get_financial_profile(
    db: Session = Depends(get_db_connection),
    service: AIProfileService = Depends(get_profile_service)
):
    """
    Retorna o Perfil Financeiro do Investidor gerado autonomamente
    com base no histórico comportamental.
    """
    return service.get_financial_profile(db)
