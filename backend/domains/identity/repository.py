from sqlalchemy import text
from sqlalchemy.engine import Connection
from typing import Optional, Dict, Any
import uuid

class UserRepository:
    def __init__(self, db: Connection):
        self.db = db

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = text("SELECT * FROM users WHERE email = :email LIMIT 1")
        result = self.db.execute(query, {"email": email}).mappings().first()
        if result:
            return dict(result)
        return None

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = text("SELECT * FROM users WHERE id = :user_id LIMIT 1")
        result = self.db.execute(query, {"user_id": user_id}).mappings().first()
        if result:
            return dict(result)
        return None

    def create(self, email: str, name: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        query = text("""
            INSERT INTO users (id, email, name)
            VALUES (:id, :email, :name)
            RETURNING *
        """)
        result = self.db.execute(query, {"id": user_id, "email": email, "name": name}).mappings().first()
        self.db.commit()
        return dict(result)
