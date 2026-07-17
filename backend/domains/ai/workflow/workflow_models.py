from pydantic import BaseModel
from typing import Optional

class WorkflowStatusDTO(BaseModel):
    daily: str
    weekly: str
    monthly: str
    last_execution: str
    running: bool

class WorkflowRunRequest(BaseModel):
    workflow: str

class WorkflowRunRecord(BaseModel):
    id: str
    workflow_name: str
    workflow_type: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    trigger: str
    executed_steps: str
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
