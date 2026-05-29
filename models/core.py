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