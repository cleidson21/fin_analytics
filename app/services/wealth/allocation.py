from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.wealth import Position
from typing import Dict, Any

class AllocationService:
    def __init__(self, db: Session):
        self.db = db

    def get_allocation(self) -> Dict[str, Any]:
        """Agrupamento por classe de ativo e cálculo percentual."""
        latest_date = self.db.query(func.max(Position.data_snapshot)).scalar()
        if not latest_date:
            return {"total_portfolio": 0.0, "classes": {}}

        positions = self.db.query(Position).filter(Position.data_snapshot == latest_date).all()
        
        total_portfolio = sum(p.total_atual for p in positions)
        
        if total_portfolio == 0:
            return {"total_portfolio": 0.0, "classes": {}}

        classes_dict = {}
        for p in positions:
            classe = p.classe_ativo or "NAO_CLASSIFICADO"
            if classe not in classes_dict:
                classes_dict[classe] = {"total_atual": 0.0, "percentual": 0.0}
            
            classes_dict[classe]["total_atual"] += p.total_atual

        # Calcular percentuais
        for classe, data in classes_dict.items():
            data["percentual"] = (data["total_atual"] / total_portfolio) * 100

        return {
            "total_portfolio": total_portfolio,
            "classes": classes_dict
        }
