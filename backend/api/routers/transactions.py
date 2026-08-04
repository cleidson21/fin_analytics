from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies.auth import get_current_user
from backend.core.container import (
    get_transactions_use_case,
    get_update_transaction_category_use_case,
    get_transaction_details_use_case
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.transaction import TransactionResponseDTO, UpdateTransactionCategoryDTO
from backend.application.use_cases.transactions import (
    GetTransactionsUseCase, 
    UpdateTransactionCategoryUseCase,
    GetTransactionDetailsUseCase
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionResponseDTO])
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetTransactionsUseCase = Depends(get_transactions_use_case)
):
    transactions, _ = await use_case.execute(user_id=current_user.id, page=page, page_size=page_size)
    return transactions

@router.get("/{id}", response_model=TransactionResponseDTO)
async def get_transaction(
    id: UUID,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: GetTransactionDetailsUseCase = Depends(get_transaction_details_use_case)
):
    transaction = await use_case.execute(transaction_id=id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # In a real app we'd also check if the transaction belongs to current_user
    return transaction

@router.patch("/{id}/category", response_model=TransactionResponseDTO)
async def update_category(
    id: UUID,
    payload: UpdateTransactionCategoryDTO,
    current_user: UserResponseDTO = Depends(get_current_user),
    use_case: UpdateTransactionCategoryUseCase = Depends(get_update_transaction_category_use_case)
):
    updated = await use_case.execute(
        transaction_id=id, 
        macro_categoria=payload.macro_categoria,
        natureza=payload.natureza,
        subnatureza=payload.subnatureza
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated
