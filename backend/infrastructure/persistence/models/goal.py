from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Numeric, DateTime, Date, Integer, Text, ForeignKey, Enum as SAEnum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus


class GoalModel(Base):
    """
    ORM de persistência para o módulo de Metas (Wealth Intelligence).

    Colunas adicionadas no Lote 10.1:
      current_amount       — valor atual (manual, nullable)
      priority             — prioridade 1–5 (nullable)
      monthly_contribution — aporte mensal planejado (nullable)
      linked_account_id    — referência textual de conta (sem FK, nullable)
      assumptions_json     — JSON de premissas para 10.3 (nullable)
    """
    __tablename__ = "goals"

    # Campos originais
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    goal_type: Mapped[GoalType] = mapped_column(
        SAEnum(GoalType, native_enum=False, length=50), nullable=False
    )
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        SAEnum(GoalStatus, native_enum=False, length=50),
        nullable=False,
        default=GoalStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Novos campos — Lote 10.1
    current_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    priority: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    monthly_contribution: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    linked_account_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    assumptions_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
