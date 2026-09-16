from datetime import datetime
from typing import Optional
from uuid import UUID

from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository
from backend.application.dtos.goal_dto import GoalUpdateDTO, GoalResponseDTO


class UpdateGoalUseCase:
    """
    Atualiza uma meta existente, garantindo user isolation.
    Apenas campos fornecidos no DTO são atualizados (patch semântico).
    """

    def __init__(self, repository: GoalRepository):
        self.repository = repository

    async def execute(
        self, goal_id: UUID, user_id: UUID, dto: GoalUpdateDTO
    ) -> Optional[GoalResponseDTO]:
        # Buscar a meta garantindo ownership
        existing = await self.repository.get_by_id(goal_id, user_id)
        if existing is None:
            return None  # Goal não existe ou pertence a outro usuário

        # Aplicar apenas os campos fornecidos (patch semântico)
        if dto.name is not None:
            existing.name = dto.name
        if dto.description is not None:
            existing.description = dto.description
        if dto.goal_type is not None:
            existing.goal_type = dto.goal_type
        if dto.target_amount is not None:
            existing.target_amount = dto.target_amount
        if dto.target_date is not None:
            existing.target_date = dto.target_date
        if dto.status is not None:
            existing.status = dto.status
        if dto.current_amount is not None:
            existing.current_amount = dto.current_amount
        if dto.priority is not None:
            existing.priority = dto.priority
        if dto.monthly_contribution is not None:
            existing.monthly_contribution = dto.monthly_contribution
        if dto.linked_account_id is not None:
            existing.linked_account_id = dto.linked_account_id
        if dto.assumptions_json is not None:
            existing.assumptions_json = dto.assumptions_json

        existing.updated_at = datetime.utcnow()

        # Validar após aplicar as alterações
        existing.validate()

        updated = await self.repository.update(existing)
        return GoalResponseDTO.from_entity(updated)
