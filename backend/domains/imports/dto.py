from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class EventTypeEnum(str, Enum):
    """Event types for canonical financial events."""
    CASH_FLOW = "CASH_FLOW"
    TRADE = "TRADE"
    DIVIDEND = "DIVIDEND"
    CREDIT_EXPENSE = "CREDIT_EXPENSE"


class ImportStatusEnum(str, Enum):
    """Status lifecycle for imports."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLBACKED = "ROLLBACKED"


class ImportSource(str, Enum):
    """Fontes de importação de arquivos."""
    NUBANK_CONTA = "NUBANK_CONTA"
    NUBANK_FATURA = "NUBANK_FATURA"
    MYPROFIT_PROVENTOS = "MYPROFIT_PROVENTOS"
    MYPROFIT_EVOLUCAO = "MYPROFIT_EVOLUCAO"
    PIERRE = "PIERRE"
    B3 = "B3"


class RawDocument(BaseModel):
    """
    Representa qualquer documento bruto lido pelos Readers.
    Não contém regras financeiras.
    """
    source: str
    filename: str
    mime_type: str
    encoding: str
    parser_version: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Any
    document_hash: str
    created_at: datetime


class CanonicalFinancialEvent(BaseModel):
    """
    Representa o contrato universal do sistema.
    Base de toda a normalização.
    """
    source_system: str
    source_type: str
    event_type: EventTypeEnum
    transaction_date: date
    settlement_date: Optional[date] = None
    description: str
    normalized_description: str
    amount: Decimal
    currency: str
    asset: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    account: Optional[str] = None
    credit_card: Optional[str] = None
    broker: Optional[str] = None
    external_uuid: Optional[str] = None
    external_hash: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_structural_rules(self):
        """Validações estruturais obrigatórias do contrato."""
        if self.event_type == EventTypeEnum.TRADE:
            if not self.asset or self.quantity is None:
                raise ValueError("Eventos do tipo TRADE exigem 'asset' e 'quantity'.")
        
        if self.event_type == EventTypeEnum.CREDIT_EXPENSE:
            if not self.credit_card:
                raise ValueError("Eventos do tipo CREDIT_EXPENSE exigem 'credit_card'.")
        
        return self


class ImportSessionDTO(BaseModel):
    """
    Representa uma sessão de upload de arquivos.
    """
    session_id: str
    created_at: datetime
    user_id: str
    files: List[str]
    status: ImportStatusEnum


class ImportBatchDTO(BaseModel):
    """
    Representa um lote de documentos agrupados de uma sessão.
    """
    batch_id: str
    session_id: str
    documents: List[RawDocument]
    validation_status: ImportStatusEnum


class ImportRunStatistics(BaseModel):
    """
    Estatísticas atreladas a uma execução de importação.
    """
    total_processed: int = 0
    total_inserted: int = 0
    total_updated: int = 0
    total_ignored: int = 0
    total_errors: int = 0


class ImportRunDTO(BaseModel):
    """
    Representa uma execução de importação no Governance.
    """
    run_id: str
    batch_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    statistics: ImportRunStatistics = Field(default_factory=ImportRunStatistics)
    rollback_available: bool = True


class ImportAuditDTO(BaseModel):
    """
    Representa auditoria e estatísticas finas de inserções e conflitos.
    """
    run_id: str
    created: int
    updated: int
    ignored: int
    conflicts: int
    warnings: int
    errors: int
