from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'fin_analytics_v2.db')
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# For SQLite, we must enforce foreign keys for CASCADE to work
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')

from sqlalchemy import event
event.listen(engine, 'connect', _fk_pragma_on_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
