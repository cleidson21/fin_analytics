from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.core_finance import Goal, Transaction
from decimal import Decimal

class GoalAlert(dict):
    pass

class GoalService:
    def __init__(self, db: Session):
        self.db = db

    def check_goal_status(self, year: int, month: int) -> list[dict]:
        goals = self.db.query(Goal).filter(Goal.active == 1).all()
        results = []
        
        for goal in goals:
            # Calculate total expenses for this goal's category in the specified month
            spent_cents = self.db.query(func.sum(Transaction.valor_cents)).filter(
                Transaction.natureza == 'EXPENSE',
                Transaction.category_id == goal.category_id,
                extract('year', Transaction.data) == year,
                extract('month', Transaction.data) == month
            ).scalar() or 0
            
            spent = float(spent_cents) / 100.0
            limit = float(goal.limit_cents) / 100.0
            
            pct_used = (spent / limit * 100) if limit > 0 else 0
            
            status = 'OK'
            severity = 'INFO'
            
            if pct_used >= 100:
                status = 'EXCEEDED'
                severity = 'CRITICAL'
            elif pct_used >= 80:
                status = 'WARNING'
                severity = 'WARNING'
                
            results.append({
                "category_id": goal.category_id,
                "limit_amount": limit,
                "spent_amount": spent,
                "percentage_used": round(pct_used, 2),
                "status": status,
                "severity": severity,
                "configured_severity": goal.severity_level
            })
            
        return results
