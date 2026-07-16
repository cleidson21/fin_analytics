from fastapi import APIRouter, Depends
from typing import List
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.insights.insight_models import InsightDTO
from backend.domains.ai.insights.insight_service import AIInsightService
from backend.domains.ai.insights.insight_repository import InsightRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/insights", tags=["Artificial Intelligence"])

def get_insight_service():
    provider = GeminiProvider()
    repository = InsightRepository()
    return AIInsightService(provider, repository)

@router.get("", response_model=List[InsightDTO])
def get_insights(
    db: Session = Depends(get_db_connection),
    service: AIInsightService = Depends(get_insight_service)
):
    """
    Lista os Insights e Alertas Financeiros gerados proativamente pela IA.
    """
    return service.get_insights(db)
