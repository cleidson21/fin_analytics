from typing import Optional, List
from uuid import UUID
from datetime import datetime

from backend.application.ports.account_repository import IAccountRepository
from backend.domain.entities.account import Account
from backend.domain.enums.provider_type import ProviderType
from backend.application.queries.get_accounts import GetAccountsQuery

def _entity_to_legacy_dict(acc: Account) -> dict:
    return {
        "provider": acc.provider.value if hasattr(acc.provider, "value") else str(acc.provider),
        "external_id": acc.external_id,
        "name": acc.name,
        "type": acc.type,
        "subtype": acc.subtype,
        "bank": None,
        "connector": None,
        "credit_metadata_json": None,
        "last_sync": datetime.utcnow()
    }

class PierreLegacyAccountAdapter(IAccountRepository):
    def __init__(self):
        from backend.domains.pierre.repository import AccountRepository as LegacyAccRepo
        from backend.database.session import SessionLocal
        self._legacy_repo = LegacyAccRepo()
        self._SessionLocal = SessionLocal

    async def create(self, account: Account) -> Account:
        return await self.upsert(account)

    async def get_by_id(self, id: UUID) -> Optional[Account]:
        return None

    async def get_by_external_id(self, external_id: str, provider: ProviderType) -> Optional[Account]:
        db = self._SessionLocal()
        try:
            provider_str = provider.value if hasattr(provider, "value") else str(provider)
            existing = self._legacy_repo.get_by_external_id(db, provider_str, external_id)
            if not existing:
                return None
            # Return dummy entity just to satisfy interface if needed,
            # but PierreImportService only uses upsert which doesn't check existence first
            return Account(
                id=UUID(int=0), user_id=UUID(int=0), provider=provider,
                name=existing.name, type=existing.type
            )
        finally:
            db.close()

    async def list(self, user_id: UUID, filters: GetAccountsQuery) -> List[Account]:
        return []

    async def update_balance(self, id: UUID, balance, updated_at) -> Account:
        return None

    async def upsert(self, account: Account) -> Account:
        acc_dict = _entity_to_legacy_dict(account)
        db = self._SessionLocal()
        try:
            self._legacy_repo.upsert(db, acc_dict)
            db.commit()
        finally:
            db.close()
        return account
