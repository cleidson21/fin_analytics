from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime

from backend.domains.pierre.client import PierreHTTPClient
from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO

router = APIRouter(tags=["Pierre Installments"], prefix="/installments")

def get_month_name(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        return f"{months[dt.month - 1]} {dt.year}"
    except:
        return ""

@router.get("")
async def get_installments(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    client = PierreHTTPClient()
    payload = await client.get_installments(start_date, end_date)
    
    purchases = payload.get("purchases", [])
    
    active_count = 0
    finished_count = 0
    items = []
    
    for idx, p in enumerate(purchases):
        is_active = p.get("amountRemaining", 0) > 0
        if is_active:
            active_count += 1
        else:
            finished_count += 1
            
        installments = p.get("installments", [])
        
        # Calculate projected end date based on the last installment
        projected_end_date = None
        if installments:
            last_inst = installments[-1]
            projected_end_date = get_month_name(last_inst.get("dueDate"))
            
        # Determine current installment logically
        current_installment = p.get("installmentsPaid", 0)
        if is_active and current_installment < p.get("totalInstallments", 0):
            current_installment += 1
            
        first_inst_found = installments[0].get("installmentNumber", 1) if installments else 1
        
        # Generate a unique pseudo-id for the frontend card key
        purchase_id = f"{p.get('accountId', 'account')}-{p.get('description', 'desc')}-{p.get('purchaseDate', 'date')}-{idx}"
        
        items.append({
            "purchase_id": purchase_id,
            "base_name": p.get("description", "Sem descrição"),
            "original_name": p.get("description", "Sem descrição"),
            "date": p.get("purchaseDate", ""),
            "installment_amount": p.get("installmentValue", 0),
            "current_installment": current_installment,
            "first_installment_found": first_inst_found,
            "total_installments": p.get("totalInstallments", 1),
            "total_estimated": p.get("totalAmount", 0),
            "already_paid": p.get("amountPaid", 0),
            "remaining": p.get("amountRemaining", 0),
            "projected_end_date": projected_end_date,
            "is_active": is_active,
        })
        
    return {
        "month": "Período Selecionado",
        "active_installments": active_count,
        "finished_installments": finished_count,
        "global_estimated": payload.get("totalAmount", 0),
        "global_paid": payload.get("totalAmountPaid", 0),
        "global_remaining": payload.get("totalAmountRemaining", 0),
        "last_installment_date": None,
        "items": items
    }
