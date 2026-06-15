from app.repositories.base import BaseRepository
from app.models.core_finance import Transaction, Category, Goal, Subscription, User
from sqlalchemy.orm import Session
from typing import Any, Optional

class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    # Note: Transaction uses id_economico as primary key
    def get(self, db: Session, id: Any) -> Optional[Transaction]:
        return db.query(self.model).filter(self.model.id_economico == id).first()

class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)

class GoalRepository(BaseRepository[Goal]):
    def __init__(self):
        super().__init__(Goal)

class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self):
        super().__init__(Subscription)

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
