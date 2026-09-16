from typing import Optional
from uuid import UUID

from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository
from backend.application.dtos.goal_dto import GoalResponseDTO


class GetGoalUseCase:
    """
    Retorna uma meta pelo ID, garantindo user isolation.
    Retorna None se a meta não existir ou não pertencer ao usuário.
    """

    def __init__(self, repository: GoalRepository):
        self.repository = repository

    async def execute(self, goal_id: UUID, user_id: UUID) -> Optional[GoalResponseDTO]:
        goal = await self.repository.get_by_id(goal_id, user_id)
        if goal is None:
            return None
        return GoalResponseDTO.from_entity(goal)
