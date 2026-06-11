from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, TypedDict


class Source(str, Enum):
    # ── Legado ──────────────────────────────────────────────────
    NUBANK   = "NUBANK"       # CSV legado (compatibilidade com imports antigos)
    MYPROFIT = "MYPROFIT"
    PIERRE   = "PIERRE"
    MANUAL   = "MANUAL"

    # ── ETL v2 (Sprint 4.4) ─────────────────────────────────────
    NUBANK_CONTA  = "NUBANK_CONTA"   # CSV extrato conta corrente
    NUBANK_FATURA = "NUBANK_FATURA"  # CSV fatura cartão de crédito
    NUBANK_PDF    = "NUBANK_PDF"     # PDF investimentos Nubank


class EventType(str, Enum):
    """Tipo canônico de evento financeiro no pipeline ETL v2."""
    TRANSACTION   = "TRANSACTION"    # débito/crédito em conta corrente
    POSITION      = "POSITION"       # snapshot de carteira (MyProfit)
    DIVIDEND      = "DIVIDEND"       # provento recebido
    INVOICE       = "INVOICE"        # lançamento em fatura de cartão de crédito
    PORTFOLIO_EVO = "PORTFOLIO_EVO"  # evolução patrimonial mensal


class PipelineStatus(str, Enum):
    """Estágio atual de um RawFinancialEvent no pipeline."""
    RAW        = "RAW"
    NORMALIZED = "NORMALIZED"
    MATCHED    = "MATCHED"
    RECONCILED = "RECONCILED"
    CLASSIFIED = "CLASSIFIED"
    PROMOTED   = "PROMOTED"


class MatchStatus(str, Enum):
    """Resultado do EventMatcher para um evento."""
    NEW               = "NEW"
    DUPLICATE         = "DUPLICATE"
    CROSS_SOURCE_MATCH = "CROSS_SOURCE_MATCH"
    CONFLICT          = "CONFLICT"


class RuleType(str, Enum):
    """Tipos de regras aprendidas na Memória Financeira."""
    CATEGORIZATION       = "CATEGORIZATION"
    RECONCILIATION       = "RECONCILIATION"
    TICKER_TRANSLATION   = "TICKER_TRANSLATION"
    DIVIDEND_TRANSLATION = "DIVIDEND_TRANSLATION"
    NEGATIVE_MATCH       = "NEGATIVE_MATCH"
    FEEDBACK             = "FEEDBACK"

class ClassificationSource(str, Enum):
    RULE = "RULE"
    HEURISTIC = "HEURISTIC"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    OPENFINANCE = "OPENFINANCE"


# ─────────────────────────────────────────────────────────────────────────────
# Modelos legados — mantidos para compatibilidade com parsers existentes
# ─────────────────────────────────────────────────────────────────────────────

class CanonicalTransaction(TypedDict):
    id_economico: str
    source: Source
    data: date
    descricao_original: str
    descricao_normalizada: str
    valor: Decimal
    identificador_externo: str


class CanonicalPosition(TypedDict):
    source: Source
    data_snapshot: date
    ticker: str
    quantidade: Decimal
    preco_medio: Decimal
    total_investido: Decimal
    preco_atual: Decimal
    total_atual: Decimal
    ganho: Decimal


class CanonicalEvent(TypedDict):
    id_economico: str
    source: Source
    tipo_evento: str
    ticker: str
    data_pagamento: date
    valor_liquido: Decimal


class CanonicalPortfolioEvolution(TypedDict):
    source: Source
    reference_month: date
    rentabilidade_mensal_pct: Decimal
    rentabilidade_acumulada_pct: Decimal
    patrimonio_cents: int
    compras_cents: int
    vendas_cents: int
    op_finalizadas_cents: int
    proventos_cents: int
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


# ─────────────────────────────────────────────────────────────────────────────
# Modelo ETL v2 — RawFinancialEvent universal
# ─────────────────────────────────────────────────────────────────────────────

class RawFinancialEvent(TypedDict):
    """
    Modelo universal do pipeline ETL v2.
    Representa qualquer evento financeiro de qualquer fonte,
    antes de ser promovido para as tabelas finais.
    """
    # ── Identificação ────────────────────────────────────────────
    id:              str            # UUID v4
    event_type:      EventType
    source:          str            # Source enum value
    import_run_id:   str
    source_line_no:  int | None
    raw_content:     str | None     # linha bruta original (auditoria)

    # ── Dados temporais ──────────────────────────────────────────
    event_date:      date | None
    reference_month: date | None    # para PORTFOLIO_EVO

    # ── Financeiros ──────────────────────────────────────────────
    amount_cents:    int | None
    currency:        str            # 'BRL'

    # ── Fingerprints de deduplicação ─────────────────────────────
    semantic_id:     str            # SHA-256 intra-source (determinístico)
    cross_fingerprint: str | None   # SHA-256 cross-source (sem campo source)
    external_id:     str | None     # id externo da fonte (ex: Nubank "Identificador")

    # ── Metadados livres por fonte ───────────────────────────────
    metadata:        dict[str, Any]
    # Exemplos:
    #   POSITION: {"ticker": "VGIR11", "quantidade": "100", "preco_medio": "9.85", ...}
    #   DIVIDEND: {"ticker": "VGIR11", "tipo_evento": "DIVIDENDO"}
    #   INVOICE:  {"title": "Mercado Livre", "installment": "1/3"}

    # ── Status do pipeline ───────────────────────────────────────
    pipeline_status: str            # PipelineStatus enum value
    match_status:    str            # MatchStatus enum value

    # ── Resultado da promoção ────────────────────────────────────
    promoted_entity_id: str | None
    promoted_table:     str | None



class CanonicalTransaction(TypedDict):
    id_economico: str
    source: Source
    data: date
    descricao_original: str
    descricao_normalizada: str
    valor: Decimal
    identificador_externo: str


class CanonicalPosition(TypedDict):
    source: Source
    data_snapshot: date
    ticker: str
    quantidade: Decimal
    preco_medio: Decimal
    total_investido: Decimal
    preco_atual: Decimal
    total_atual: Decimal
    ganho: Decimal


class CanonicalEvent(TypedDict):
    id_economico: str
    source: Source
    tipo_evento: str
    ticker: str
    data_pagamento: date
    valor_liquido: Decimal


class CanonicalPortfolioEvolution(TypedDict):
    source: Source
    reference_month: date
    rentabilidade_mensal_pct: Decimal
    rentabilidade_acumulada_pct: Decimal
    patrimonio_cents: int
    compras_cents: int
    vendas_cents: int
    op_finalizadas_cents: int
    proventos_cents: int
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