from fastapi import FastAPI, Depends
from sqlalchemy import text
from backend.shared.db import get_db_connection
from backend.domains.identity.router import router as auth_router
from backend.domains.banking.router import router as banking_router

from backend.domains.credit.router import router as credit_router
from backend.domains.investments.router import router as investments_router

app = FastAPI(title="FinAnalytics V3", version="1.0.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(banking_router, prefix="/api/v1")
app.include_router(credit_router, prefix="/api/v1")
app.include_router(investments_router, prefix="/api/v1/investments")

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
