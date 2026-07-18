from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from backend.shared.config import settings

# Conexão com SQLite
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

Base = declarative_base()

def get_db_connection():
    with engine.connect() as connection:
        yield connection

from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

