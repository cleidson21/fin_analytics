"""Governance enums for transaction classification and processing state."""

from __future__ import annotations

from enum import Enum, unique


@unique
class TipoTransacao(str, Enum):
    """Canonical transaction types used across the application."""

    RECEITA = "RECEITA"
    GASTO = "GASTO"
    INVESTIMENTO = "INVESTIMENTO"
    TRANSFERENCIA = "TRANSFERENCIA"
    REVISAO_MANUAL = "REVISAO_MANUAL"


@unique
class CategoriaFallback(str, Enum):
    """Fallback categories used when a transaction cannot be classified."""

    NAO_CLASSIFICADO = "NAO_CLASSIFICADO"
    OUTROS = "OUTROS"


@unique
class FonteDados(str, Enum):
    """Supported data sources for ingestion and lineage tracking."""

    NUBANK = "NUBANK"
    MYPROFIT = "MYPROFIT"
    MANUAL = "MANUAL"
    SISTEMA = "SISTEMA"


@unique
class StatusProcessamento(str, Enum):
    """Processing status values for ETL and governance flows."""

    SUCESSO = "SUCESSO"
    ERRO = "ERRO"
    QUARENTENA = "QUARENTENA"
    IGNORADO = "IGNORADO"


@unique
class ClasseAtivo(str, Enum):
    """Supported asset classes for the wealth layer."""

    ACAO_BR = "ACAO_BR"
    FII = "FII"
    ETF_EUA = "ETF_EUA"
    CRIPTO = "CRIPTO"
    RENDA_FIXA = "RENDA_FIXA"
    CAIXA = "CAIXA"


@unique
class StatusMeta(str, Enum):
    """Lifecycle states for financial goals."""

    ATIVA = "ATIVA"
    CONCLUIDA = "CONCLUIDA"
    PAUSADA = "PAUSADA"
