from sqlalchemy.engine import Connection
from sqlalchemy import text
from typing import List, Dict, Any, Optional

class TransactionRepository:
    def __init__(self, db: Connection):
        self.db = db
        
    def find_all(self, limit: int = 50, offset: int = 0, search: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        query = '''
            SELECT 
                t.id, 
                COALESCE(t.normalized_desc, t.original_description) as descricao,
                c.name as categoria,
                p.name as macro_categoria,
                '' as parcelamento,
                t.original_description as observacao,
                t.date as data_transacao,
                t.amount as valor_cents,
                t.type as natureza,
                a.name as account
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN categories p ON c.parent_id = p.id
            LEFT JOIN accounts a ON t.account_id = a.id
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
        if category:
            query += " AND c.name = :category"
            params["category"] = category
            
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
                "valor": row.valor_cents / 100.0 if row.valor_cents is not None else None,
                "date": row.data_transacao,
                "description": row.descricao,
                "category": row.categoria,
                "natureza": row.natureza,
                "account": row.account
            })
            
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }
