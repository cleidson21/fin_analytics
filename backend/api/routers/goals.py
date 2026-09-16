from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.application.dtos.goal_dto import GoalCreateDTO, GoalUpdateDTO, GoalResponseDTO
from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.use_cases.goal.create_goal import CreateGoalUseCase
from backend.application.use_cases.goal.list_goals import ListGoalsUseCase
from backend.application.use_cases.goal.get_goal import GetGoalUseCase
from backend.application.use_cases.goal.update_goal import UpdateGoalUseCase
from backend.application.use_cases.goal.delete_goal import DeleteGoalUseCase
from backend.core.container import (
    get_create_goal_use_case,
    get_list_goals_use_case,
    get_get_goal_use_case,
    get_update_goal_use_case,
    get_delete_goal_use_case,
)

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_goal(
    dto: GoalCreateDTO,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: CreateGoalUseCase = Depends(get_create_goal_use_case),
):
    """
    Cria uma nova meta para o usuário autenticado.
    O user_id é extraído do token JWT — nunca do corpo da requisição.
    """
    return await use_case.execute(current_user.id, dto)


@router.get("", response_model=List[GoalResponseDTO])
async def list_goals(
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: ListGoalsUseCase = Depends(get_list_goals_use_case),
):
    """Lista todas as metas do usuário autenticado, ordenadas por prioridade e criação."""
    return await use_case.execute(current_user.id)


@router.get("/{goal_id}", response_model=GoalResponseDTO)
async def get_goal(
    goal_id: UUID,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetGoalUseCase = Depends(get_get_goal_use_case),
):
    """
    Retorna uma meta pelo ID.
    Retorna 404 se a meta não existir ou pertencer a outro usuário (user isolation).
    """
    goal = await use_case.execute(goal_id, current_user.id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada."
        )
    return goal


@router.put("/{goal_id}", response_model=GoalResponseDTO)
async def update_goal(
    goal_id: UUID,
    dto: GoalUpdateDTO,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: UpdateGoalUseCase = Depends(get_update_goal_use_case),
):
    """
    Atualiza uma meta existente do usuário autenticado.
    Atualização é parcial (patch semântico): somente campos fornecidos são alterados.
    Retorna 404 se a meta não existir ou pertencer a outro usuário.
    """
    try:
        updated = await use_case.execute(goal_id, current_user.id, dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada."
        )
    return updated


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: DeleteGoalUseCase = Depends(get_delete_goal_use_case),
):
    """
    Exclui uma meta do usuário autenticado.
    Retorna 204 se excluída com sucesso.
    Retorna 404 se a meta não existir ou pertencer a outro usuário.
    """
    deleted = await use_case.execute(goal_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada."
        )
