from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any

class PositionRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_positions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        # Using raw SQL inside the repository as approved, optimized for the frontend DTO
        # Left joining assets to get classe_ativo
        query = text("""
            SELECT 
                p.id, 
                p.ticker, 
                p.quantity as quantidade, 
                p.total_value as valor_atual, 
                p.total_value as valor_investido, /* Simplified for UI */
                p.reference_date as data_snapshot,
                a.asset_class as classe_ativo
            FROM position_snapshots p
            LEFT JOIN assets a ON p.ticker = a.ticker
            ORDER BY p.reference_date DESC 
            LIMIT :limit OFFSET :offset
        """)
        rows = self.session.execute(query, {"limit": limit, "offset": offset}).mappings().all()
        return [dict(r) for r in rows]

    def count_positions(self) -> int:
        return self.session.execute(text("SELECT COUNT(*) FROM position_snapshots")).scalar() or 0

class DividendRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_dividends(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = text("""
            SELECT 
                d.id as id_economico, 
                d.type as tipo_evento, 
                d.gross_amount as valor, 
                d.payment_date as data_pagamento, 
                a.ticker as ticker
            FROM dividends d 
            LEFT JOIN assets a ON d.asset_id = a.id 
            ORDER BY d.payment_date DESC 
            LIMIT :limit OFFSET :offset
        """)
        rows = self.session.execute(query, {"limit": limit, "offset": offset}).mappings().all()
        return [dict(r) for r in rows]

    def count_dividends(self) -> int:
        return self.session.execute(text("SELECT COUNT(*) FROM dividends")).scalar() or 0
