from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.shared.db import get_db_connection
from backend.domains.identity.router import router as auth_router
from backend.domains.banking.router import router as banking_router

from backend.domains.credit.router import router as credit_router
from backend.domains.investments.router import router as investments_router
from backend.domains.market_data.router import router as market_data_router
from backend.domains.ai.workflow.workflow_scheduler import WorkflowScheduler
from backend.domains.ai.workflow.workflow_repository import WorkflowRepository
from backend.domains.ai.workflow.workflow_service import WorkflowService
from backend.domains.ai.workflow.workflow_router import router as workflow_router
from backend.domains.governance.router import router as governance_router
from backend.domains.ai.router import router as ai_router
from backend.domains.ai.dashboard.dashboard_router import router as dashboard_router
from backend.domains.ai.events.event_registry import EventRegistry
from backend.domains.ai.plugins.plugin_manager import PluginManager
from backend.domains.ai.plugins.plugin_router import router as plugin_router
app = FastAPI(title="FinAnalytics V3", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scheduler instance
global_scheduler = None

@app.on_event("startup")
def startup_event():
    PluginManager.initialize_all()
    global global_scheduler
    service = WorkflowService(WorkflowRepository())
    global_scheduler = WorkflowScheduler(service)
    global_scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    global global_scheduler
    if global_scheduler:
        global_scheduler.stop()
    PluginManager.shutdown_all()


app.include_router(auth_router, prefix="/api/v1")
app.include_router(banking_router, prefix="/api/v1")
app.include_router(credit_router, prefix="/api/v1")
app.include_router(investments_router, prefix="/api/v1/investments")
app.include_router(market_data_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(plugin_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(governance_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health_check(db=Depends(get_db_connection)):
    try:
        # Tenta executar uma query simples para validar a conexão
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "db": db_status
    }
