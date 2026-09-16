"""
tests/unit/test_goals_api.py

Testes de API (router) para o módulo Goals:
  - POST, GET list, GET by id, PUT, DELETE
  - Autenticação (401)
  - Validação (422)
  - User isolation (404 para goal de outro usuário)
  - current_amount / progress_pct
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.main import app
from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.persistence.models.goal import GoalModel
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus


# ------------------------------------------------------------------ #
#  Mock de usuários                                                   #
# ------------------------------------------------------------------ #

USER_A_ID = uuid.uuid4()
USER_B_ID = uuid.uuid4()

def _make_user(user_id: uuid.UUID) -> UserResponseDTO:
    return UserResponseDTO(
        id=user_id,
        email=f"{user_id}@test.com",
        name="Test User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        last_login_at=None,
    )

MOCK_USER_A = _make_user(USER_A_ID)
MOCK_USER_B = _make_user(USER_B_ID)

async def get_current_user_a():
    return MOCK_USER_A

async def get_current_user_b():
    return MOCK_USER_B


# ------------------------------------------------------------------ #
#  Modelo de goal retornado pelo DB                                   #
# ------------------------------------------------------------------ #

GOAL_ID = uuid.uuid4()

def make_goal_model(user_id=None) -> GoalModel:
    m = GoalModel()
    m.id = GOAL_ID
    m.user_id = user_id or USER_A_ID
    m.name = "Reserva de Emergência"
    m.description = "Fundo de emergência de 6 meses"
    m.goal_type = GoalType.EMERGENCY_RESERVE
    m.target_amount = 30000.0
    m.target_date = None
    m.status = GoalStatus.ACTIVE
    m.current_amount = None
    m.priority = 1
    m.monthly_contribution = 1500.0
    m.linked_account_id = None
    m.assumptions_json = None
    m.created_at = datetime.utcnow()
    m.updated_at = datetime.utcnow()
    return m


# ------------------------------------------------------------------ #
#  Helpers de mock session                                            #
# ------------------------------------------------------------------ #

class MockResult:
    def __init__(self, items, scalar_value=None):
        self._items = items
        self._scalar_value = scalar_value

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalars(self):
        return self

    def all(self):
        return self._items


def make_refresh_noop():
    async def noop(m): pass
    return noop


# ------------------------------------------------------------------ #
#  Fixtures                                                           #
# ------------------------------------------------------------------ #

@pytest.fixture
def mock_session():
    s = AsyncMock()
    s.refresh = make_refresh_noop()
    return s


@pytest.fixture
def client_a(mock_session):
    async def get_mock_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = get_current_user_a
    app.dependency_overrides[get_db_session] = get_mock_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def client_b(mock_session):
    """Cliente autenticado como USER_B, mesma sessão mock."""
    async def get_mock_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = get_current_user_b
    app.dependency_overrides[get_db_session] = get_mock_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def client_noauth():
    """Cliente sem autenticação."""
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------ #
#  POST /api/v1/goals                                                 #
# ------------------------------------------------------------------ #

def test_create_goal_201(client_a, mock_session):
    model = make_goal_model()
    mock_session.execute.return_value = MockResult([model])

    response = client_a.post("/api/v1/goals", json={
        "name": "Reserva de Emergência",
        "goal_type": "EMERGENCY_RESERVE",
        "target_amount": 30000.0,
        "priority": 1,
        "monthly_contribution": 1500.0,
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Reserva de Emergência"
    assert data["goal_type"] == "EMERGENCY_RESERVE"
    assert data["status"] == "ACTIVE"
    assert data["user_id"] == str(USER_A_ID)


def test_create_goal_requires_auth(client_noauth):
    response = client_noauth.post("/api/v1/goals", json={
        "name": "Teste",
        "goal_type": "CUSTOM",
        "target_amount": 1000.0,
    })
    assert response.status_code == 401


def test_create_goal_invalid_amount(client_a, mock_session):
    """target_amount <= 0 deve retornar 422."""
    response = client_a.post("/api/v1/goals", json={
        "name": "Meta Inválida",
        "goal_type": "CUSTOM",
        "target_amount": 0,
    })
    assert response.status_code == 422


def test_create_goal_invalid_priority(client_a, mock_session):
    """priority fora do range 1–5 deve retornar 422."""
    response = client_a.post("/api/v1/goals", json={
        "name": "Meta Inválida",
        "goal_type": "CUSTOM",
        "target_amount": 1000.0,
        "priority": 10,
    })
    assert response.status_code == 422


def test_create_goal_invalid_monthly_contribution(client_a, mock_session):
    """monthly_contribution negativo deve retornar 422."""
    response = client_a.post("/api/v1/goals", json={
        "name": "Meta Inválida",
        "goal_type": "CUSTOM",
        "target_amount": 1000.0,
        "monthly_contribution": -100.0,
    })
    assert response.status_code == 422


def test_create_goal_with_new_type(client_a, mock_session):
    """Novos GoalTypes do Lote 10.1 devem ser aceitos."""
    model = make_goal_model()
    model.goal_type = GoalType.FINANCIAL_INDEPENDENCE
    mock_session.execute.return_value = MockResult([model])

    response = client_a.post("/api/v1/goals", json={
        "name": "Independência Financeira",
        "goal_type": "FINANCIAL_INDEPENDENCE",
        "target_amount": 2000000.0,
    })
    assert response.status_code == 201


def test_create_goal_invalid_assumptions_json(client_a, mock_session):
    """assumptions_json inválido deve retornar 422."""
    response = client_a.post("/api/v1/goals", json={
        "name": "Meta Teste",
        "goal_type": "CUSTOM",
        "target_amount": 5000.0,
        "assumptions_json": "isto nao e json",
    })
    assert response.status_code == 422


# ------------------------------------------------------------------ #
#  GET /api/v1/goals                                                  #
# ------------------------------------------------------------------ #

def test_list_goals_200(client_a, mock_session):
    model = make_goal_model()
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get("/api/v1/goals")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Reserva de Emergência"


def test_list_goals_empty(client_a, mock_session):
    mock_session.execute.return_value = MockResult([])

    response = client_a.get("/api/v1/goals")

    assert response.status_code == 200
    assert response.json() == []


def test_list_goals_requires_auth(client_noauth):
    response = client_noauth.get("/api/v1/goals")
    assert response.status_code == 401


# ------------------------------------------------------------------ #
#  GET /api/v1/goals/{id}                                             #
# ------------------------------------------------------------------ #

def test_get_goal_by_id_200(client_a, mock_session):
    model = make_goal_model()
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get(f"/api/v1/goals/{GOAL_ID}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(GOAL_ID)


def test_get_goal_by_id_not_found(client_a, mock_session):
    mock_session.execute.return_value = MockResult([])

    response = client_a.get(f"/api/v1/goals/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_goal_requires_auth(client_noauth):
    response = client_noauth.get(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 401


# ------------------------------------------------------------------ #
#  PUT /api/v1/goals/{id}                                             #
# ------------------------------------------------------------------ #

def test_update_goal_200(client_a, mock_session):
    model = make_goal_model()
    # get_by_id via execute, update via session.get
    mock_session.execute.return_value = MockResult([model])
    mock_session.get = AsyncMock(return_value=model)

    response = client_a.put(f"/api/v1/goals/{GOAL_ID}", json={
        "name": "Reserva Atualizada",
        "priority": 2,
    })

    assert response.status_code == 200
    data = response.json()
    assert "id" in data


def test_update_goal_not_found(client_a, mock_session):
    mock_session.execute.return_value = MockResult([])

    response = client_a.put(f"/api/v1/goals/{uuid.uuid4()}", json={
        "name": "Qualquer",
    })

    assert response.status_code == 404


def test_update_goal_requires_auth(client_noauth):
    response = client_noauth.put(f"/api/v1/goals/{GOAL_ID}", json={"name": "X"})
    assert response.status_code == 401


def test_update_goal_invalid_amount(client_a, mock_session):
    response = client_a.put(f"/api/v1/goals/{GOAL_ID}", json={
        "target_amount": -500.0,
    })
    assert response.status_code == 422


# ------------------------------------------------------------------ #
#  DELETE /api/v1/goals/{id}                                          #
# ------------------------------------------------------------------ #

def test_delete_goal_204(client_a, mock_session):
    model = make_goal_model()
    mock_session.get = AsyncMock(return_value=model)

    response = client_a.delete(f"/api/v1/goals/{GOAL_ID}")

    assert response.status_code == 204


def test_delete_goal_not_found(client_a, mock_session):
    mock_session.get = AsyncMock(return_value=None)

    response = client_a.delete(f"/api/v1/goals/{uuid.uuid4()}")

    assert response.status_code == 404


def test_delete_goal_requires_auth(client_noauth):
    response = client_noauth.delete(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 401


# ------------------------------------------------------------------ #
#  User Isolation — USER_B não pode acessar goal de USER_A           #
# ------------------------------------------------------------------ #

def test_user_b_cannot_get_user_a_goal(mock_session):
    """USER_B tentando acessar goal de USER_A deve receber 404."""
    async def get_mock_db():
        yield mock_session

    # Simula que a query com user_id=USER_B não encontra nada
    # (porque o repositório filtra por user_id)
    mock_session.execute.return_value = MockResult([])  # sem resultado para USER_B

    app.dependency_overrides[get_current_user] = get_current_user_b
    app.dependency_overrides[get_db_session] = get_mock_db

    with TestClient(app) as c:
        response = c.get(f"/api/v1/goals/{GOAL_ID}")

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_user_b_cannot_delete_user_a_goal(mock_session):
    """USER_B tentando excluir goal de USER_A deve receber 404."""
    async def get_mock_db():
        yield mock_session

    model_a = make_goal_model(user_id=USER_A_ID)
    mock_session.get = AsyncMock(return_value=model_a)

    app.dependency_overrides[get_current_user] = get_current_user_b
    app.dependency_overrides[get_db_session] = get_mock_db

    with TestClient(app) as c:
        response = c.delete(f"/api/v1/goals/{GOAL_ID}")

    app.dependency_overrides.clear()
    # user_id do model (USER_A) != user_id do current_user (USER_B) → False → 404
    assert response.status_code == 404


# ------------------------------------------------------------------ #
#  progress_pct — regras da especificação                             #
# ------------------------------------------------------------------ #

def test_response_progress_pct_null_when_current_amount_null(client_a, mock_session):
    """Quando current_amount é null, progress_pct deve ser null."""
    model = make_goal_model()
    model.current_amount = None
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["current_amount"] is None
    assert data["progress_pct"] is None


def test_response_progress_pct_zero_when_current_zero(client_a, mock_session):
    """Quando current_amount=0 e target>0, progress_pct=0.0."""
    model = make_goal_model()
    model.current_amount = 0.0
    model.target_amount = 30000.0
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["current_amount"] == 0.0
    assert data["progress_pct"] == 0.0


def test_response_progress_pct_calculated(client_a, mock_session):
    """progress_pct calculado corretamente."""
    model = make_goal_model()
    model.current_amount = 15000.0
    model.target_amount = 30000.0
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 200
    data = response.json()
    assert abs(data["progress_pct"] - 50.0) < 0.01


def test_response_progress_pct_capped_at_100(client_a, mock_session):
    """progress_pct não deve ultrapassar 100%."""
    model = make_goal_model()
    model.current_amount = 40000.0
    model.target_amount = 30000.0
    mock_session.execute.return_value = MockResult([model])

    response = client_a.get(f"/api/v1/goals/{GOAL_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["progress_pct"] == 100.0
