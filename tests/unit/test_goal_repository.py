"""
tests/unit/test_goal_repository.py

Testes de repositório de Goals usando AsyncMock (padrão do projeto).
Cobre: create, get_by_id, get_by_user, update, delete, user isolation.
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.entities.goal import Goal
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus
from backend.infrastructure.persistence.models.goal import GoalModel
from backend.infrastructure.persistence.repositories.goal_repository import GoalRepository


# ------------------------------------------------------------------ #
#  Fábrica de objetos de teste                                        #
# ------------------------------------------------------------------ #

USER_A = uuid4()
USER_B = uuid4()
GOAL_ID = uuid4()


def make_goal_entity(user_id=None, **overrides) -> Goal:
    defaults = dict(
        id=GOAL_ID,
        user_id=user_id or USER_A,
        name="Meta de Emergência",
        target_amount=30000.0,
        goal_type=GoalType.EMERGENCY_RESERVE,
        status=GoalStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    return Goal(**defaults)


def make_goal_model(user_id=None) -> GoalModel:
    m = GoalModel()
    m.id = GOAL_ID
    m.user_id = user_id or USER_A
    m.name = "Meta de Emergência"
    m.target_amount = 30000.0
    m.goal_type = GoalType.EMERGENCY_RESERVE
    m.status = GoalStatus.ACTIVE
    m.description = None
    m.target_date = None
    m.current_amount = None
    m.priority = None
    m.monthly_contribution = None
    m.linked_account_id = None
    m.assumptions_json = None
    m.created_at = datetime.utcnow()
    m.updated_at = datetime.utcnow()
    return m


# ------------------------------------------------------------------ #
#  create                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_repository_create():
    session = AsyncMock()
    model = make_goal_model()

    async def mock_refresh(m):
        m.id = GOAL_ID
        m.created_at = datetime.utcnow()
        m.updated_at = datetime.utcnow()

    session.refresh = mock_refresh

    repo = GoalRepository(session=session)
    entity = make_goal_entity()

    with patch.object(repo, "_to_model", return_value=model):
        with patch.object(repo, "_to_entity", return_value=entity):
            result = await repo.create(entity)

    session.add.assert_called_once_with(model)
    session.commit.assert_called_once()
    assert result.name == "Meta de Emergência"


# ------------------------------------------------------------------ #
#  get_by_id                                                          #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_repository_get_by_id_found():
    session = AsyncMock()
    model = make_goal_model()
    session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=model))

    repo = GoalRepository(session=session)
    result = await repo.get_by_id(GOAL_ID, USER_A)

    assert result is not None
    assert result.name == "Meta de Emergência"


@pytest.mark.asyncio
async def test_repository_get_by_id_not_found():
    session = AsyncMock()
    session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    repo = GoalRepository(session=session)
    result = await repo.get_by_id(GOAL_ID, USER_A)

    assert result is None


@pytest.mark.asyncio
async def test_repository_get_by_id_user_isolation():
    """get_by_id para um user_id diferente deve retornar None."""
    session = AsyncMock()
    # Simulamos que a query filtrou por user_id e não encontrou nada
    session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    repo = GoalRepository(session=session)
    result = await repo.get_by_id(GOAL_ID, USER_B)  # USER_B não é dono

    assert result is None


# ------------------------------------------------------------------ #
#  get_by_user                                                        #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_repository_get_by_user():
    session = AsyncMock()
    model = make_goal_model()
    session.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[model]))))

    repo = GoalRepository(session=session)
    results = await repo.get_by_user(USER_A)

    assert len(results) == 1
    assert results[0].user_id == USER_A


@pytest.mark.asyncio
async def test_repository_get_by_user_empty():
    session = AsyncMock()
    session.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

    repo = GoalRepository(session=session)
    results = await repo.get_by_user(USER_A)

    assert results == []


# ------------------------------------------------------------------ #
#  update                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_repository_update_ok():
    session = AsyncMock()
    model = make_goal_model(user_id=USER_A)
    session.get = AsyncMock(return_value=model)

    async def mock_refresh(m):
        pass

    session.refresh = mock_refresh

    repo = GoalRepository(session=session)
    entity = make_goal_entity(user_id=USER_A, name="Meta Atualizada")
    result = await repo.update(entity)

    assert model.name == "Meta Atualizada"
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_repository_update_wrong_user():
    """update com user_id diferente deve lançar ValueError."""
    session = AsyncMock()
    model = make_goal_model(user_id=USER_A)
    session.get = AsyncMock(return_value=model)

    repo = GoalRepository(session=session)
    entity = make_goal_entity(user_id=USER_B)  # user_id diferente do dono

    with pytest.raises(ValueError, match="access denied"):
        await repo.update(entity)


@pytest.mark.asyncio
async def test_repository_update_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    repo = GoalRepository(session=session)
    entity = make_goal_entity()

    with pytest.raises(ValueError, match="not found"):
        await repo.update(entity)


# ------------------------------------------------------------------ #
#  delete                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_repository_delete_ok():
    session = AsyncMock()
    model = make_goal_model(user_id=USER_A)
    session.get = AsyncMock(return_value=model)

    repo = GoalRepository(session=session)
    result = await repo.delete(GOAL_ID, USER_A)

    assert result is True
    session.delete.assert_called_once_with(model)
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_repository_delete_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    repo = GoalRepository(session=session)
    result = await repo.delete(GOAL_ID, USER_A)

    assert result is False


@pytest.mark.asyncio
async def test_repository_delete_wrong_user():
    """delete com user_id diferente deve retornar False (não lança exceção)."""
    session = AsyncMock()
    model = make_goal_model(user_id=USER_A)
    session.get = AsyncMock(return_value=model)

    repo = GoalRepository(session=session)
    result = await repo.delete(GOAL_ID, USER_B)

    assert result is False
    session.delete.assert_not_called()
