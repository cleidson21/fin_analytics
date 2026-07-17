from sqlalchemy.engine import Connection
from sqlalchemy import text
from typing import Dict, Any, List
import calendar
from datetime import datetime

class DashboardRepository:
    def __init__(self, db: Connection):
        self.db = db

    def get_summary(self, month: str) -> Dict[str, Any]:
        query = """
            SELECT 
              SUM(CASE WHEN type = 'IN' AND is_ignored = 0 AND is_transfer = 0 THEN amount ELSE 0 END) as income_cents,
              SUM(CASE WHEN type = 'OUT' AND is_ignored = 0 AND is_transfer = 0 AND is_investment = 0 THEN amount ELSE 0 END) as expenses_cents,
              SUM(CASE WHEN is_investment = 1 THEN amount ELSE 0 END) as investments_cents
            FROM transactions
            WHERE date LIKE :month || '%'
        """
        row = self.db.execute(text(query), {"month": month}).fetchone()
        
        income = (row.income_cents or 0) / 100.0
        expenses = (row.expenses_cents or 0) / 100.0
        investments = (row.investments_cents or 0) / 100.0
        net = income - expenses
        savings_rate = (net / income * 100) if income > 0 else 0.0

        return {
            "month": month,
            "receitas": {"current": income, "previous": 0.0, "delta_pct": 0.0},
            "despesas": {"current": expenses, "previous": 0.0, "delta_pct": 0.0},
            "saldo_liquido": {"current": net, "previous": 0.0, "delta_pct": 0.0},
            "patrimonio": {"current": investments, "previous": 0.0, "delta_pct": 0.0},
        }

    def get_pacing(self, month: str) -> Dict[str, Any]:
        budget = 10000.00
        
        query = """
            SELECT SUM(amount) as expenses_cents
            FROM transactions
            WHERE date LIKE :month || '%' 
              AND type = 'OUT' 
              AND is_ignored = 0 
              AND is_transfer = 0 
              AND is_investment = 0
        """
        row = self.db.execute(text(query), {"month": month}).fetchone()
        spent = (row.expenses_cents or 0) / 100.0
        
        try:
            year, m = map(int, month.split('-'))
            days_total = calendar.monthrange(year, m)[1]
            now = datetime.now()
            if now.year == year and now.month == m:
                days_elapsed = now.day
            elif (year < now.year) or (year == now.year and m < now.month):
                days_elapsed = days_total
            else:
                days_elapsed = 0
        except:
            days_total = 30
            days_elapsed = 30

        projected = (spent / days_elapsed * days_total) if days_elapsed > 0 else 0.0

        return {
            "current_month": month,
            "previous_month": "",
            "current_expenses": spent,
            "previous_expenses": 0.0,
            "delta_percentage": 0.0,
            "trend": "ESTAVEL",
            "severity": "NORMAL",
            "message": "Dentro do orçamento",
            "daily_data": []
        }

    def get_heatmap(self, month: str) -> List[Dict[str, Any]]:
        query = """
            SELECT date, SUM(amount) as total_cents, COUNT(id) as count
            FROM transactions
            WHERE date LIKE :month || '%' 
              AND type = 'OUT' 
              AND is_ignored = 0 
              AND is_transfer = 0 
              AND is_investment = 0
            GROUP BY date
            ORDER BY date ASC
        """
        rows = self.db.execute(text(query), {"month": month}).fetchall()
        return [
            {"date": r.date, "amount": str(r.total_cents / 100.0), "intensity": r.count}
            for r in rows
        ]

    def get_categories(self, month: str) -> List[Dict[str, Any]]:
        query = """
            SELECT c.name as category, SUM(t.amount) as total_cents
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.date LIKE :month || '%' 
              AND t.type = 'OUT' 
              AND t.is_ignored = 0 
              AND t.is_transfer = 0 
              AND t.is_investment = 0
            GROUP BY c.name
            ORDER BY total_cents DESC
        """
        rows = self.db.execute(text(query), {"month": month}).fetchall()
        return [
            {"category": r.category, "total": r.total_cents / 100.0}
            for r in rows
        ]

    def get_catalog(self) -> Dict[str, List[Any]]:
        cat_query = "SELECT id, name, type FROM categories"
        merch_query = "SELECT id, name FROM merchants"
        acc_query = "SELECT id, name FROM accounts"
        
        categories = [r.name for r in self.db.execute(text(cat_query)).fetchall()]
        merchants = [r.name for r in self.db.execute(text(merch_query)).fetchall()]
        accounts = [r.name for r in self.db.execute(text(acc_query)).fetchall()]
        
        return {
            "categories": categories,
            "merchants": merchants,
            "accounts": accounts,
            "natures": ["INCOME", "EXPENSE", "TRANSFER", "INVESTMENT", "DIVIDEND"]
        }
