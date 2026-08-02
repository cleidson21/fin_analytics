from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from backend.domains.pierre.models import (
    Account,
    Transaction,
    Category,
    SyncState,
    SyncHistory
)

class AccountRepository:
    def upsert(self, db: Session, account_data: dict) -> Account:
        stmt = insert(Account).values(**account_data)
        
        # Exclude primary keys from update
        update_dict = {c.name: c for c in stmt.excluded if c.name not in ['provider', 'external_id']}
        
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=['provider', 'external_id'],
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['provider', 'external_id'])
            
        db.execute(stmt)
        return self.get_by_external_id(db, account_data['provider'], account_data['external_id'])

    def get_by_external_id(self, db: Session, provider: str, external_id: str) -> Optional[Account]:
        return db.query(Account).filter(Account.provider == provider, Account.external_id == external_id).first()

    def list_all(self, db: Session) -> List[Account]:
        return db.query(Account).all()


class TransactionRepository:
    def upsert(self, db: Session, transaction_data: dict) -> Transaction:
        stmt = insert(Transaction).values(**transaction_data)
        
        update_dict = {c.name: c for c in stmt.excluded if c.name not in ['provider', 'external_id']}
        
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=['provider', 'external_id'],
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['provider', 'external_id'])
            
        db.execute(stmt)
        return self.get_by_external_id(db, transaction_data['provider'], transaction_data['external_id'])

    def get_by_external_id(self, db: Session, provider: str, external_id: str) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.provider == provider, Transaction.external_id == external_id).first()

    def list_all(self, db: Session) -> List[Transaction]:
        return db.query(Transaction).all()


class CategoryRepository:
    def insert_if_not_exists(self, db: Session, category_data: dict) -> Category:
        stmt = insert(Category).values(**category_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=['provider', 'name'])
        db.execute(stmt)
        return db.query(Category).filter(Category.provider == category_data['provider'], Category.name == category_data['name']).first()

    def list_all(self, db: Session) -> List[Category]:
        return db.query(Category).all()


class SyncRepository:
    def update_state(self, db: Session, state_data: dict) -> SyncState:
        stmt = insert(SyncState).values(**state_data)
        update_dict = {c.name: c for c in stmt.excluded if c.name != 'provider'}
        
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=['provider'],
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['provider'])
            
        db.execute(stmt)
        return self.get_state(db, state_data['provider'])

    def get_state(self, db: Session, provider: str) -> Optional[SyncState]:
        return db.query(SyncState).filter(SyncState.provider == provider).first()

    def create_history(self, db: Session, history_data: dict) -> SyncHistory:
        history = SyncHistory(**history_data)
        db.add(history)
        db.flush()
        return history

    def list_history(self, db: Session, provider: str) -> List[SyncHistory]:
        return db.query(SyncHistory).filter(SyncHistory.provider == provider).all()
