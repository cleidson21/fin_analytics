from pydantic import BaseModel
from typing import List, Optional

class MemoryDTO(BaseModel):
    investment_preferences: List[str]
    behavior_patterns: List[str]
    historical_strengths: List[str]
    historical_attention_points: List[str]
    confidence_score: float
    generated_at: str

class MemoryRecord(BaseModel):
    id: str
    memory_version: int
    investment_preferences: str # JSON array
    behavior_patterns: str # JSON array
    historical_strengths: str # JSON array
    historical_attention_points: str # JSON array
    recurring_goals: str # JSON array
    learning_summary: str
    confidence_score: float
    generated_at: str
    expires_at: Optional[str]
    cache_key: str
