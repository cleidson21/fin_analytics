from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

class AssetTypeEnum(str, Enum):
    """Tipos de ativos suportados pelo consolidador patrimonial."""
    STOCK = "STOCK"
    FII = "FII"
    ETF = "ETF"
    BDR = "BDR"
    FIXED_INCOME = "FIXED_INCOME"
    TREASURY = "TREASURY"
    CRYPTO = "CRYPTO"
    FUNDS = "FUNDS"
    UNKNOWN = "UNKNOWN"

class PositionSnapshot(BaseModel):
    """
    Representa uma fotografia (estado patrimonial estático) de um ativo em uma data específica.
    Diferentemente do CanonicalFinancialEvent, esta entidade não registra fluxo de caixa ou
    transações, mas a custódia efetiva naquele instante do tempo.
    """
    source_system: str           # Ex: 'B3_AREA_INVESTIDOR', 'MYPROFIT'
    reference_date: date         # Data base do snapshot (ex: fechamento do pregão)
    ticker: str                  # Código do ativo (ex: 'PETR4', 'Tesouro IPCA')
    asset_type: AssetTypeEnum    # Classe do ativo
    institution: str             # Corretora, custodiante ou carteira (ex: 'NUBANK', 'XP')
    quantity: Decimal            # Quantidade exata detida na data base
    
    # Valores de precificação (dependentes da fonte)
    unit_price: Optional[Decimal] = None # Preço médio (MyProfit) ou preço de fechamento (B3)
    total_value: Optional[Decimal] = None # Valor patrimonial calculado (quantity * unit_price)
    
    # Hash de Identidade Arquitetural
    # A chave conceitual que garante idempotência: hash(reference_date + ticker + institution)
    # Se o sistema importar múltiplos arquivos ou fontes contendo a mesma custódia na mesma
    # data para a mesma corretora, o banco fará UPSERT (Merge) para não duplicar patrimônio.
    snapshot_hash: str           
    
    # Metadados e Rastreabilidade
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    INITIAL_POSITION = "INITIAL_POSITION"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    AMORTIZATION = "AMORTIZATION"
    SPLIT = "SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    BONUS_SHARE = "BONUS_SHARE"
    MERGER = "MERGER"

class TradeDTO(BaseModel):
    """
    Representa um evento canônico de negociação (Trade).
    """
    ticker: str
    broker: str
    operation_type: TradeType
    market_type: Optional[str] = None
    expiration_date: Optional[date] = None
    trade_date: date
    quantity: Decimal
    unit_price: Decimal
    total_value: Decimal
    source: str
    idempotency_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReconciliationStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"

class ReconciliationRecommendation(str, Enum):
    NO_ACTION = "Sem ação"
    REVIEW_IMPORT = "Revisar importação"
    UPDATE_SNAPSHOT = "Atualizar snapshot"
    CHECK_CUSTODY = "Conferir custódia"

class ReconciliationResult(BaseModel):
    ticker: str
    broker: str
    ledger_quantity: Decimal
    snapshot_quantity: Decimal
    difference: Decimal
    difference_percent: Decimal
    status: ReconciliationStatus
    recommendation: ReconciliationRecommendation

class ImportLogDTO(BaseModel):
    """
    Representa o registro histórico permanente e auditável de uma importação (Gate 10.2).
    """
    id: str
    user_id: str
    created_at: datetime
    filename: str
    file_type: str
    file_size: int
    checksum: str
    parser: str
    rows_read: int
    rows_imported: int
    rows_duplicated: int
    rows_failed: int
    processing_time_ms: int
    status: str
    error_message: Optional[str] = None
    metadata_json: Optional[str] = None


class PerformanceHistoryPoint(BaseModel):
    date: str
    month: str
    patrimonio: str
    patrimonio_value: Decimal
    compras: str
    compras_value: Decimal
    vendas: str
    vendas_value: Decimal
    proventos: str
    proventos_value: Decimal
    rentabilidade_mensal_pct: Decimal
    rentabilidade_acumulada_pct: Decimal
    ibov_mensal_pct: Decimal
    ibov_acumulado_pct: Decimal
    cdi_mensal_pct: Decimal
    cdi_acumulado_pct: Decimal
    ipca_mensal_pct: Decimal
    ipca_acumulado_pct: Decimal
    ifix_mensal_pct: Decimal
    ifix_acumulado_pct: Decimal
    sp500_mensal_pct: Decimal
    sp500_acumulado_pct: Decimal
    idiv_mensal_pct: Decimal
    idiv_acumulado_pct: Decimal

class PerformanceHistory(BaseModel):
    points: list[PerformanceHistoryPoint]
    summary: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MarketDataPoint(BaseModel):
    date: date
    ibov: Decimal
    cdi: Decimal
    ifix: Decimal
    ipca: Decimal
    sp500: Decimal
    idiv: Decimal

class MarketSeries(BaseModel):
    points: list[MarketDataPoint]


class MessageResponse(BaseModel):
    message: str

from typing import Generic, TypeVar, List
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

class PortfolioEvolutionSummary(BaseModel):
    current_wealth: Decimal
    total_invested: Decimal
    total_dividends: Decimal
    accumulated_return_pct: Decimal

class DividendHistoryDTO(BaseModel):
    id_economico: str
    ticker: str
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    valor: Optional[Decimal] = None
    data_pagamento: Optional[str] = None

class DividendBreakdownDTO(BaseModel):
    ticker: str
    total_received: Decimal

