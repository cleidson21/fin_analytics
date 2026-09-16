from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.models.goal import GoalModel
from backend.domain.entities.goal import Goal
from backend.domain.enums.goal_status import GoalStatus


class GoalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ #
    #  Conversão entre camadas                                            #
    # ------------------------------------------------------------------ #

    def _to_entity(self, model: GoalModel) -> Goal:
        return Goal(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            goal_type=model.goal_type,
            target_amount=float(model.target_amount),
            target_date=model.target_date,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            # Novos campos — Lote 10.1
            current_amount=float(model.current_amount) if model.current_amount is not None else None,
            priority=model.priority,
            monthly_contribution=float(model.monthly_contribution) if model.monthly_contribution is not None else None,
            linked_account_id=model.linked_account_id,
            assumptions_json=model.assumptions_json,
        )

    def _to_model(self, entity: Goal) -> GoalModel:
        return GoalModel(
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
            # Novos campos — Lote 10.1
            current_amount=entity.current_amount,
            priority=entity.priority,
            monthly_contribution=entity.monthly_contribution,
            linked_account_id=entity.linked_account_id,
            assumptions_json=entity.assumptions_json,
        )

    # ------------------------------------------------------------------ #
    #  CRUD                                                               #
    # ------------------------------------------------------------------ #

    async def create(self, goal: Goal) -> Goal:
        model = self._to_model(goal)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, goal_id: UUID, user_id: UUID) -> Optional[Goal]:
        """Retorna a meta se pertencer ao usuário. User isolation garantido."""
        stmt = select(GoalModel).where(
            GoalModel.id == goal_id,
            GoalModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user(self, user_id: UUID) -> List[Goal]:
        """Lista todas as metas do usuário, ordenadas por prioridade e criação."""
        stmt = (
            select(GoalModel)
            .where(GoalModel.user_id == user_id)
            .order_by(
                GoalModel.priority.nulls_last(),
                GoalModel.created_at.desc()
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update(self, goal: Goal) -> Goal:
        """
        Atualiza a meta verificando que pertence ao user_id.
        Garante user isolation — não permite atualização de meta de outro usuário.
        """
        model = await self.session.get(GoalModel, goal.id)
        if model is None or model.user_id != goal.user_id:
            raise ValueError("Goal not found or access denied")

        # Campos originais
        model.name = goal.name
        model.description = goal.description
        model.goal_type = goal.goal_type
        model.target_amount = goal.target_amount
        model.target_date = goal.target_date
        model.status = goal.status
        model.updated_at = datetime.utcnow()

        # Novos campos — Lote 10.1
        model.current_amount = goal.current_amount
        model.priority = goal.priority
        model.monthly_contribution = goal.monthly_contribution
        model.linked_account_id = goal.linked_account_id
        model.assumptions_json = goal.assumptions_json

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, goal_id: UUID, user_id: UUID) -> bool:
        """
        Exclui a meta verificando que pertence ao user_id.
        Retorna True se excluída, False se não encontrada.
        """
        model = await self.session.get(GoalModel, goal_id)
        if model is None or model.user_id != user_id:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True
