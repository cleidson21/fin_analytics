from sqlalchemy import create_engine
from backend.shared.config import settings

# Conexão com SQLite
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

def get_db_connection():
    with engine.connect() as connection:
        yield connection
