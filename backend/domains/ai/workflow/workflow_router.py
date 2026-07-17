from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.workflow.workflow_models import WorkflowStatusDTO, WorkflowRunRequest
from backend.domains.ai.workflow.workflow_service import WorkflowService
from backend.domains.ai.workflow.workflow_repository import WorkflowRepository

router = APIRouter(prefix="/workflow", tags=["Workflow Engine"])

def get_workflow_service():
    repository = WorkflowRepository()
    return WorkflowService(repository)

@router.get("/status", response_model=WorkflowStatusDTO)
def get_workflow_status(
    db: Session = Depends(get_db_connection),
    service: WorkflowService = Depends(get_workflow_service)
):
    """
    Retorna o status atual dos pipelines internos.
    """
    return service.get_status(db)

@router.post("/run")
def trigger_workflow_run(
    request: WorkflowRunRequest,
    service: WorkflowService = Depends(get_workflow_service)
):
    """
    Aciona manualmente um workflow (daily, weekly, monthly). Apenas para fins administrativos.
    """
    if request.workflow == "daily":
        service.run_daily(trigger="manual")
    elif request.workflow == "weekly":
        service.run_weekly(trigger="manual")
    elif request.workflow == "monthly":
        service.run_monthly(trigger="manual")
    else:
        return {"error": "Invalid workflow type. Use daily, weekly, or monthly."}
        
    return {"message": f"Workflow {request.workflow} triggered successfully."}
