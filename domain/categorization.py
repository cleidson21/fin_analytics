"""Rule-based transaction categorization backed by a CSV taxonomy."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from config.constants import CategoriaFallback, TipoTransacao
from utils.normalization import normalize_text


@dataclass(frozen=True, slots=True)
class CategorizationRule:
	"""Single keyword rule loaded from the category taxonomy CSV."""

	keyword: str
	categoria: str
	tipo: TipoTransacao
	prioridade: int
	descricao: str | None = None


DEFAULT_CATEGORIAS_CSV: Final[Path] = Path(__file__).resolve().parents[1] / "config" / "categorias.csv"


class Categorizer:
	"""In-memory keyword categorizer for financial transaction descriptions.

	Rules are loaded from ``config/categorias.csv`` and ordered by ascending
	priority so higher-priority matches win first.
	"""

	def __init__(self, csv_path: Path | str = DEFAULT_CATEGORIAS_CSV) -> None:
		self._csv_path = Path(csv_path)
		self._rules = self._load_rules(self._csv_path)

	@staticmethod
	def _load_rules(csv_path: Path) -> list[CategorizationRule]:
		"""Load and normalize categorization rules from a CSV file."""

		with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
			reader = csv.DictReader(csv_file)
			rules = [
				CategorizationRule(
					keyword=normalize_text(row.get("keyword", "")),
					categoria=normalize_text(row.get("categoria", "")),
					tipo=TipoTransacao(row.get("tipo", "")),
					prioridade=int(row.get("prioridade", 0)),
					descricao=row.get("descricao", "").strip() if row.get("descricao") else None,
				)
				for row in reader
				if row.get("keyword") and row.get("categoria") and row.get("tipo") and row.get("prioridade")
			]

		return sorted(rules, key=lambda rule: (rule.prioridade, rule.keyword))

	def get_category_description(self, categoria: str) -> str:
		"""Return a human-friendly description for a given category.

		If the taxonomy provides a `descricao` for any rule matching the
		category, return it; otherwise fall back to the category label.
		"""

		normalized = normalize_text(categoria)
		for rule in self._rules:
			if rule.categoria and rule.categoria == normalized and rule.descricao:
				return rule.descricao
		# fallback to the original label if nothing more descriptive found
		return categoria

	def categorize(self, descricao: str) -> tuple[str | CategoriaFallback, TipoTransacao | str]:
		"""Categorize a transaction description using the loaded keyword rules.

		Args:
			descricao: Raw transaction description.

		Returns:
			A tuple with category and type. If no rule matches, the fallback
			values ``CategoriaFallback.NAO_CLASSIFICADO`` and
			``TipoTransacao.REVISAO_MANUAL`` are returned.
		"""

		descricao_normalizada = normalize_text(descricao)

		for rule in self._rules:
			if rule.keyword and rule.keyword in descricao_normalizada:
				return rule.categoria, rule.tipo

		return CategoriaFallback.NAO_CLASSIFICADO, TipoTransacao.REVISAO_MANUAL
