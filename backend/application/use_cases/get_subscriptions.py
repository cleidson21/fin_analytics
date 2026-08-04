from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.infrastructure.persistence.models.transaction import TransactionModel

class GetSubscriptionsUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, user_id: str) -> List[Dict[str, Any]]:
        # Fetch all transactions that are recurring
        result = await self.session.execute(
            select(TransactionModel)
            .where(TransactionModel.user_id == user_id)
            .where(TransactionModel.is_recurring == True)
        )
        transactions = list(result.scalars().all())
        
        # Group by description
        grouped = {}
        for tx in transactions:
            name = tx.description
            if name not in grouped:
                grouped[name] = []
            grouped[name].append(tx)
            
        subscriptions = []
        for name, txs in grouped.items():
            txs = sorted(txs, key=lambda x: x.transaction_date)
            last_tx = txs[-1]
            
            # Simple assumption: 1 transaction per month means monthly subscription
            frequency = "MONTHLY"
            status = "ACTIVE"
            
            subscriptions.append({
                "id": str(last_tx.id),
                "name": name,
                "amount": float(last_tx.amount),
                "frequency": frequency,
                "status": status,
                "last_payment_date": last_tx.transaction_date.isoformat() if last_tx.transaction_date else None,
                "category": last_tx.provider_metadata.get("pierre_category") if last_tx.provider_metadata else "Serviços",
            })
            
        subscriptions.sort(key=lambda x: x["name"])
        return subscriptions
