"""Goals service for financial objective tracking."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from config.constants import StatusMeta
from models.wealth_schemas import MetaFinanceiraDTO
from repositories.wealth_repository import WealthRepository
from pydantic import ValidationError
from utils.logger import get_logger


class GoalsService:
	"""Compute financial goal progress using the wealth repository."""

	def __init__(self, repository: WealthRepository) -> None:
		self._repository = repository
		self._logger = get_logger(__name__)

	def create_goal(self, nome: str, valor_alvo: Decimal, prazo_meses: int, prioridade: int) -> bool:
		"""Validate and persist a new financial goal."""

		try:
			goal = MetaFinanceiraDTO.model_validate(
				{
					"nome": nome,
					"valor_alvo": valor_alvo,
					"prazo_meses": prazo_meses,
					"prioridade": prioridade,
				},
			)
		except (TypeError, ValueError, ValidationError) as exc:
			self._logger.exception("Invalid goal payload: nome=%r prazo_meses=%r prioridade=%r", nome, prazo_meses, prioridade)
			return False

		if goal.valor_alvo <= 0:
			self._logger.warning("Rejected goal with non-positive target value: nome=%r valor_alvo=%s", goal.nome, goal.valor_alvo)
			return False

		if goal.prazo_meses <= 0:
			self._logger.warning("Rejected goal with non-positive deadline: nome=%r prazo_meses=%s", goal.nome, goal.prazo_meses)
			return False

		try:
			self._repository.upsert_goal(goal)
		except Exception as exc:
			self._logger.exception("Failed to persist goal nome=%r: %s", goal.nome, exc)
			return False

		return True

	def get_goals_progress(self) -> list[dict[str, Any]]:
		"""Return each goal with completion percentage and monthly contribution advice."""

		results: list[dict[str, Any]] = []
		for goal in self._repository.fetch_goals():
			valor_alvo = self._to_decimal(goal.get("valor_alvo"))
			valor_atual = self._to_decimal(goal.get("valor_atual"))
			prazo_meses = int(goal.get("prazo_meses") or 0)
			prioridade = int(goal.get("prioridade") or 0)
			status = goal.get("status", StatusMeta.ATIVA)

			if valor_alvo <= 0:
				percentual_conclusao = Decimal("0")
			else:
				percentual_conclusao = min((valor_atual / valor_alvo) * Decimal("100"), Decimal("100"))

			valor_restante = max(valor_alvo - valor_atual, Decimal("0"))
			aporte_mensal_sugerido = (
				valor_restante / Decimal(prazo_meses)
				if prazo_meses > 0 and valor_restante > 0
				else Decimal("0")
			)

			results.append(
				{
					"nome": goal.get("nome"),
					"valor_alvo": valor_alvo,
					"valor_atual": valor_atual,
					"prazo_meses": prazo_meses,
					"prioridade": prioridade,
					"status": status.value if isinstance(status, StatusMeta) else str(status),
					"percentual_conclusao": percentual_conclusao,
					"aporte_mensal_sugerido": aporte_mensal_sugerido,
					"valor_restante": valor_restante,
				},
			)

		return results

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert repository numeric values into ``Decimal`` safely."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		return Decimal("0")
