from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

@dataclass(kw_only=True)
class Category:
    id: UUID = field(default_factory=uuid4)
    name: str
    slug: str
    is_system: bool
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
