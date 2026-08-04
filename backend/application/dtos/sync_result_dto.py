from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class SyncResultDTO(BaseModel):
    """DTO de resultado de uma importação/sincronização. Retornado para o frontend."""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(..., description="'success' | 'partial' | 'failed'")
    imported: int = Field(0, description="Transações inseridas/atualizadas")
    skipped: int = Field(0, description="Transações ignoradas (duplicadas)")
    errors: int = Field(0, description="Registros com erro de conversão")
    accounts_synced: int = Field(0, description="Contas sincronizadas")
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
