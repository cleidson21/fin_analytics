"""Smart fuzzy categorization for financial transaction descriptions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Final, Sequence

from config.constants import CategoriaFallback
from models.wealth_schemas import CategoriaDimDTO
from rapidfuzz import fuzz, process
from repositories.wealth_repository import WealthRepository
from utils.normalization import normalize_text


@dataclass(frozen=True, slots=True)
class _Choice:
	"""Normalized fuzzy-match candidate associated with a category DTO."""

	label: str
	dto: CategoriaDimDTO


class SmartCategorizer:
	"""Fuzzy classifier that maps descriptions to the closest category."""

	def __init__(
		self,
		categories: Sequence[CategoriaDimDTO] | None = None,
		*,
		repository: WealthRepository | None = None,
		threshold: int = 80,
	) -> None:
		self._repository = repository
		self._threshold = threshold
		self._choices: list[_Choice] = []
		self._choice_lookup: dict[str, CategoriaDimDTO] = {}
		self._categories = list(categories) if categories is not None else self._load_categories()
		self.refresh(self._categories)

	def refresh(self, categories: Sequence[CategoriaDimDTO] | None = None) -> None:
		"""Reload the fuzzy index from the provided category list or the repository."""

		resolved_categories = list(categories) if categories is not None else self._load_categories()
		choices: list[_Choice] = []
		lookup: dict[str, CategoriaDimDTO] = {}

		for category in resolved_categories:
			for label in self._candidate_labels(category):
				if not label:
					continue
				lookup.setdefault(label, category)
				choices.append(_Choice(label=label, dto=category))

		self._choices = choices
		self._choice_lookup = lookup

	def categorize(self, descricao: str) -> CategoriaDimDTO:
		"""Return the best matching category or the quarantine fallback."""

		cleaned = self._clean_text(descricao)
		if not cleaned or not self._choices:
			return self._fallback_category()

		exact = self._choice_lookup.get(cleaned)
		if exact is not None:
			return exact

		choice = process.extractOne(
			cleaned,
			(choice.label for choice in self._choices),
			scorer=fuzz.WRatio,
			processor=None,
			score_cutoff=self._threshold,
		)
		if choice is None:
			return self._fallback_category()

		matched_label = str(choice[0])
		resolved = self._choice_lookup.get(matched_label)
		if resolved is None:
			return self._fallback_category()
		return resolved

	def categorize_transaction(self, descricao: str) -> CategoriaDimDTO:
		"""Compatibility alias used by the transaction transformer."""

		return self.categorize(descricao)

	def _load_categories(self) -> list[CategoriaDimDTO]:
		"""Load categories from DuckDB when possible, otherwise use a fallback taxonomy."""

		if self._repository is not None:
			try:
				return self._repository.fetch_categories()
			except Exception:
				return self._fallback_categories()

		try:
			return WealthRepository(read_only=True).fetch_categories()
		except Exception:
			return self._fallback_categories()

	@staticmethod
	def _candidate_labels(category: CategoriaDimDTO) -> list[str]:
		"""Build the searchable labels for a category."""

		macro = SmartCategorizer._clean_text(category.macro_categoria)
		subcategoria = SmartCategorizer._clean_text(category.subcategoria)
		combined = SmartCategorizer._clean_text(f"{category.macro_categoria} {category.subcategoria}")
		labels = [label for label in (combined, subcategoria, macro) if label]
		return list(dict.fromkeys(labels))

	@staticmethod
	def _clean_text(value: str) -> str:
		"""Remove punctuation, digits and extra spacing before fuzzy matching."""

		text = normalize_text(value)
		text = re.sub(r"\d+", " ", text)
		text = re.sub(r"[^A-Z\s]", " ", text)
		text = re.sub(r"\s+", " ", text).strip()
		return text

	@staticmethod
	def _fallback_category() -> CategoriaDimDTO:
		"""Return the quarantine category used when confidence is too low."""

		return CategoriaDimDTO.model_validate(
			{
				"id": CategoriaFallback.NAO_CLASSIFICADO.value,
				"macro_categoria": CategoriaFallback.NAO_CLASSIFICADO.value,
				"subcategoria": CategoriaFallback.NAO_CLASSIFICADO.value,
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#9CA3AF",
				"icone": "question",
				"budget_default": Decimal("0"),
			},
		)

	@staticmethod
	def _fallback_categories() -> list[CategoriaDimDTO]:
		"""Built-in category set used when the repository is unavailable."""

		return [
			CategoriaDimDTO.model_validate(
				{
					"macro_categoria": "MORADIA",
					"subcategoria": "ALUGUEL",
					"tipo_financeiro": "FIXO",
					"essencialidade": "ESSENCIAL",
					"cor_dashboard": "#7C4DFF",
					"icone": "house",
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
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
					"budget_default": Decimal("0"),
				},
			),
		]
