from fastapi import HTTPException, status
from backend.shared.config import settings
from backend.shared.security import create_access_token
from backend.domains.identity.repository import UserRepository
from typing import Dict, Any

class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate_and_seed(self, email: str, password: str) -> Dict[str, Any]:
        # Validate against environment config
        if email != settings.ADMIN_EMAIL or password != settings.ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Seed or fetch user
        user = self.repository.find_by_email(email)
        if not user:
            user = self.repository.create(email=email, name="Admin User")

        # Generate JWT token
        access_token = create_access_token(subject=user["id"])
        
        # Frontend Contract requires user to have username and role
        frontend_user = {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "username": user["email"],
            "role": "admin"
        }

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "token": access_token,  # Compatible with Frontend Contract
            "user": frontend_user
        }
