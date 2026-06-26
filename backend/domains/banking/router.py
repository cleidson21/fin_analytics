from fastapi import APIRouter, Depends, Query
from sqlalchemy.engine import Connection
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from backend.shared.db import get_db_connection
from backend.domains.identity.router import get_current_user
from backend.domains.banking.repository import TransactionRepository
from backend.domains.banking.dashboard_repository import DashboardRepository
from backend.domains.banking.dto import TransactionDTO

router = APIRouter(tags=["Banking"])

class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionDTO]
    total: int
    limit: int
    offset: int

@router.get("/transactions", response_model=PaginatedTransactionsResponse)
def get_transactions(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    category: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
    db: Connection = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    repo = TransactionRepository(db)
    result = repo.find_all(
        limit=limit, 
        offset=offset, 
        search=search, 
        start_date=startDate, 
        end_date=endDate,
        category=category
    )
    return result

@router.get("/dashboard/summary-v2")
def get_dashboard_summary(month: str, db: Connection = Depends(get_db_connection), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = DashboardRepository(db)
    return repo.get_summary(month)

@router.get("/dashboard/pacing-v2")
def get_dashboard_pacing(month: str, db: Connection = Depends(get_db_connection), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = DashboardRepository(db)
    return repo.get_pacing(month)

@router.get("/dashboard/heatmap")
def get_dashboard_heatmap(month: str, db: Connection = Depends(get_db_connection), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = DashboardRepository(db)
    return repo.get_heatmap(month)

@router.get("/dashboard/categories")
def get_dashboard_categories(month: str, db: Connection = Depends(get_db_connection), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = DashboardRepository(db)
    return repo.get_categories(month)

@router.get("/catalog")
def get_catalog(db: Connection = Depends(get_db_connection), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = DashboardRepository(db)
    return repo.get_catalog()
