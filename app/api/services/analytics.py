from decimal import Decimal

from app.api.schemas.dashboard import CategoryComparison, DailyHeatmap, PacingComparison
from app.core.formatters import format_money
from database.queries import FinancialQueries


class AnalyticsService:
    def __init__(self):
        self.queries = FinancialQueries()

    def get_expense_pacing(self, current_month: str) -> PacingComparison:
        """Calcula o ritmo de gastos mês a mês e devolve dados prontos para a UI."""
        year, month = map(int, current_month.split("-"))
        previous_month = f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"

        df_curr = self.queries.get_cashflow_summary(month=current_month)
        df_prev = self.queries.get_cashflow_summary(month=previous_month)

        raw_curr = df_curr.loc[df_curr["natureza"] == "EXPENSE", "total"].sum() if not df_curr.empty else 0
        raw_prev = df_prev.loc[df_prev["natureza"] == "EXPENSE", "total"].sum() if not df_prev.empty else 0

        exp_curr = abs(Decimal(str(raw_curr)))
        exp_prev = abs(Decimal(str(raw_prev)))

        if exp_prev == 0:
            delta_pct = Decimal("100.00") if exp_curr > 0 else Decimal("0.00")
        else:
            delta_pct = ((exp_curr - exp_prev) / exp_prev) * Decimal("100")

        delta_fmt = format_money(delta_pct)

        if delta_pct > 0:
            trend = "up"
            severity = "danger"
            message = f"Seus gastos subiram {delta_fmt}% em relação ao mês anterior."
        elif delta_pct < 0:
            trend = "down"
            severity = "good"
            message = f"Excelente! Seus gastos caíram {format_money(abs(delta_pct))}% em relação ao mês passado."
        else:
            trend = "stable"
            severity = "warning"
            message = "Seus gastos ficaram estáveis em relação ao mês anterior."

        return PacingComparison(
            current_month=current_month,
            previous_month=previous_month,
            current_expenses=format_money(exp_curr),
            previous_expenses=format_money(exp_prev),
            delta_percentage=delta_fmt,
            trend=trend,
            severity=severity,
            message=message,
        )

    def get_monthly_heatmap(self, month: str) -> list[DailyHeatmap]:
        import calendar
        from datetime import date

        year, month_number = map(int, month.split("-"))
        _, last_day = calendar.monthrange(year, month_number)
        df_daily = self.queries.get_daily_expenses(month)

        expenses_dict = {}
        max_amount = Decimal("0.00")

        if not df_daily.empty:
            for _, row in df_daily.iterrows():
                value = abs(Decimal(str(row["total"])))
                expenses_dict[row["data"]] = value
                if value > max_amount:
                    max_amount = value

        heatmap = []
        for day in range(1, last_day + 1):
            date_str = f"{year}-{month_number:02d}-{day:02d}"
            amount = expenses_dict.get(date_str, Decimal("0.00"))
            intensity = float(amount / max_amount) if max_amount > 0 else 0.0

            heatmap.append(
                DailyHeatmap(
                    date=date.fromisoformat(date_str),
                    amount=format_money(amount),
                    intensity=round(intensity, 2),
                )
            )

        return heatmap

    def get_categories_comparison(self, current_month: str) -> list[CategoryComparison]:
        year, month = map(int, current_month.split("-"))
        previous_month = f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"

        df_curr = self.queries.get_expenses_by_category(month=current_month)
        df_prev = self.queries.get_expenses_by_category(month=previous_month)

        curr_dict = (
            {row["macro_categoria"]: abs(row["total"]) for _, row in df_curr.iterrows()}
            if not df_curr.empty
            else {}
        )
        prev_dict = (
            {row["macro_categoria"]: abs(row["total"]) for _, row in df_prev.iterrows()}
            if not df_prev.empty
            else {}
        )

        comparisons = []
        for category, curr_value in curr_dict.items():
            prev_value = prev_dict.get(category, 0)

            curr_fmt = format_money(curr_value)
            prev_fmt = format_money(prev_value)

            if Decimal(prev_fmt) == 0:
                delta = Decimal("100.00") if Decimal(curr_fmt) > 0 else Decimal("0.00")
            else:
                delta = ((Decimal(curr_fmt) - Decimal(prev_fmt)) / Decimal(prev_fmt)) * 100

            severity = "good"
            if delta > 20:
                severity = "danger"
            elif delta > 0:
                severity = "warning"

            comparisons.append(
                CategoryComparison(
                    category=category,
                    current_amount=curr_fmt,
                    previous_amount=prev_fmt,
                    delta_percentage=format_money(delta),
                    severity=severity,
                )
            )

        return sorted(comparisons, key=lambda item: item.current_amount, reverse=True)