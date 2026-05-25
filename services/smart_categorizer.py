"""Smart fuzzy categorization for financial transaction descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Mapping

from config.constants import CategoriaFallback, TipoTransacao
from models.wealth_schemas import CategoriaDimDTO
from rapidfuzz import fuzz, process
from repositories.wealth_repository import WealthRepository
from utils.normalization import normalize_text


DEFAULT_ALIASES: Final[dict[str, str]] = {
	"PGTO IFOOD": "IFOOD",
	"IFOOD BURGER": "IFOOD",
	"IFOOD*BURGER": "IFOOD",
	"UBER DO BRASIL": "UBER",
	"UBER *TRIP": "UBER",
	"UBER TRIP": "UBER",
	"MERCADO PAGO": "SUPERMERCADO",
	"NETFLIX": "STREAMING",
	"SPOTIFY": "STREAMING",
	"AMAZON PRIME": "STREAMING",
	"APORTE B3": "APORTE",
	"BOLSA APORTE": "APORTE",
}


@dataclass(frozen=True, slots=True)
class _CategoryChoice:
	"""Internal fuzzy-search choice keyed by normalized subcategory."""

	key: str
	dto: CategoriaDimDTO


class SmartCategorizer:
	"""Fuzzy, repository-backed classifier for financial descriptions."""

	def __init__(
		self,
		repository: WealthRepository | None = None,
		*,
		aliases: Mapping[str, str] | None = None,
		threshold: int = 85,
	) -> None:
		try:
			self._repository = repository or WealthRepository(read_only=True)
		except Exception:
			self._repository = None
		self._threshold = threshold
		self._aliases = self._build_alias_index(aliases or DEFAULT_ALIASES)
		self._category_choices: list[_CategoryChoice] = []
		self._subcategory_lookup: dict[str, CategoriaDimDTO] = {}
		self.refresh()

	def refresh(self) -> None:
		"""Reload categories from DuckDB."""

		categories = self._repository.fetch_categories() if self._repository is not None else self._fallback_categories()
		choices: list[_CategoryChoice] = []
		lookup: dict[str, CategoriaDimDTO] = {}
		for category in categories:
			choice_key = self._clean_text(category.subcategoria)
			if not choice_key:
				continue
			lookup.setdefault(choice_key, category)
			choices.append(_CategoryChoice(key=choice_key, dto=category))

		self._subcategory_lookup = lookup
		self._category_choices = choices

	def categorize_transaction(self, descricao: str) -> CategoriaDimDTO:
		"""Map a raw description to the closest financial category."""

		cleaned = self._clean_text(descricao)
		if not cleaned:
			return self._fallback_category()

		alias_key = self._aliases.get(cleaned)
		if alias_key:
			resolved = self._subcategory_lookup.get(alias_key)
			if resolved is not None:
				return resolved

		exact_match = self._subcategory_lookup.get(cleaned)
		if exact_match is not None:
			return exact_match

		if not self._category_choices:
			return self._fallback_category()

		choice = process.extractOne(
			cleaned,
			[_choice.key for _choice in self._category_choices],
			scorer=fuzz.WRatio,
			processor=None,
			score_cutoff=self._threshold,
		)
		if choice is None:
			return self._fallback_category()

		matched_key = str(choice[0])
		resolved = self._subcategory_lookup.get(matched_key)
		if resolved is not None:
			return resolved

		return self._fallback_category()

	def categorize(self, descricao: str) -> tuple[CategoriaDimDTO, TipoTransacao | str]:
		"""Compatibility alias for older call sites."""

		categoria = self.categorize_transaction(descricao)
		if self._is_fallback(categoria):
			return categoria, TipoTransacao.REVISAO_MANUAL
		return categoria, TipoTransacao.GASTO

	@staticmethod
	def _build_alias_index(raw_aliases: Mapping[str, str]) -> dict[str, str]:
		"""Normalize aliases into lookup keys."""

		return {
			SmartCategorizer._clean_text(alias): SmartCategorizer._clean_text(target)
			for alias, target in raw_aliases.items()
			if alias and target
		}

	@staticmethod
	def _clean_text(value: str) -> str:
		"""Normalize a transaction description for fuzzy matching."""

		text = normalize_text(value)
		text = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", text)
		text = re.sub(r"\b\d+\b", " ", text)
		text = re.sub(r"[^A-Z0-9\s]", " ", text)
		text = re.sub(r"\s+", " ", text).strip()
		return text

	def _fallback_category(self) -> CategoriaDimDTO:
		"""Return the generic quarantine category."""

		return CategoriaDimDTO.model_validate(
			{
				"id": CategoriaFallback.NAO_CLASSIFICADO.value,
				"macro_categoria": CategoriaFallback.NAO_CLASSIFICADO.value,
				"subcategoria": CategoriaFallback.NAO_CLASSIFICADO.value,
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#9CA3AF",
				"icone": "question",
				"budget_default": 0,
			},
		)

	@staticmethod
	def _fallback_categories() -> list[CategoriaDimDTO]:
		"""Return the built-in taxonomy used when DuckDB cannot be opened."""

		return [
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "MORADIA",
					"subcategoria": "ALUGUEL",
					"tipo_financeiro": "FIXO",
					"essencialidade": "ESSENCIAL",
					"cor_dashboard": "#7C4DFF",
					"icone": "house",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "TRANSPORTE",
					"subcategoria": "UBER",
					"tipo_financeiro": "VARIAVEL",
					"essencialidade": "DISCRICIONARIO",
					"cor_dashboard": "#00B8D9",
					"icone": "car",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "ALIMENTACAO",
					"subcategoria": "IFOOD",
					"tipo_financeiro": "VARIAVEL",
					"essencialidade": "DISCRICIONARIO",
					"cor_dashboard": "#FFB020",
					"icone": "utensils",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "ALIMENTACAO",
					"subcategoria": "SUPERMERCADO",
					"tipo_financeiro": "VARIAVEL",
					"essencialidade": "ESSENCIAL",
					"cor_dashboard": "#FFB020",
					"icone": "basket",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "SAUDE",
					"subcategoria": "FARMACIA",
					"tipo_financeiro": "VARIAVEL",
					"essencialidade": "ESSENCIAL",
					"cor_dashboard": "#2EC4B6",
					"icone": "medical",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "LAZER",
					"subcategoria": "STREAMING",
					"tipo_financeiro": "RECORRENTE",
					"essencialidade": "DISCRICIONARIO",
					"cor_dashboard": "#FF6B6B",
					"icone": "tv",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "ASSINATURAS",
					"subcategoria": "SOFTWARE",
					"tipo_financeiro": "RECORRENTE",
					"essencialidade": "DISCRICIONARIO",
					"cor_dashboard": "#9B5DE5",
					"icone": "subscription",
					"budget_default": 0,
				},
			),
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "INVESTIMENTOS",
					"subcategoria": "APORTE",
					"tipo_financeiro": "FIXO",
					"essencialidade": "ESSENCIAL",
					"cor_dashboard": "#06D6A0",
					"icone": "chart-line",
					"budget_default": 0,
				},
			),
		]

	@staticmethod
	def _is_fallback(category: CategoriaDimDTO) -> bool:
		"""Check whether a category is the quarantine fallback."""

		return category.subcategoria == CategoriaFallback.NAO_CLASSIFICADO.value
