from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import accounts, catalog, dashboard, governance, investments, transactions


app = FastAPI(
    title="FinAnalytics V2 - Wealth API",
    description="Motor Financeiro (Core Backend) para o frontend Pierre/Next.js",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catálogo"])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["Governança"])
app.include_router(investments.router, prefix="/api/v1/investments", tags=["Investimentos"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transações"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Contas"])