from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import internal, accounts, catalog, dashboard, governance, investments, transactions, database_admin, audit, prompts, auth, learning
from database.bootstrap_governance import init_governance_db

# Inicializar governance.db
init_governance_db()

app = FastAPI(
    title="FinAnalytics V2 - Wealth API",
    description="Motor Financeiro (Core Backend) para o frontend Pierre/Next.js",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

@app.middleware("http")
async def payload_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAYLOAD_BYTES:
        return Response(status_code=413, content="Payload Too Large")
    return await call_next(request)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catálogo"])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["Governança"])
app.include_router(database_admin.router, prefix="/api/v1/governance/database", tags=["Database Admin"])
app.include_router(audit.router, prefix="/api/v1/governance/audit", tags=["Auditoria"])
app.include_router(investments.router, prefix="/api/v1/investments", tags=["Investimentos"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transações"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Contas"])
app.include_router(prompts.router, prefix="/api/v1/governance/prompts", tags=["Prompts"])
app.include_router(learning.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1/internal", tags=["Internal"])
