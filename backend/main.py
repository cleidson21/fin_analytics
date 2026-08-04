from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.base import Base
from backend.database.engine import engine
from backend.domains.pierre.router import router as pierre_router
from backend.domains.pierre.read_router import router as read_router

# Ensure all V3 tables exist on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fin Analytics V3", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sprint 1 — Importação Pierre
app.include_router(pierre_router, prefix="/api/v1")

# Sprint 2 — Leitura (Read Models)
app.include_router(read_router, prefix="/api/v1")
