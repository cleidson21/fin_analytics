from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TypedDict


class Source(str, Enum):
    NUBANK = "NUBANK"
    MYPROFIT = "MYPROFIT"
    MANUAL = "MANUAL"


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