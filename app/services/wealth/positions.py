from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Dict, Any
from app.models.wealth import Position

class PositionService:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_positions(self) -> List[dict]:
        """Retorna as posições do snapshot mais recente."""
        latest_date = self.db.query(func.max(Position.data_snapshot)).scalar()
        if not latest_date:
            return []

        positions = self.db.query(Position).filter(Position.data_snapshot == latest_date).all()
        
        result = []
        for p in positions:
            result.append({
                "ticker": p.ticker,
                "quantidade": p.quantidade,
                "preco_medio": p.preco_medio,
                "total_investido": p.total_investido,
                "preco_atual": p.preco_atual,
                "total_atual": p.total_atual,
                "ganho": p.ganho,
                "classe_ativo": p.classe_ativo
            })
        return result

    def get_portfolio_summary(self) -> dict:
        """Resumo consolidado do portfolio atual."""
        latest_date = self.db.query(func.max(Position.data_snapshot)).scalar()
        if not latest_date:
            return {"total_investido": 0.0, "total_atual": 0.0, "ganho_total": 0.0, "ganho_pct": 0.0}

        summary = self.db.query(
            func.sum(Position.total_investido).label("total_investido"),
            func.sum(Position.total_atual).label("total_atual"),
            func.sum(Position.ganho).label("ganho_total")
        ).filter(Position.data_snapshot == latest_date).first()

        invested = summary.total_investido or 0.0
        current = summary.total_atual or 0.0
        ganho = summary.ganho_total or 0.0
        
        ganho_pct = (ganho / invested * 100) if invested > 0 else 0.0

        return {
            "total_investido": invested,
            "total_atual": current,
            "ganho_total": ganho,
            "ganho_pct": ganho_pct,
            "data_snapshot": latest_date
        }
