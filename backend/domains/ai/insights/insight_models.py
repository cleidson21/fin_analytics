from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class InsightDTO(BaseModel):
    id: str
    insight_type: str
    severity: str
    title: str
    description: str
    recommendation: str
    source_tables: List[str]
    generated_at: str
    expires_at: Optional[str]
    dismissed: bool

class AIInsightGenerationResult(BaseModel):
    insights: List[InsightDTO]
