from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus


@dataclass
class Goal:
    id: UUID
    user_id: UUID
    name: str
    target_amount: float
    goal_type: GoalType
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    # Campos opcionais originais
    description: Optional[str] = None
    target_date: Optional[date] = None

    # Novos campos — Lote 10.1
    current_amount: Optional[float] = None          # Manual; null = não informado
    priority: Optional[int] = None                  # 1 (mais alta) a 5 (mais baixa)
    monthly_contribution: Optional[float] = None    # Aporte mensal planejado
    linked_account_id: Optional[str] = None         # Referência textual; sem FK formal
    assumptions_json: Optional[str] = None          # JSON string para uso em 10.3

    def validate(self) -> None:
        """Valida as regras de domínio básicas da Meta."""
        if self.target_amount <= 0:
            raise ValueError("target_amount must be strictly positive.")

        if not self.name or len(self.name.strip()) < 3 or len(self.name) > 100:
            raise ValueError("Goal name must be between 3 and 100 characters.")

        if self.target_date and isinstance(self.target_date, date):
            if self.target_date < date.today():
                raise ValueError("target_date must be today or in the future.")

        if self.current_amount is not None and self.current_amount < 0:
            raise ValueError("current_amount must be >= 0 when provided.")

        if self.priority is not None and self.priority not in (1, 2, 3, 4, 5):
            raise ValueError("priority must be between 1 and 5.")

        if self.monthly_contribution is not None and self.monthly_contribution < 0:
            raise ValueError("monthly_contribution must be >= 0 when provided.")

    def progress_pct(self) -> Optional[float]:
        """
        Retorna o percentual de progresso da meta.

        Regra (aprovada em Lote 10.1):
          - null se current_amount não foi informado
          - min((current_amount / target_amount) * 100, 100.0) caso contrário

        Nunca persistido — calculado sob demanda.
        """
        if self.current_amount is None:
            return None
        if self.target_amount <= 0:
            return None
        return min((self.current_amount / self.target_amount) * 100.0, 100.0)
