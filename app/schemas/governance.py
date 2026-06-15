from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImportRunBase(BaseModel):
    source_type: str = 'PIERRE'
    file_name: str
    status: str = 'PENDING'

class ImportRunResponse(ImportRunBase):
    id: str
    started_at: datetime
    class Config:
        from_attributes = True

class RawEventBase(BaseModel):
    source: str
    event_type: str
    semantic_id: str

class RawEventResponse(RawEventBase):
    id: str
    import_run_id: str
    class Config:
        from_attributes = True
