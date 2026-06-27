from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection
from typing import Dict, Any

from backend.shared.db import get_db_connection
from backend.domains.identity.router import get_current_user
from backend.domains.credit.repository import CreditRepository
from backend.domains.credit.dto import InstallmentsDashboardDTO, SubscriptionsDashboardDTO

router = APIRouter(tags=["Credit"])

@router.get("/dashboard/installments", response_model=InstallmentsDashboardDTO)
def get_installments_dashboard(
    month: str, 
    db: Connection = Depends(get_db_connection), 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    repo = CreditRepository(db)
    return repo.get_installments_dashboard(month)

@router.get("/dashboard/subscriptions", response_model=SubscriptionsDashboardDTO)
def get_subscriptions_dashboard(
    month: str, 
    db: Connection = Depends(get_db_connection), 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    repo = CreditRepository(db)
    return repo.get_subscriptions_dashboard(month)
