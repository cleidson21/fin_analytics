from pydantic import BaseModel
from typing import List, Optional

class ProfileDTO(BaseModel):
    profile: str
    investment_style: str
    strengths: List[str]
    attention_points: List[str]
    generated_at: str

class ProfileRecord(BaseModel):
    id: str
    profile_version: int
    investor_profile: str
    risk_tolerance: str
    investment_style: str
    portfolio_maturity: str
    diversification_score: str
    cash_behavior: str
    dividend_focus: str
    consistency_score: str
    planning_score: str
    macro_sensitivity: str
    behavior_summary: str
    strengths: str # JSON array
    attention_points: str # JSON array
    generated_at: str
    expires_at: Optional[str]
    cache_key: str
