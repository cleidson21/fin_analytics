from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class CategoryResponseDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    is_system: bool
    icon: Optional[str] = None
    color: Optional[str] = None
