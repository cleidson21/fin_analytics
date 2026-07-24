from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.application.commands.authenticate_user_command import AuthenticateUserCommand
from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.api.dependencies.auth import resolve_authenticate_user
from backend.application.exceptions.invalid_credentials_error import InvalidCredentialsError
from backend.application.exceptions.user_not_found_error import UserNotFoundError
from backend.application.exceptions.unauthorized_error import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(
    request: LoginRequest,
    use_case: AuthenticateUserUseCase = Depends(resolve_authenticate_user)
):
    command = AuthenticateUserCommand(email=request.email, password=request.password)
    try:
        result = await use_case.execute(command)
        return result
    except (InvalidCredentialsError, UserNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
