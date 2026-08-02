from backend.database.session import SessionLocal
from backend.domains.pierre.repository import (
    AccountRepository,
    TransactionRepository,
    CategoryRepository,
    SyncRepository
)

class AccountService:
    def __init__(self):
        self.repository = AccountRepository()

    def save(self, account_data: dict):
        with SessionLocal() as db:
            result = self.repository.upsert(db, account_data)
            db.commit()
            db.refresh(result)
            db.expunge(result)
            return result

    def get(self, provider: str, external_id: str):
        with SessionLocal() as db:
            result = self.repository.get_by_external_id(db, provider, external_id)
            if result:
                db.expunge(result)
            return result

    def list_all(self):
        with SessionLocal() as db:
            results = self.repository.list_all(db)
            db.expunge_all()
            return results

class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()

    def save(self, transaction_data: dict):
        with SessionLocal() as db:
            result = self.repository.upsert(db, transaction_data)
            db.commit()
            db.refresh(result)
            db.expunge(result)
            return result

    def get(self, provider: str, external_id: str):
        with SessionLocal() as db:
            result = self.repository.get_by_external_id(db, provider, external_id)
            if result:
                db.expunge(result)
            return result

    def list_all(self):
        with SessionLocal() as db:
            results = self.repository.list_all(db)
            db.expunge_all()
            return results

class CategoryService:
    def __init__(self):
        self.repository = CategoryRepository()

    def save_if_not_exists(self, category_data: dict):
        with SessionLocal() as db:
            result = self.repository.insert_if_not_exists(db, category_data)
            db.commit()
            db.refresh(result)
            db.expunge(result)
            return result

    def list_all(self):
        with SessionLocal() as db:
            results = self.repository.list_all(db)
            db.expunge_all()
            return results

class SyncService:
    def __init__(self):
        self.repository = SyncRepository()

    def update_state(self, state_data: dict):
        with SessionLocal() as db:
            result = self.repository.update_state(db, state_data)
            db.commit()
            db.refresh(result)
            db.expunge(result)
            return result

    def get_state(self, provider: str):
        with SessionLocal() as db:
            result = self.repository.get_state(db, provider)
            if result:
                db.expunge(result)
            return result

    def create_history(self, history_data: dict):
        with SessionLocal() as db:
            result = self.repository.create_history(db, history_data)
            db.commit()
            db.refresh(result)
            db.expunge(result)
            return result

    def list_history(self, provider: str):
        with SessionLocal() as db:
            results = self.repository.list_history(db, provider)
            db.expunge_all()
            return results
