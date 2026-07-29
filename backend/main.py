from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.engine import engine
from backend.database.base import Base
from backend.database.session import SessionLocal
from backend.core.container import get_bootstrap_admin
from backend.api.routers import dev, auth, accounts, transactions, dashboard, categories, governance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup - cria as tabelas e executa bootstrap
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with SessionLocal() as session:
        bootstrap = get_bootstrap_admin(session)
        await bootstrap.execute()
        await session.commit()
    
    yield
    # Cleanup

app = FastAPI(
    title="FIN Analytics V2",
    description="API para gestão financeira pessoal com integração Pierre",
    version="2.0.0",
    lifespan=lifespan,
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrando routers
app.include_router(auth.router)
app.include_router(dev.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(categories.router)
app.include_router(governance.router)
