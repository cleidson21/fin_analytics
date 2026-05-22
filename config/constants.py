"""Immutable business constants for fin_analytics.

This module contains values that represent business rules and do not belong to
runtime configuration.
"""

from __future__ import annotations

from enum import Enum, unique
from typing import Final


@unique
class TipoTransacao(str, Enum):
	"""Canonical transaction types used across the application."""

	RECEITA = "RECEITA"
	GASTO = "GASTO"
	INVESTIMENTO = "INVESTIMENTO"
	TRANSFERENCIA = "TRANSFERENCIA"


TIPOS_TRANSACAO: Final[tuple[str, ...]] = tuple(member.value for member in TipoTransacao)
"""Ordered tuple with all supported transaction types."""


@unique
class CategoriaPadrao(str, Enum):
	"""Default business categories used for transaction classification."""

	ALIMENTACAO = "ALIMENTACAO"
	TRANSPORTE = "TRANSPORTE"
	MORADIA = "MORADIA"
	SAUDE = "SAUDE"
	LAZER = "LAZER"
	VESTUARIO = "VESTUARIO"
	ASSINATURAS = "ASSINATURAS"
	INVESTIMENTOS = "INVESTIMENTOS"
	TRANSFERENCIAS = "TRANSFERENCIAS"
	RECEITA = "RECEITA"
	OUTROS = "OUTROS"


CATEGORIAS_PADRAO: Final[tuple[str, ...]] = tuple(member.value for member in CategoriaPadrao)
"""Ordered tuple with the default category taxonomy."""


@unique
class SubcategoriaPadrao(str, Enum):
	"""Second-level categories used by the ingestion and reporting layers."""

	MERCADO = "MERCADO"
	DELIVERY = "DELIVERY"
	RESTAURANTE = "RESTAURANTE"
	COMBUSTIVEL = "COMBUSTIVEL"
	MANUTENCAO_VEICULO = "MANUTENCAO_VEICULO"
	TRANSPORTE_APP = "TRANSPORTE_APP"
	ALUGUEL = "ALUGUEL"
	CONDOMINIO = "CONDOMINIO"
	UTILIDADES = "UTILIDADES"
	FARMACIA = "FARMACIA"
	CONSULTA = "CONSULTA"
	CUIDADOS_PESSOAIS = "CUIDADOS_PESSOAIS"
	ENTRETENIMENTO = "ENTRETENIMENTO"
	VIAGEM = "VIAGEM"
	PRESENTES = "PRESENTES"
	ROUPAS = "ROUPAS"
	CALCADOS = "CALCADOS"
	ACESSORIOS = "ACESSORIOS"
	STREAMING = "STREAMING"
	INTERNET = "INTERNET"
	CELULAR = "CELULAR"
	RENDA_FIXA = "RENDA_FIXA"
	FII = "FII"
	ACOES_BR = "ACOES_BR"
	ACOES_EXT = "ACOES_EXT"
	ETF = "ETF"
	CRIPTOATIVOS = "CRIPTOATIVOS"
	ENTRE_CONTAS = "ENTRE_CONTAS"
	ECOMMERCE = "ECOMMERCE"
	SALARIO = "SALARIO"
	DIVIDENDOS = "DIVIDENDOS"
	PROVENTOS_FII = "PROVENTOS_FII"
	FREELANCE = "FREELANCE"
	OUTRAS_RECEITAS = "OUTRAS_RECEITAS"
	DIVERSO = "DIVERSO"


SUBCATEGORIAS_PADRAO: Final[tuple[str, ...]] = tuple(
	member.value for member in SubcategoriaPadrao
)
"""Ordered tuple with the default subcategory taxonomy."""


TIPO_POR_CATEGORIA: Final[dict[CategoriaPadrao, TipoTransacao]] = {
	CategoriaPadrao.ALIMENTACAO: TipoTransacao.GASTO,
	CategoriaPadrao.TRANSPORTE: TipoTransacao.GASTO,
	CategoriaPadrao.MORADIA: TipoTransacao.GASTO,
	CategoriaPadrao.SAUDE: TipoTransacao.GASTO,
	CategoriaPadrao.LAZER: TipoTransacao.GASTO,
	CategoriaPadrao.VESTUARIO: TipoTransacao.GASTO,
	CategoriaPadrao.ASSINATURAS: TipoTransacao.GASTO,
	CategoriaPadrao.INVESTIMENTOS: TipoTransacao.INVESTIMENTO,
	CategoriaPadrao.TRANSFERENCIAS: TipoTransacao.TRANSFERENCIA,
	CategoriaPadrao.RECEITA: TipoTransacao.RECEITA,
	CategoriaPadrao.OUTROS: TipoTransacao.GASTO,
}
"""Maps each category to its default transaction type."""


SUBCATEGORIA_PARENT: Final[dict[SubcategoriaPadrao, CategoriaPadrao]] = {
	SubcategoriaPadrao.MERCADO: CategoriaPadrao.ALIMENTACAO,
	SubcategoriaPadrao.DELIVERY: CategoriaPadrao.ALIMENTACAO,
	SubcategoriaPadrao.RESTAURANTE: CategoriaPadrao.ALIMENTACAO,
	SubcategoriaPadrao.COMBUSTIVEL: CategoriaPadrao.TRANSPORTE,
	SubcategoriaPadrao.MANUTENCAO_VEICULO: CategoriaPadrao.TRANSPORTE,
	SubcategoriaPadrao.TRANSPORTE_APP: CategoriaPadrao.TRANSPORTE,
	SubcategoriaPadrao.ALUGUEL: CategoriaPadrao.MORADIA,
	SubcategoriaPadrao.CONDOMINIO: CategoriaPadrao.MORADIA,
	SubcategoriaPadrao.UTILIDADES: CategoriaPadrao.MORADIA,
	SubcategoriaPadrao.FARMACIA: CategoriaPadrao.SAUDE,
	SubcategoriaPadrao.CONSULTA: CategoriaPadrao.SAUDE,
	SubcategoriaPadrao.CUIDADOS_PESSOAIS: CategoriaPadrao.SAUDE,
	SubcategoriaPadrao.ENTRETENIMENTO: CategoriaPadrao.LAZER,
	SubcategoriaPadrao.VIAGEM: CategoriaPadrao.LAZER,
	SubcategoriaPadrao.PRESENTES: CategoriaPadrao.LAZER,
	SubcategoriaPadrao.ROUPAS: CategoriaPadrao.VESTUARIO,
	SubcategoriaPadrao.CALCADOS: CategoriaPadrao.VESTUARIO,
	SubcategoriaPadrao.ACESSORIOS: CategoriaPadrao.VESTUARIO,
	SubcategoriaPadrao.STREAMING: CategoriaPadrao.ASSINATURAS,
	SubcategoriaPadrao.INTERNET: CategoriaPadrao.ASSINATURAS,
	SubcategoriaPadrao.CELULAR: CategoriaPadrao.ASSINATURAS,
	SubcategoriaPadrao.RENDA_FIXA: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.FII: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.ACOES_BR: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.ACOES_EXT: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.ETF: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.CRIPTOATIVOS: CategoriaPadrao.INVESTIMENTOS,
	SubcategoriaPadrao.ENTRE_CONTAS: CategoriaPadrao.TRANSFERENCIAS,
	SubcategoriaPadrao.ECOMMERCE: CategoriaPadrao.OUTROS,
	SubcategoriaPadrao.SALARIO: CategoriaPadrao.RECEITA,
	SubcategoriaPadrao.DIVIDENDOS: CategoriaPadrao.RECEITA,
	SubcategoriaPadrao.PROVENTOS_FII: CategoriaPadrao.RECEITA,
	SubcategoriaPadrao.FREELANCE: CategoriaPadrao.RECEITA,
	SubcategoriaPadrao.OUTRAS_RECEITAS: CategoriaPadrao.RECEITA,
	SubcategoriaPadrao.DIVERSO: CategoriaPadrao.OUTROS,
}
"""Maps each subcategory to its parent category."""
