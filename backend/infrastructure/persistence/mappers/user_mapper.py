from backend.domain.entities.user import User
from backend.infrastructure.persistence.models.user import UserModel


class UserMapper:
    """
    Mapper para converter a entidade de domínio User para o modelo ORM UserModel e vice-versa.
    Não contém lógica de negócio ou de banco de dados.
    """

    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Converte UserModel (ORM) -> User (Domain)"""
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_verified=model.is_verified,
            role=model.role,
            created_at=model.created_at,
            last_login_at=model.last_login_at,
        )

    @staticmethod
    def to_orm(entity: User) -> UserModel:
        """Converte User (Domain) -> UserModel (ORM)"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            role=entity.role,
            created_at=entity.created_at,
            last_login_at=entity.last_login_at,
        )
