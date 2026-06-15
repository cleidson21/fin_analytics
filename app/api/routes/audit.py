from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import require_admin
from app.api.schemas.admin import AuditRun, AuditRollback
from app.api.services.governance_service import GovernanceService

router = APIRouter(dependencies=[Depends(require_admin)])
service = GovernanceService()

@router.get("", response_model=list[AuditRun])
def get_audit(status_filter: str = "ALL"):
    return service.get_audit_runs(status_filter)

@router.get("/rollbacks", response_model=list[AuditRollback])
def get_audit_rollbacks():
    return service.get_audit_rollbacks()

@router.get("/{run_id}", response_model=AuditRun)
def get_audit_run(run_id: str):
    runs = service.get_audit_runs("ALL")
    for r in runs:
        if r['id'] == run_id:
            return r
    raise HTTPException(status_code=404, detail="Run not found")
