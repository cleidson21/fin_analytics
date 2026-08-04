from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.infrastructure.persistence.models.transaction import TransactionModel

class GetInstallmentsUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, user_id: str) -> List[Dict[str, Any]]:
        # Fetch all transactions that have a purchase_id and installment_count > 1
        result = await self.session.execute(
            select(TransactionModel)
            .where(TransactionModel.user_id == user_id)
            .where(TransactionModel.installment_count > 1)
            .where(TransactionModel.purchase_id != None)
        )
        transactions = list(result.scalars().all())
        
        # Group by purchase_id
        grouped = {}
        for tx in transactions:
            pid = str(tx.purchase_id)
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(tx)
            
        installments = []
        for pid, txs in grouped.items():
            txs = sorted(txs, key=lambda x: x.installment_current or 0)
            last_tx = txs[-1]
            first_tx = txs[0]
            
            total_installments = last_tx.installment_count or 1
            current_installment = last_tx.installment_current or 1
            first_installment_found = first_tx.installment_current or 1
            installment_amount = float(last_tx.amount)
            
            total_estimated = installment_amount * total_installments
            already_paid = sum(float(t.amount) for t in txs)
            remaining = max(0, total_estimated - already_paid)
            
            is_active = current_installment < total_installments
            
            projected_end_date = None
            if last_tx.transaction_date and current_installment > 0:
                months_left = total_installments - current_installment
                # simplistic month addition
                month = last_tx.transaction_date.month - 1 + months_left
                year = last_tx.transaction_date.year + month // 12
                month = month % 12 + 1
                
                months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                projected_end_date = f"{months[month-1]} {year}"
            
            installments.append({
                "purchase_id": pid,
                "base_name": last_tx.description,
                "original_name": last_tx.original_description,
                "date": last_tx.transaction_date.isoformat() if last_tx.transaction_date else "",
                "installment_amount": installment_amount,
                "current_installment": current_installment,
                "first_installment_found": first_installment_found,
                "total_installments": total_installments,
                "total_estimated": total_estimated,
                "already_paid": already_paid,
                "remaining": remaining,
                "projected_end_date": projected_end_date,
                "is_active": is_active,
            })
            
        # Sort by active first, then date descending
        installments.sort(key=lambda x: (not x["is_active"], x["date"]), reverse=True)
        return installments
