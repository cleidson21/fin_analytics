from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.core_finance import Transaction
from app.schemas.dashboard import PacingComparison, PacingV2, DailyDataPoint
from decimal import Decimal
import calendar
from datetime import date

class CashflowService:
    def __init__(self, db: Session):
        self.db = db

    def _get_expenses_sum(self, year: int, month: int, up_to_day: int = None) -> float:
        query = self.db.query(func.sum(Transaction.valor)).filter(
            Transaction.natureza == 'EXPENSE',
            extract('year', Transaction.data) == year,
            extract('month', Transaction.data) == month
        )
        if up_to_day:
            query = query.filter(extract('day', Transaction.data) <= up_to_day)
        
        result = query.scalar()
        return float(result) if result else 0.0

    def _get_income_sum(self, year: int, month: int, up_to_day: int = None) -> float:
        query = self.db.query(func.sum(Transaction.valor)).filter(
            Transaction.natureza == 'INCOME',
            extract('year', Transaction.data) == year,
            extract('month', Transaction.data) == month
        )
        if up_to_day:
            query = query.filter(extract('day', Transaction.data) <= up_to_day)
        
        result = query.scalar()
        return float(result) if result else 0.0

    def _get_daily_expenses(self, year: int, month: int) -> dict:
        results = self.db.query(
            extract('day', Transaction.data).label('day'),
            func.sum(Transaction.valor).label('total')
        ).filter(
            Transaction.natureza == 'EXPENSE',
            extract('year', Transaction.data) == year,
            extract('month', Transaction.data) == month
        ).group_by('day').all()
        
        return {int(r.day): float(r.total) for r in results}

    def _format_money(self, amount: float) -> str:
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def get_expense_pacing(self, current_month: str) -> PacingComparison:
        year, month = map(int, current_month.split("-"))
        prev_year = year if month > 1 else year - 1
        prev_month = month - 1 if month > 1 else 12
        previous_month_str = f"{prev_year}-{prev_month:02d}"

        exp_curr_val = abs(self._get_expenses_sum(year, month))
        exp_prev_val = abs(self._get_expenses_sum(prev_year, prev_month))

        exp_curr = Decimal(str(exp_curr_val))
        exp_prev = Decimal(str(exp_prev_val))

        if exp_prev == 0:
            delta_pct = Decimal("100.00") if exp_curr > 0 else Decimal("0.00")
        else:
            delta_pct = ((exp_curr - exp_prev) / exp_prev) * Decimal("100")

        delta_fmt = f"{float(delta_pct):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        if delta_pct > 0:
            trend = "up"
            severity = "danger"
            message = f"Seus gastos subiram {delta_fmt}% em relação ao mês anterior."
        elif delta_pct < 0:
            trend = "down"
            severity = "good"
            message = f"Excelente! Seus gastos caíram {f'{abs(float(delta_pct)):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')}% em relação ao mês passado."
        else:
            trend = "stable"
            severity = "warning"
            message = "Seus gastos ficaram estáveis em relação ao mês anterior."

        return PacingComparison(
            current_month=current_month,
            previous_month=previous_month_str,
            current_expenses=self._format_money(float(exp_curr)),
            previous_expenses=self._format_money(float(exp_prev)),
            delta_percentage=delta_fmt,
            trend=trend,
            severity=severity,
            message=message
        )

    def get_pacing_v2(self, month: str) -> PacingV2:
        base = self.get_expense_pacing(month)
        
        year, month_number = map(int, month.split("-"))
        prev_year, prev_month_number = map(int, base.previous_month.split("-"))

        current_daily_map = self._get_daily_expenses(year, month_number)
        previous_daily_map = self._get_daily_expenses(prev_year, prev_month_number)

        _, current_last_day = calendar.monthrange(year, month_number)
        _, previous_last_day = calendar.monthrange(prev_year, prev_month_number)

        daily_data = []
        for day in range(1, current_last_day + 1):
            current_date = f"{year}-{month_number:02d}-{day:02d}"
            
            prev_amount = 0.0
            if day <= previous_last_day:
                prev_amount = previous_daily_map.get(day, 0.0)

            daily_data.append(
                DailyDataPoint(
                    date=date.fromisoformat(current_date).isoformat(),
                    current_amount=abs(current_daily_map.get(day, 0.0)),
                    previous_amount=abs(prev_amount)
                )
            )

        return PacingV2(
            current_month=base.current_month,
            previous_month=base.previous_month,
            current_expenses=float(base.current_expenses.replace('R$ ', '').replace('.', '').replace(',', '.')),
            previous_expenses=float(base.previous_expenses.replace('R$ ', '').replace('.', '').replace(',', '.')),
            delta_percentage=float(base.delta_percentage.replace('R$ ', '').replace('.', '').replace(',', '.')),
            trend=base.trend,
            severity=base.severity,
            message=base.message,
            daily_data=daily_data
        )
