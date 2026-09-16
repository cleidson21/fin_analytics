from uuid import UUID

from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository


class DeleteGoalUseCase:
    """
    Exclui uma meta pelo ID, garantindo user isolation.
    Retorna True se excluída, False se não encontrada ou de outro usuário.
    """

    def __init__(self, repository: GoalRepository):
        self.repository = repository

    async def execute(self, goal_id: UUID, user_id: UUID) -> bool:
        return await self.repository.delete(goal_id, user_id)
