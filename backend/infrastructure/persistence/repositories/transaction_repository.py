from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.domain.entities.transaction import Transaction
from backend.domain.entities.category import Category
from backend.infrastructure.persistence.models.transaction import TransactionModel
from backend.infrastructure.persistence.models.category import CategoryModel

class SQLAlchemyTransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def find(self, 
                   user_id: UUID, 
                   page: int = 1, 
                   page_size: int = 20, 
                   start_date: Optional[date] = None, 
                   end_date: Optional[date] = None,
                   category_id: Optional[UUID] = None) -> Tuple[List[Transaction], int]:
        
        # In a real scenario we'd join with accounts to check user_id. 
        # For this slice, we assume transactions are filtered correctly or we join on Account.
        # But we don't have AccountModel here yet. Let's just build the basic query.
        stmt = select(TransactionModel)
        count_stmt = select(func.count(TransactionModel.id))

        filters = []
        if start_date:
            filters.append(TransactionModel.transaction_date >= start_date)
        if end_date:
            filters.append(TransactionModel.transaction_date <= end_date)
        if category_id:
            filters.append(TransactionModel.category_id == category_id)
            
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
            
        stmt = stmt.order_by(desc(TransactionModel.transaction_date))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(stmt)
        count_result = await self.session.execute(count_stmt)
        
        models = result.scalars().all()
        total = count_result.scalar() or 0
        
        return [self._to_entity(m) for m in models], total

    async def get_monthly_totals(self, month: str) -> Dict[str, float]:
        """Returns {'income': ..., 'expense': ...} for the given YYYY-MM month."""
        import calendar
        year, m = month.split("-")
        y_int, m_int = int(year), int(m)
        _, last_day = calendar.monthrange(y_int, m_int)
        start = date(y_int, m_int, 1)
        end = date(y_int, m_int, last_day)

        income_stmt = (
            select(func.sum(TransactionModel.amount))
            .where(and_(
                TransactionModel.transaction_date >= start,
                TransactionModel.transaction_date <= end,
                TransactionModel.direction == "CREDIT"
            ))
        )
        expense_stmt = (
            select(func.sum(TransactionModel.amount))
            .where(and_(
                TransactionModel.transaction_date >= start,
                TransactionModel.transaction_date <= end,
                TransactionModel.direction == "DEBIT"
            ))
        )

        income_result = await self.session.execute(income_stmt)
        expense_result = await self.session.execute(expense_stmt)

        income = float(income_result.scalar() or 0)
        expense = float(expense_result.scalar() or 0)
        return {"income": income, "expense": expense}

    async def get_categories_breakdown(self, month: str) -> List[Dict[str, Any]]:
        """Returns [{'category': 'Food', 'total': 150.0}, ...]"""
        # month format YYYY-MM
        year, m = month.split("-")
        
        # PostgreSQL specific date_trunc or extract could be used, but since it's SQLite primarily, 
        # we can use func.strftime or just filter by dates.
        # Let's filter by start/end of month for cross-db compatibility
        import calendar
        from datetime import date
        
        y_int, m_int = int(year), int(m)
        _, last_day = calendar.monthrange(y_int, m_int)
        
        start_date = date(y_int, m_int, 1)
        end_date = date(y_int, m_int, last_day)

        stmt = (
            select(
                CategoryModel.name.label("category"),
                func.sum(TransactionModel.amount).label("total")
            )
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                and_(
                    TransactionModel.transaction_date >= start_date,
                    TransactionModel.transaction_date <= end_date,
                    TransactionModel.direction == "DEBIT" # Only expenses
                )
            )
            .group_by(CategoryModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
        )

        result = await self.session.execute(stmt)
        breakdown = []
        for row in result:
            breakdown.append({
                "category": row.category,
                "total": float(row.total)
            })
            
        return breakdown

    async def save(self, transaction: Transaction) -> Transaction:
        model = TransactionModel(
            id=transaction.id,
            provider=transaction.provider,
            account_id=transaction.account_id,
            amount=transaction.amount,
            direction=transaction.direction,
            currency_code=transaction.currency_code,
            description=transaction.description,
            type=transaction.type,
            status=transaction.status,
            transaction_date=transaction.transaction_date,
            is_recurring=transaction.is_recurring,
            hash=transaction.hash,
            external_id=transaction.external_id,
            original_description=transaction.original_description,
            category_id=transaction.category_id,
            posted_date=transaction.posted_date,
            installment_count=transaction.installment_count,
            installment_current=transaction.installment_current,
            provider_metadata=transaction.provider_metadata,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            deleted_at=transaction.deleted_at
        )
        self.session.add(model)
        await self.session.flush()
        return transaction

    async def update_category(self, transaction_id: UUID, category_id: UUID) -> Optional[Transaction]:
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
            
        model.category_id = category_id
        await self.session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            provider=model.provider,
            account_id=model.account_id,
            amount=model.amount,
            direction=model.direction,
            currency_code=model.currency_code,
            description=model.description,
            type=model.type,
            status=model.status,
            transaction_date=model.transaction_date,
            is_recurring=model.is_recurring,
            hash=model.hash,
            external_id=model.external_id,
            original_description=model.original_description,
            category_id=model.category_id,
            posted_date=model.posted_date,
            installment_count=model.installment_count,
            installment_current=model.installment_current,
            provider_metadata=model.provider_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at
        )
