import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt

from backend.application.ports.i_jwt_service import IJWTService


class JWTService(IJWTService):
    """
    Serviço de infraestrutura para criação e validação de tokens JWT.
    Independente de Frameworks, Domain e Banco de dados.
    Recebe suas configurações (secrets e tempo de expiração) via construtor
    (injeção de dependência).
    """

    def __init__(self, secret: str, expire_minutes: int, refresh_expire_days: int) -> None:
        self._secret = secret
        self._expire_minutes = expire_minutes
        self._refresh_expire_days = refresh_expire_days
        self._algorithm = "HS256"

    def create_access_token(self, user_id: str) -> str:
        """
        Gera um JWT access_token de curta duração.
        Claims obrigatórias conforme docs/48_SECURITY.md: sub, exp, iat, jti.
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self._expire_minutes)
        claims = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access"
        }
        return jwt.encode(claims, self._secret, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """
        Gera um JWT refresh_token de longa duração.
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=self._refresh_expire_days)
        claims = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        }
        return jwt.encode(claims, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decodifica o token sem validar a assinatura.
        Útil para ler o JTI ou claims antes da validação estrita.
        """
        return jwt.get_unverified_claims(token)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica a assinatura e expiração do token e retorna as claims.
        """
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as e:
            raise ValueError(f"Token inválido ou expirado: {str(e)}")
