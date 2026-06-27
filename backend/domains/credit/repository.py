from sqlalchemy.engine import Connection
from sqlalchemy import text
from typing import Dict, Any, List
from backend.domains.credit.dto import InstallmentsDashboardDTO, SubscriptionsDashboardDTO, InstallmentItem, SubscriptionItem

class CreditRepository:
    def __init__(self, db: Connection):
        self.db = db

    def get_installments_dashboard(self, month: str) -> InstallmentsDashboardDTO:
        # We query the `installments` joined with `installment_plans` for the target month
        query = """
            SELECT 
                i.id as installment_id,
                p.description,
                i.amount,
                i.installment_number,
                p.total_installments,
                m.name as merchant_name,
                i.expected_date,
                i.status
            FROM installments i
            JOIN installment_plans p ON i.installment_plan_id = p.id
            LEFT JOIN merchants m ON p.merchant_id = m.id
            WHERE i.expected_date LIKE :month || '%'
            ORDER BY i.expected_date ASC
        """
        rows = self.db.execute(text(query), {"month": month}).fetchall()
        
        items = []
        global_estimated = 0.0
        active = 0
        finished = 0
        
        for row in rows:
            amt_float = row.amount / 100.0
            global_estimated += amt_float
            active += 1
            if row.installment_number == row.total_installments:
                finished += 1
                
            items.append(InstallmentItem(
                id=row.installment_id,
                description=row.description,
                amount=amt_float,
                installment_number=row.installment_number,
                total_installments=row.total_installments,
                merchant_name=row.merchant_name,
                expected_date=row.expected_date,
                status=row.status
            ))
            
        return InstallmentsDashboardDTO(
            month=month,
            active_installments=active,
            finished_installments=finished,
            global_estimated=global_estimated,
            items=items
        )

    def get_subscriptions_dashboard(self, month: str) -> SubscriptionsDashboardDTO:
        # Mocking for now, as subscriptions are inferred from categories (e.g. streaming, telecom, etc.)
        query = """
            SELECT 
                t.id, 
                t.original_description as description, 
                t.amount, 
                c.name as category, 
                m.name as merchant_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            LEFT JOIN merchants m ON t.merchant_id = m.id
            WHERE t.date LIKE :month || '%'
              AND c.slug IN ('housing.telecom', 'services.streaming')
              AND t.type = 'OUT'
        """
        rows = self.db.execute(text(query), {"month": month}).fetchall()
        
        items = []
        monthly_total = 0.0
        
        for row in rows:
            amt_float = row.amount / 100.0
            monthly_total += amt_float
            items.append(SubscriptionItem(
                id=row.id,
                description=row.description,
                amount=amt_float,
                category=row.category,
                merchant_name=row.merchant_name
            ))
            
        return SubscriptionsDashboardDTO(
            month=month,
            active_count=len(items),
            monthly_total=monthly_total,
            annual_projection=monthly_total * 12,
            items=items
        )
