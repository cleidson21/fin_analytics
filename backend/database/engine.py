import os
from sqlalchemy import create_engine

# The database file is stored in the project root directory.
# Hard-coded to V3 path to prevent V2 legacy DATABASE_URL from overriding it.
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fin_analytics_v3.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
