from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class DashboardViewModelDTO(BaseModel):
    summary: Dict[str, Any]
    portfolio: Dict[str, Any]
    insights: List[Dict[str, Any]]
    priorities: List[str]
    planning: Dict[str, Any]
    coach: Dict[str, Any]
    profile: Dict[str, Any]
    personalization: Dict[str, Any]
    status: str
    generated_at: str
    cache_key: str
