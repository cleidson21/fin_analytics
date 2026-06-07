from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import require_admin
from app.api.schemas.admin import AuditRun, AuditRollback
from database.queries import FinancialQueries

router = APIRouter(dependencies=[Depends(require_admin)])
queries = FinancialQueries()

@router.get("", response_model=list[AuditRun])
def get_audit(status_filter: str = "ALL"):
    return queries.get_audit_runs(status_filter)

@router.get("/rollbacks", response_model=list[AuditRollback])
def get_audit_rollbacks():
    return queries.get_audit_rollbacks()

@router.get("/{run_id}", response_model=AuditRun)
def get_audit_run(run_id: str):
    runs = queries.get_audit_runs("ALL")
    for r in runs:
        if r['id'] == run_id:
            return r
    raise HTTPException(status_code=404, detail="Run not found")
