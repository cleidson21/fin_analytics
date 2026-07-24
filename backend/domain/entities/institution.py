from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class Institution:
    id: UUID
    name: str
    code: str
    type: str | None
    country: str
    logo_url: str | None
    created_at: datetime
