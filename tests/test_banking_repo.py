import sqlite3
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Create directories
os.makedirs("backend/domains/banking", exist_ok=True)
with open("backend/domains/banking/__init__.py", "w") as f:
    pass

with open("backend/domains/banking/dto.py", "w") as f:
    f.write("""from pydantic import BaseModel
from typing import Optional

class TransactionDTO(BaseModel):
    id: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    macro_categoria: str = "Outros"
    parcelamento: str = ""
    observacao: Optional[str] = None
    data_transacao: Optional[str] = None
    valor: Optional[float] = None
    valor_cents: Optional[int] = None
""")

with open("backend/domains/banking/repository.py", "w") as f:
    f.write("""from sqlalchemy.engine import Connection
from sqlalchemy import text
from typing import List, Dict, Any, Optional

class TransactionRepository:
    def __init__(self, db: Connection):
        self.db = db
        
    def find_all(self, limit: int = 50, offset: int = 0, search: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        query = '''
            SELECT 
                t.id, 
                COALESCE(t.normalized_desc, t.original_description) as descricao,
                c.name as categoria,
                p.name as macro_categoria,
                '' as parcelamento,
                t.original_description as observacao,
                t.date as data_transacao,
                t.amount as valor_cents
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN categories p ON c.parent_id = p.id
            WHERE t.is_ignored = 0
        '''
        params = {}
        
        if start_date:
            query += " AND t.date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND t.date <= :end_date"
            params["end_date"] = end_date
        if search:
            query += " AND (t.normalized_desc LIKE :search OR t.original_description LIKE :search)"
            params["search"] = f"%{search}%"
            
        count_query = f"SELECT COUNT(*) FROM ({query})"
        total = self.db.execute(text(count_query), params).scalar()
        
        query += " ORDER BY t.date DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        rows = self.db.execute(text(query), params).fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row.id,
                "descricao": row.descricao,
                "categoria": row.categoria,
                "macro_categoria": row.macro_categoria or "Outros",
                "parcelamento": row.parcelamento,
                "observacao": row.observacao,
                "data_transacao": row.data_transacao,
                "valor_cents": row.valor_cents,
                "valor": row.valor_cents / 100.0 if row.valor_cents is not None else None
            })
            
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }
""")

# Test execution
engine = create_engine("sqlite:///database/fin_analytics_v3.db")
with engine.connect() as conn:
    from backend.domains.banking.repository import TransactionRepository
    repo = TransactionRepository(conn)
    result = repo.find_all(limit=5)
    print("Test Result Total:", result["total"])
    print("Test Items Count:", len(result["items"]))
    if result["items"]:
        print("First item:", result["items"][0])
