from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

class ImportWarning(BaseModel):
    message: str
    row: Optional[int] = None

class ImportError(BaseModel):
    message: str
    row: Optional[int] = None

class ImportReport(BaseModel):
    source: str
    file_name: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    elapsed_ms: int = 0
    rows_read: int = 0
    rows_parsed: int = 0
    rows_normalized: int = 0
    rows_persisted: int = 0
    duplicates_detected: int = 0
    warnings: List[ImportWarning] = Field(default_factory=list)
    errors: List[ImportError] = Field(default_factory=list)
    success: bool = False
