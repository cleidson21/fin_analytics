from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DatabaseSummary(BaseModel):
    total_transactions: int
    total_positions: int
    total_dividends: int
    total_evolutions: int
    total_import_runs: int
    runs_confirmed: int
    runs_pending: int

class TableStatus(BaseModel):
    table_name: str
    row_count: int
    status: str

class DatabaseHealth(BaseModel):
    database: str
    imports: str
    wealth: str
    staging: str

class DatabaseIntegrity(BaseModel):
    orphan_runs: int
    pending_staging: int
    duplicate_transactions_suspects: int

class VacuumEstimate(BaseModel):
    size_current_kb: float
    estimated_post_vacuum_kb: float

class VacuumResult(BaseModel):
    size_before_kb: float
    size_after_kb: float
    freed_space_kb: float

class AuditRun(BaseModel):
    id: str
    file_name: str
    source_type: str
    started_at: datetime
    status: str
    created_by: Optional[str]
    rows_read: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int

class AuditRollback(BaseModel):
    id: str
    file_name: str
    rollback_timestamp: Optional[datetime]
    rollback_user: Optional[str]
    rollback_reason: Optional[str]
    started_at: datetime

class AuditLogResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    changed_by: Optional[str]
    created_at: datetime

class AuditLogDetailResponse(AuditLogResponse):
    field_changes: Optional[str]
    created_at: datetime

class TransactionUpdateRequest(BaseModel):
    descricao_normalizada: Optional[str] = None
    macro_categoria: Optional[str] = None
    sub_categoria: Optional[str] = None
    subnatureza: Optional[str] = None
    natureza: Optional[str] = None
    parcelamento: Optional[str] = None
    observacao: Optional[str] = None

class PositionUpdateRequest(BaseModel):
    classe_ativo: Optional[str] = None
    ticker: Optional[str] = None
    observacao: Optional[str] = None

class DividendUpdateRequest(BaseModel):
    ticker: Optional[str] = None
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None

class CategoryMergeRequest(BaseModel):
    source_category: str
    target_category: str
