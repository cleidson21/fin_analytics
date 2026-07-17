from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    source: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
