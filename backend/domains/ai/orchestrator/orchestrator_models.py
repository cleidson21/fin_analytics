from pydantic import BaseModel
from typing import Dict, Any, Optional

class OrchestratorStatusDTO(BaseModel):
    status: str
    modules: Dict[str, str]
    generated_at: str

class UnifiedContextDTO(BaseModel):
    profile: Optional[Dict[str, Any]] = None
    coach: Optional[Dict[str, Any]] = None
    executive: Optional[Dict[str, Any]] = None
    personalization: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    insights: Optional[Dict[str, Any]] = None
    planning: Optional[Dict[str, Any]] = None
    advisor_status: Optional[str] = None
    cache_key: str
