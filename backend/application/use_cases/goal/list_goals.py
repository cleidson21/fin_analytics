from typing import List
from uuid import UUID

from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository
from backend.application.dtos.goal_dto import GoalResponseDTO


class ListGoalsUseCase:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    async def execute(self, user_id: UUID) -> List[GoalResponseDTO]:
        goals = await self.repository.get_by_user(user_id)
        return [GoalResponseDTO.from_entity(g) for g in goals]
