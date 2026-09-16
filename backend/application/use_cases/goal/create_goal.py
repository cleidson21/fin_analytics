from datetime import datetime
from uuid import UUID, uuid4

from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository
from backend.domain.entities.goal import Goal
from backend.domain.enums.goal_status import GoalStatus
from backend.application.dtos.goal_dto import GoalCreateDTO, GoalResponseDTO


class CreateGoalUseCase:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, dto: GoalCreateDTO) -> GoalResponseDTO:
        now = datetime.utcnow()
        goal_entity = Goal(
            id=uuid4(),
            user_id=user_id,
            name=dto.name,
            description=dto.description,
            goal_type=dto.goal_type,
            target_amount=dto.target_amount,
            target_date=dto.target_date,
            status=GoalStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            # Novos campos — Lote 10.1
            current_amount=dto.current_amount,
            priority=dto.priority,
            monthly_contribution=dto.monthly_contribution,
            linked_account_id=dto.linked_account_id,
            assumptions_json=dto.assumptions_json,
        )
        goal_entity.validate()
        saved = await self.repository.create(goal_entity)
        return GoalResponseDTO.from_entity(saved)
