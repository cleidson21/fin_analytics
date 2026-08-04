from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

@dataclass(kw_only=True)
class Tag:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    name: str
    color: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
