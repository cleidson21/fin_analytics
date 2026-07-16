from pydantic import BaseModel
from typing import Any, Dict, Optional

class AIResponseDTO(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    model: str
    tokens: int
    latency: float

class AIHealthcheckDTO(BaseModel):
    provider: str
    model: str
    status: str
    response_time_ms: float
    availability: bool
