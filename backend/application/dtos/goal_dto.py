import json
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus


class GoalCreateDTO(BaseModel):
    """DTO de criação de meta. Todos os campos obrigatórios são validados aqui."""

    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    goal_type: GoalType
    target_amount: float = Field(..., gt=0, description="Valor-alvo da meta. Deve ser > 0.")

    # Campos opcionais
    target_date: Optional[date] = None
    current_amount: Optional[float] = Field(
        None, ge=0,
        description="Valor atual da meta (informado manualmente). null = não informado."
    )
    priority: Optional[int] = Field(
        None, ge=1, le=5,
        description="Prioridade de 1 (mais alta) a 5 (mais baixa)."
    )
    monthly_contribution: Optional[float] = Field(
        None, ge=0,
        description="Aporte mensal planejado."
    )
    linked_account_id: Optional[str] = Field(
        None, max_length=255,
        description="Referência textual a uma conta. Sem validação de FK nesta fase."
    )
    assumptions_json: Optional[str] = Field(
        None,
        description="JSON de premissas para projeções (uso em Lote 10.3). Validado como JSON."
    )

    @field_validator("assumptions_json")
    @classmethod
    def validate_assumptions_json(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            json.loads(v)
        except (ValueError, TypeError):
            raise ValueError("assumptions_json must be a valid JSON string.")
        return v


class GoalUpdateDTO(BaseModel):
    """DTO de atualização parcial de meta. Todos os campos são opcionais."""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    goal_type: Optional[GoalType] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    status: Optional[GoalStatus] = None

    # Novos campos — Lote 10.1
    current_amount: Optional[float] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=1, le=5)
    monthly_contribution: Optional[float] = Field(None, ge=0)
    linked_account_id: Optional[str] = Field(None, max_length=255)
    assumptions_json: Optional[str] = None

    @field_validator("assumptions_json")
    @classmethod
    def validate_assumptions_json(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            json.loads(v)
        except (ValueError, TypeError):
            raise ValueError("assumptions_json must be a valid JSON string.")
        return v


class GoalResponseDTO(BaseModel):
    """DTO de resposta — todos os campos persistidos + progress_pct calculado."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    goal_type: GoalType
    target_amount: float
    target_date: Optional[date] = None
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    # Novos campos — Lote 10.1
    current_amount: Optional[float] = None  # null = não informado (nunca 0 por padrão)
    priority: Optional[int] = None
    monthly_contribution: Optional[float] = None
    linked_account_id: Optional[str] = None
    assumptions_json: Optional[str] = None

    # Campo derivado — não persistido
    progress_pct: Optional[float] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "GoalResponseDTO":
        """
        Constrói o DTO a partir da entidade Goal.
        Calcula progress_pct deterministicamente (aprovado em Lote 10.1):
          - null se current_amount é null
          - min((current / target) * 100, 100.0) caso contrário
        """
        progress = entity.progress_pct() if hasattr(entity, "progress_pct") else None
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            goal_type=entity.goal_type,
            target_amount=entity.target_amount,
            target_date=entity.target_date,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            current_amount=entity.current_amount,
            priority=entity.priority,
            monthly_contribution=entity.monthly_contribution,
            linked_account_id=entity.linked_account_id,
            assumptions_json=entity.assumptions_json,
            progress_pct=progress,
        )
