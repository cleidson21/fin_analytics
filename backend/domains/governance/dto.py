from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# DTOs for the Governance Dashboard
class DashboardMetricsDTO(BaseModel):
    total_runs: int
    confirmed_runs: int
    pending_runs: int
    lines_inserted: int
    lines_updated: int
    lines_failed: int
    last_import: Optional[str] = None

class ImportRunItemDTO(BaseModel):
    id: str
    source_type: str
    file_name: str
    started_at: str
    status: str
    rows_read: int
    rows_inserted: int
    rows_failed: int

class ImportRunListResponseDTO(BaseModel):
    items: List[ImportRunItemDTO]
    total: int

# Generic Paginated Response
class PaginatedResponseDTO(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
