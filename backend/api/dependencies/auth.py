from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from uuid import UUID

from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.core.container import get_authenticate_user_use_case
from backend.core.config import settings
from backend.database.session import SessionLocal
from backend.api.dependencies.database import get_db_session
from backend.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository
from backend.application.dtos.user_response_dto import UserResponseDTO

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def resolve_authenticate_user(session=Depends(get_db_session)) -> AuthenticateUserUseCase:
    """Resolve a injeção do caso de uso de autenticação para o FastAPI."""
    return get_authenticate_user_use_case(session)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> UserResponseDTO:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except JWTError:
        raise credentials_exception
        
    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
        
    return UserResponseDTO(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )
