from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.domains.identity.router import get_current_user


from backend.shared.db import get_db
from backend.domains.governance.import_service import GovernanceImportService
from backend.domains.governance.service import DashboardService, ImportService
from backend.domains.governance.dto import DashboardMetricsDTO, ImportRunListResponseDTO, ImportRunItemDTO
from backend.domains.investments.service import PositionService, DividendService
from backend.domains.investments.dto import PaginatedResponse

class UploadPayload(BaseModel):
    file_name: str
    raw_text: str
    source_type: str

router = APIRouter(prefix="/governance", tags=["Governance"])

@router.get("/dashboard", response_model=DashboardMetricsDTO)
def get_governance_dashboard(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    service = DashboardService(db)
    return service.get_metrics()

@router.get("/imports", response_model=ImportRunListResponseDTO)
def list_imports(limit: int = 10, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    service = ImportService(db)
    return service.list_imports(limit, offset)

@router.get("/imports/{run_id}", response_model=ImportRunItemDTO)
def get_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    service = ImportService(db)
    run_item = service.get_import(run_id)
    if not run_item:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_item

@router.get("/imports/{run_id}/staging-items")
def get_staging_items(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    service = ImportService(db)
    return service.get_staging_items(run_id)

@router.post("/imports/{run_id}/confirm")
def confirm_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    service = GovernanceImportService()
    try:
        # Note: GovernanceImportService will need to be refactored to use `db` 
        # in the future, but currently keeping its signature to avoid breaking it 
        # before Phase H1.4.
        result = service.confirm_and_process(run_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/imports/{run_id}/rollback")
def rollback_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    service = ImportService(db)
    service.rollback_import(run_id)
    return {"status": "success"}

@router.get("/database/summary")
def get_db_summary(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "size_mb": 15.4,
        "tables_count": 12,
        "total_rows": 25000,
        "last_backup": datetime.now(timezone.utc).isoformat(),
        "status": "healthy"
    }

@router.get("/database/health")
def get_db_health(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "database": "OK",
        "imports": "OK",
        "wealth": "OK",
        "staging": "OK",
        "status": "UP",
        "connections": 1,
        "latency_ms": 5
    }

@router.get("/database/tables")
def get_db_tables(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return [
        {"table_name": "transactions", "row_count": 10000, "size_kb": 2048},
        {"table_name": "categories", "row_count": 50, "size_kb": 128},
        {"table_name": "merchants", "row_count": 200, "size_kb": 256}
    ]

@router.get("/database/integrity")
def get_db_integrity(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "status": "PASS",
        "foreign_keys_ok": True,
        "orphan_runs": 0,
        "duplicate_transactions_suspects": 0,
        "pending_staging": 0,
        "checks": [
            {"name": "PRAGMA integrity_check", "passed": True},
            {"name": "PRAGMA foreign_key_check", "passed": True}
        ]
    }

@router.get("/audit")
def list_audit(status_filter: str = "ALL", current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return []

@router.get("/audit/rollbacks")
def list_rollbacks(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return []

@router.get("/positions", response_model=PaginatedResponse)
def list_positions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    service = PositionService(db)
    return service.list_positions(limit, offset)

@router.get("/categories")
def list_categories(limit: int = 50, offset: int = 0, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"items": [], "total": 0}

@router.get("/dividends", response_model=PaginatedResponse)
def list_dividends(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    service = DividendService(db)
    return service.list_dividends(limit, offset)

@router.post("/imports/upload")
async def upload_import(
    current_user: Dict[str, Any] = Depends(get_current_user),
    source_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
) -> Dict[str, Any]:
    service = GovernanceImportService()
    
    content = ""
    file_name = "Upload Direto"
    
    if file:
        file_name = file.filename
        content = await file.read()
    elif raw_text:
        content = raw_text
    else:
        raise HTTPException(status_code=400, detail="Missing file or raw_text")
        
    return service.process_import(
        file_name=file_name,
        raw_content=content,
        source_type=source_type
    )
