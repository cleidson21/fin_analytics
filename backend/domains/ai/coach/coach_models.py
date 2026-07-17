from pydantic import BaseModel
from typing import List, Optional

class CoachDTO(BaseModel):
    weekly_focus: str
    monthly_focus: str
    priority_actions: List[str]
    recommended_habits: List[str]
    generated_at: str

class CoachRecord(BaseModel):
    id: str
    coach_version: int
    action_plan: str
    weekly_focus: str
    monthly_focus: str
    recommended_habits: str # JSON array
    priority_actions: str # JSON array
    portfolio_observations: str
    risk_observations: str
    planning_observations: str
    generated_at: str
    expires_at: Optional[str]
    cache_key: str
