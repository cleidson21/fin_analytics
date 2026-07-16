from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ExecutiveBriefDTO(BaseModel):
    summary: str
    portfolio: Dict[str, Any]
    market: Dict[str, Any]
    insights: List[Dict[str, Any]]
    planning: Dict[str, Any]
    priorities: List[str]
    generated_at: str

class ExecutiveBriefRecord(BaseModel):
    id: str
    brief_date: str
    summary: str
    portfolio_summary: str
    market_summary: str
    insights_summary: str
    planning_summary: str
    risk_summary: str
    recommended_focus: str
    generated_at: str
    expires_at: Optional[str]
    cache_key: str
