import pytest
from unittest.mock import MagicMock
from app.api.services.auth_service import AuthService
from app.api.deps import verify_password, get_password_hash

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_repo):
    service = AuthService()
    service.repo = mock_repo
    return service

def test_get_user_by_username_exists(auth_service, mock_repo):
    mock_repo.get_user_by_username.return_value = {
        "username": "admin",
        "password_hash": "hashed",
        "role": "ADMIN",
        "active": 1
    }
    
    user = auth_service.get_user_by_username("admin")
    assert user is not None
    assert user["username"] == "admin"
    mock_repo.get_user_by_username.assert_called_once_with("admin")

def test_get_user_by_username_not_found(auth_service, mock_repo):
    mock_repo.get_user_by_username.return_value = None
    user = auth_service.get_user_by_username("unknown")
    assert user is None

def test_create_user(auth_service, mock_repo):
    mock_repo.create_user.return_value = "uuid-123"
    
    uid = auth_service.create_user("newuser", "email@test.com", "hash", "VIEWER")
    assert uid == "uuid-123"
    mock_repo.create_user.assert_called_once_with("newuser", "email@test.com", "hash", "VIEWER")

def test_autenticacao_valida():
    password = "MySecretPassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True

def test_autenticacao_invalida():
    password = "MySecretPassword123"
    hashed = get_password_hash(password)
    assert verify_password("WrongPassword", hashed) is False
