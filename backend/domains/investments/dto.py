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
