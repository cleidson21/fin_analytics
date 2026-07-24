from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class InstitutionSummaryDTO(BaseModel):
    id: UUID
    name: str
    code: str
    logo_url: Optional[str] = None
