from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.memory.memory_models import MemoryDTO
from backend.domains.ai.memory.memory_service import AIMemoryService
from backend.domains.ai.memory.memory_repository import MemoryRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/memory", tags=["Artificial Intelligence"])

def get_memory_service():
    provider = GeminiProvider()
    repository = MemoryRepository()
    return AIMemoryService(provider, repository)

@router.get("", response_model=MemoryDTO)
def get_financial_memory(
    db: Session = Depends(get_db_connection),
    service: AIMemoryService = Depends(get_memory_service)
):
    """
    Retorna a Memória Financeira (DNA Histórico) do Investidor gerada a partir
    dos comportamentos passados ao longo do tempo.
    """
    return service.get_financial_memory(db)
