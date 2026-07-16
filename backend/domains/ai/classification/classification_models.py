from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class AIClassificationInput(BaseModel):
    description: str
    institution: str
    amount: float
    date: date
    history: Optional[str] = None
    # No sensitive fields allowed

class AIClassificationOutput(BaseModel):
    suggested_category: str
    confidence: float
    reason: str
    alternatives: List[str]

class AIClassificationRecord(BaseModel):
    id: Optional[str] = None
    transaction_hash: str
    prompt_hash: str
    suggested_category: str
    confidence: float
    accepted_by_user: Optional[bool] = None
    final_category: Optional[str] = None
    created_at: Optional[str] = None
