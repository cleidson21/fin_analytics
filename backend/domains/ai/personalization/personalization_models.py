from pydantic import BaseModel
from typing import List, Optional

class PersonalizationDTO(BaseModel):
    communication_style: str
    detail_level: str
    priority_topics: List[str]
    dashboard_focus: List[str]
    preferred_frequency: str
    generated_at: str

class PersonalizationRecord(BaseModel):
    id: str
    personalization_version: int
    communication_style: str
    detail_level: str
    priority_topics: str # JSON array
    preferred_frequency: str
    dashboard_focus: str # JSON array
    notification_preferences: str # JSON array
    learning_preferences: str # JSON array
    language_profile: str
    summary_preferences: str
    generated_at: str
    expires_at: Optional[str]
    cache_key: str
