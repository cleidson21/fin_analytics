from datetime import date
from typing import List, Optional
from uuid import UUID

from backend.application.dtos.transaction import (
    TransactionResponseDTO, 
    CategorySummaryDTO,
    CategoryBreakdownDTO,
    KpiItemDTO,
    DashboardSummaryV2DTO,
)
from backend.infrastructure.persistence.repositories.transaction_repository import SQLAlchemyTransactionRepository
from backend.infrastructure.persistence.repositories.category_repository import SQLAlchemyCategoryRepository

def _add_months(month: str, delta: int) -> str:
    """Returns YYYY-MM shifted by delta months."""
    year, m = int(month[:4]), int(month[5:7])
    total = (year * 12 + m - 1) + delta
    return f"{total // 12}-{(total % 12) + 1:02d}"

def _kpi(current: float, previous: float) -> KpiItemDTO:
    if previous == 0:
        delta_pct = 100.0 if current > 0 else 0.0
    else:
        delta_pct = round(((current - previous) / abs(previous)) * 100, 1)
    return KpiItemDTO(current=current, previous=previous, delta_pct=delta_pct)

class GetDashboardSummaryV2UseCase:
    def __init__(self, transaction_repo: SQLAlchemyTransactionRepository):
        self.transaction_repo = transaction_repo

    async def execute(self, month: str) -> DashboardSummaryV2DTO:
        prev_month = _add_months(month, -1)
        current = await self.transaction_repo.get_monthly_totals(month)
        previous = await self.transaction_repo.get_monthly_totals(prev_month)

        receitas = _kpi(current["income"], previous["income"])
        despesas = _kpi(current["expense"], previous["expense"])
        saldo_current = current["income"] - current["expense"]
        saldo_previous = previous["income"] - previous["expense"]
        saldo_liquido = _kpi(saldo_current, saldo_previous)
        # Patrimônio: acumulado até o fim do mês (saldo cumulativo das transações)
        patrimonio = _kpi(saldo_current, saldo_previous)

        return DashboardSummaryV2DTO(
            month=month,
            receitas=receitas,
            despesas=despesas,
            saldo_liquido=saldo_liquido,
            patrimonio=patrimonio,
        )


from backend.application.ports.account_repository import IAccountRepository

class GetTransactionsUseCase:
    def __init__(self, transaction_repo: SQLAlchemyTransactionRepository, category_repo: SQLAlchemyCategoryRepository, account_repo: IAccountRepository):
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo
        self.account_repo = account_repo

    async def execute(self, user_id: UUID, page: int = 1, page_size: int = 20) -> tuple[List[TransactionResponseDTO], int]:
        transactions, total = await self.transaction_repo.find(user_id=user_id, page=page, page_size=page_size)
        
        result = []
        for t in transactions:
            category_dto = None
            if t.category_id:
                cat = await self.category_repo.get_by_id(t.category_id)
                if cat:
                    category_dto = CategorySummaryDTO(
                        id=cat.id,
                        name=cat.name,
                        slug=cat.slug,
                        icon=cat.icon,
                        color=cat.color
                    )
            
            account_name = "Account"
            if t.account_id:
                acc = await self.account_repo.get_by_id(t.account_id)
                if acc:
                    account_name = acc.name
                    
            dto = TransactionResponseDTO(
                id=t.id,
                external_id=t.external_id,
                provider=t.provider,
                account_id=t.account_id,
                account_name=account_name,
                amount=t.amount,
                direction=t.direction,
                currency_code=t.currency_code,
                description=t.description,
                category=category_dto,
                type=t.type,
                status=t.status,
                transaction_date=t.transaction_date,
                posted_date=t.posted_date,
                is_recurring=t.is_recurring,
                installment_count=t.installment_count,
                installment_current=t.installment_current,
                tags=[]
            )
            result.append(dto)
            
        return result, total


class GetTransactionDetailsUseCase:
    def __init__(self, transaction_repo: SQLAlchemyTransactionRepository, category_repo: SQLAlchemyCategoryRepository, account_repo: IAccountRepository):
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo
        self.account_repo = account_repo

    async def execute(self, transaction_id: UUID) -> Optional[TransactionResponseDTO]:
        t = await self.transaction_repo.get_by_id(transaction_id)
        if not t:
            return None
            
        category_dto = None
        if t.category_id:
            cat = await self.category_repo.get_by_id(t.category_id)
            if cat:
                category_dto = CategorySummaryDTO(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    icon=cat.icon,
                    color=cat.color
                )
        
        account_name = "Account"
        if t.account_id:
            acc = await self.account_repo.get_by_id(t.account_id)
            if acc:
                account_name = acc.name
                
        return TransactionResponseDTO(
            id=t.id,
            external_id=t.external_id,
            provider=t.provider,
            account_id=t.account_id,
            account_name=account_name,
            amount=t.amount,
            direction=t.direction,
            currency_code=t.currency_code,
            description=t.description,
            category=category_dto,
            type=t.type,
            status=t.status,
            transaction_date=t.transaction_date,
            posted_date=t.posted_date,
            is_recurring=t.is_recurring,
            installment_count=t.installment_count,
            installment_current=t.installment_current,
            tags=[]
        )

class GetCategoriesSummaryUseCase:
    def __init__(self, transaction_repo: SQLAlchemyTransactionRepository):
        self.transaction_repo = transaction_repo

    async def execute(self, user_id: UUID, month: str) -> List[CategoryBreakdownDTO]:
        breakdown = await self.transaction_repo.get_categories_breakdown(month)
        return [
            CategoryBreakdownDTO(
                category=item["category"],
                total=item["total"]
            )
            for item in breakdown
        ]

class UpdateTransactionCategoryUseCase:
    def __init__(self, transaction_repo: SQLAlchemyTransactionRepository, category_repo: SQLAlchemyCategoryRepository):
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    async def execute(self, transaction_id: UUID, macro_categoria: str, natureza: str, subnatureza: str) -> Optional[TransactionResponseDTO]:
        # 1. Look up category by name or create it
        categories = await self.category_repo.get_all(include_system=True)
        cat = next((c for c in categories if c.name.lower() == macro_categoria.lower()), None)
        
        if not cat:
            from backend.domain.entities.category import Category
            cat = Category(
                name=macro_categoria,
                slug=macro_categoria.lower().replace(" ", "-"),
                is_system=False
            )
            cat = await self.category_repo.save(cat)
            
        t = await self.transaction_repo.update_category(transaction_id, cat.id)
        if not t:
            return None
            
        # Return partial DTO for now, client only needs to know it succeeded
        return TransactionResponseDTO(
            id=t.id,
            external_id=t.external_id,
            provider=t.provider,
            account_id=t.account_id,
            account_name="Account",
            amount=t.amount,
            direction=t.direction,
            currency_code=t.currency_code,
            description=t.description,
            type=t.type,
            status=t.status,
            transaction_date=t.transaction_date,
            posted_date=t.posted_date,
            is_recurring=t.is_recurring,
            installment_count=t.installment_count,
            installment_current=t.installment_current,
            tags=[]
        )
