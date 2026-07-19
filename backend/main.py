from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.engine import engine
from backend.database.base import Base
from backend.database.session import SessionLocal
from backend.core.container import get_bootstrap_admin
from backend.api.routers import dev

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

app = FastAPI(title="FIN Analytics", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dev.router)
