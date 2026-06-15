from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.wealth import Dividend, Position
from datetime import date
from typing import Dict, Any

class DividendService:
    def __init__(self, db: Session):
        self.db = db

    def get_dividends_summary(self) -> Dict[str, float]:
        """Calcula total de dividendos recebidos e projetados (futuros)."""
        today = date.today()
        
        # Recebidos (<= hoje)
        received = self.db.query(func.sum(Dividend.valor_liquido)).filter(
            Dividend.data_pagamento <= today
        ).scalar() or 0.0
        
        # Projetados (> hoje)
        projected = self.db.query(func.sum(Dividend.valor_liquido)).filter(
            Dividend.data_pagamento > today
        ).scalar() or 0.0
        
        return {
            "received": float(received),
            "projected": float(projected)
        }

    def calculate_yoc(self) -> Dict[str, Any]:
        """
        Yield on Cost (YOC) = (Dividendos Recebidos / Capital Investido) * 100
        Calcula o YOC geral da carteira e por ativo.
        """
        today = date.today()
        
        # Total investido na carteira no snapshot mais recente
        latest_date = self.db.query(func.max(Position.data_snapshot)).scalar()
        if not latest_date:
            return {"portfolio_yoc": 0.0, "assets": {}}

        positions = self.db.query(Position).filter(Position.data_snapshot == latest_date).all()
        portfolio_invested = sum(p.total_investido for p in positions)
        
        if portfolio_invested == 0:
            return {"portfolio_yoc": 0.0, "assets": {}}

        # Dividendos totais recebidos
        total_dividends = self.db.query(func.sum(Dividend.valor_liquido)).filter(
            Dividend.data_pagamento <= today
        ).scalar() or 0.0
        
        portfolio_yoc = (total_dividends / portfolio_invested) * 100

        # Dividendos por ticker
        dividends_by_ticker = self.db.query(
            Dividend.ticker, 
            func.sum(Dividend.valor_liquido).label('total')
        ).filter(Dividend.data_pagamento <= today).group_by(Dividend.ticker).all()
        
        div_dict = {d.ticker: float(d.total) for d in dividends_by_ticker}
        
        assets_yoc = {}
        for p in positions:
            if p.total_investido > 0:
                received = div_dict.get(p.ticker, 0.0)
                yoc = (received / p.total_investido) * 100
                assets_yoc[p.ticker] = {
                    "invested": p.total_investido,
                    "dividends_received": received,
                    "yoc_pct": yoc
                }

        return {
            "portfolio_yoc": portfolio_yoc,
            "assets": assets_yoc
        }
