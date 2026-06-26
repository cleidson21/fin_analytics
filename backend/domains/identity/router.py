from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.engine import Connection
from backend.shared.db import get_db_connection
from backend.domains.identity.repository import UserRepository
from backend.domains.identity.service import AuthService
from jose import jwt, JWTError
from backend.shared.config import settings
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_auth_service(db: Connection = Depends(get_db_connection)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

def get_current_user(token: str = Depends(oauth2_scheme), db: Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    repo = UserRepository(db)
    user = repo.find_by_id(user_id)
    if user is None:
        raise credentials_exception
        
    # Mapping for frontend contract
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "username": user["email"],
        "role": "admin"
    }

@router.post("/login")
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)):
    result = auth_service.authenticate_and_seed(form_data.username, form_data.password)
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "token": result["token"],
        "user": result["user"]
    }

@router.get("/me")
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user
