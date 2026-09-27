from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.base import Base
from backend.database.engine import engine
from backend.domains.pierre.router import router as pierre_router
from backend.domains.pierre.read_router import router as read_router
from backend.domains.pierre.governance_router import router as governance_router
from backend.api.routers.dashboard import router as dashboard_router
from backend.api.routers.auth import router as auth_router
from backend.api.routers.governance import router as api_governance_router
from backend.domains.pierre.installments_router import router as installments_router
from backend.api.routers.investments import router as investments_router
from backend.api.routers.financial_health import router as financial_health_router
from backend.api.routers.planning import router as planning_router

# Ensure all V3 tables exist on startup (including GovernanceAuditLog from Sprint 2.8)
# Structural migrations (ALTER TABLE) are managed via versioned SQL scripts in database/migrations/
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fin Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")

# Sprint 1 — Importação Pierre
app.include_router(pierre_router, prefix="/api/v1")

# Sprint 2 — Leitura (Read Models)
app.include_router(read_router, prefix="/api/v1")

# Sprint 3 — Parcelamentos (Proxy)
app.include_router(installments_router, prefix="/api/v1/pierre")

# Sprint 2.8 — Governança Financeira Manual
app.include_router(governance_router, prefix="/api/v1")

# Dashboard — KPIs, Pacing, Heatmap, Categorias
app.include_router(dashboard_router, prefix="/api/v1")

# API Governance (Imports & Dashboard)
app.include_router(api_governance_router, prefix="/api/v1")

# Investments
app.include_router(investments_router, prefix="/api/v1")

# Financial Health (Wealth Intelligence Lote 10.2.6)
app.include_router(financial_health_router, prefix="/api/v1")

# Goals (Wealth Intelligence Lote 10.1)
from backend.api.routers.goals import router as goals_router
app.include_router(goals_router, prefix="/api/v1")

# Planning API foundation (10.3.8-B): endpoints arrive in later microphases.
app.include_router(planning_router, prefix="/api/v1")
