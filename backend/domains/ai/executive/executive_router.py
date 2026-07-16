from fastapi import APIRouter, Depends
from typing import List
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.executive.executive_models import ExecutiveBriefDTO
from backend.domains.ai.executive.executive_service import AIExecutiveService
from backend.domains.ai.executive.executive_repository import ExecutiveRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/executive", tags=["Artificial Intelligence"])

def get_executive_service():
    provider = GeminiProvider()
    repository = ExecutiveRepository()
    return AIExecutiveService(provider, repository)

@router.get("/brief", response_model=ExecutiveBriefDTO)
def get_executive_brief(
    db: Session = Depends(get_db_connection),
    service: AIExecutiveService = Depends(get_executive_service)
):
    """
    Retorna o Executive Brief diário consolidado. Opcionalmente gera de forma
    síncrona (on demand) se não existir nenhum briefing para a carteira.
    """
    return service.get_executive_brief(db)
