import calendar
import re

from datetime import date
from decimal import Decimal

from app.api.schemas.dashboard import (
    CategoryComparison,
    DailyDataPoint,
    DailyHeatmap,
    DashboardSummaryV2,
    InstallmentItem,
    InstallmentsSummary,
    KpiItem,
    PacingComparison,
    PacingV2,
    SubscriptionItem,
    SubscriptionsSummary,
)
from app.core.formatters import format_money
from database.financial_repository import FinancialRepository


class AnalyticsService:
    INSTALLMENT_PATTERN = re.compile(r"(.+?)\s+(\d{1,2})\s*/\s*(\d{1,2})\s*x?\b", re.IGNORECASE)

    def __init__(self):
        self.queries = FinancialRepository()

    def _month_filter_sql(self, month: str | None) -> tuple[str, list[object]]:
        if not month:
            return "", []
        return " AND strftime('%Y-%m', data) = ?", [month]

    def _fetch_expense_rows(
        self,
        month: str | None = None,
        macro_categoria: str | None = None,
    ) -> list[dict[str, object]]:
        query = """
            SELECT
                source_line_no,
                id_economico,
                data,
                descricao_original,
                valor_cents,
                macro_categoria,
                natureza,
                source
            FROM transactions
            WHERE natureza = 'EXPENSE'
        """
        params: list[object] = []

        if macro_categoria:
            query += " AND UPPER(macro_categoria) = UPPER(?)"
            params.append(macro_categoria)

        month_sql, month_params = self._month_filter_sql(month)
        query += month_sql
        params.extend(month_params)
        query += " ORDER BY data ASC, source_line_no ASC, id_economico ASC"

        with self.queries._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def _cents_to_float(self, value: object) -> float:
        return float(Decimal(str(value or 0)) / Decimal("100"))

    def _installment_bucket(self, amount: float) -> int:
        return int(round(amount / 10))

    def _parse_money(self, value: str) -> float:
        normalized = value.replace("R$", "").replace(".", "").replace(" ", "").replace(",", ".").strip()
        return float(Decimal(normalized or "0"))

    def _add_months(self, source_date: date, months: int) -> date:
        total_months = (source_date.year * 12 + (source_date.month - 1)) + months
        year = total_months // 12
        month = (total_months % 12) + 1
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(source_date.day, last_day))

    def _format_month_year_pt(self, source_date: date) -> str:
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        return f"{months[source_date.month - 1]} {source_date.year}"

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

    def _to_kpi_item(self, current: Decimal, previous: Decimal) -> KpiItem:
        current_float = float(current)
        previous_float = float(previous)

        if previous == 0:
            delta_pct = 0.0
        else:
            delta_pct = float(((current - previous) / abs(previous)) * Decimal("100"))

        return KpiItem(
            current=current_float,
            previous=previous_float,
            delta_pct=delta_pct,
        )

    def _month_minus_one(self, month: str) -> str:
        year, month_number = map(int, month.split("-"))
        if month_number == 1:
            return f"{year - 1}-12"
        return f"{year}-{month_number - 1:02d}"

    def get_summary_v2(self, month: str) -> DashboardSummaryV2:
        previous_month = self._month_minus_one(month)

        df_curr = self.queries.get_cashflow_summary(month=month)
        df_prev = self.queries.get_cashflow_summary(month=previous_month)

        receitas_curr = Decimal(str(df_curr.loc[df_curr["natureza"] == "INCOME", "total"].sum())) if not df_curr.empty else Decimal("0")
        despesas_curr = abs(Decimal(str(df_curr.loc[df_curr["natureza"] == "EXPENSE", "total"].sum()))) if not df_curr.empty else Decimal("0")

        receitas_prev = Decimal(str(df_prev.loc[df_prev["natureza"] == "INCOME", "total"].sum())) if not df_prev.empty else Decimal("0")
        despesas_prev = abs(Decimal(str(df_prev.loc[df_prev["natureza"] == "EXPENSE", "total"].sum()))) if not df_prev.empty else Decimal("0")

        saldo_curr = receitas_curr - despesas_curr
        saldo_prev = receitas_prev - despesas_prev

        patrimonio_curr = Decimal(str(self.queries.get_current_net_worth()))
        
        try:
            portfolio_summary = self.queries.get_portfolio_evolution_summary()
            rentabilidade_pct = float(portfolio_summary.get("rentabilidade_acumulada", 0.0))
        except Exception:
            rentabilidade_pct = 0.0

        patrimonio_kpi = KpiItem(
            current=float(patrimonio_curr),
            previous=0.0,
            delta_pct=rentabilidade_pct
        )

        return DashboardSummaryV2(
            month=month,
            receitas=self._to_kpi_item(receitas_curr, receitas_prev),
            despesas=self._to_kpi_item(despesas_curr, despesas_prev),
            saldo_liquido=self._to_kpi_item(saldo_curr, saldo_prev),
            patrimonio=patrimonio_kpi,
        )

    def get_subscriptions_summary(self, month: str) -> SubscriptionsSummary:
        rows = self._fetch_expense_rows(month=month, macro_categoria="ASSINATURAS")

        items = [
            SubscriptionItem(
                original_name=str(row["descricao_original"] or ""),
                date=str(row["data"]),
                amount=self._cents_to_float(row["valor_cents"]),
            )
            for row in rows
        ]

        monthly_total = sum(item.amount for item in items)
        active_count = len(items)
        average_per_service = monthly_total / active_count if active_count else 0.0

        return SubscriptionsSummary(
            month=month,
            active_count=active_count,
            monthly_total=monthly_total,
            annual_projection=monthly_total * 12,
            average_per_service=average_per_service,
            items=items,
        )

    def get_installments_summary(self, month: str | None = None) -> InstallmentsSummary:
        rows = self._fetch_expense_rows(month=None)
        grouped: dict[tuple[str, int, int], list[dict[str, object]]] = {}

        for row in rows:
            description = str(row["descricao_original"] or "").strip()
            match = self.INSTALLMENT_PATTERN.search(description)
            if not match:
                continue

            base_name = match.group(1).strip()
            current_installment = int(match.group(2))
            total_installments = int(match.group(3))

            if total_installments <= 1 or current_installment < 0 or current_installment > total_installments:
                continue

            row_date = date.fromisoformat(str(row["data"]))
            installment_amount = self._cents_to_float(row["valor_cents"])
            bucket = self._installment_bucket(installment_amount)
            
            purchase_date = self._add_months(row_date, -(current_installment - 1))
            purchase_month = f"{purchase_date.year}-{purchase_date.month:02d}"
            
            key = (base_name.lower(), total_installments, bucket, purchase_month)
            sequences = grouped.setdefault(key, [])

            matched_sequence: dict[str, object] | None = None
            for sequence in sequences:
                last_x = int(sequence["current_installment"])
                if current_installment > last_x:
                    matched_sequence = sequence
                    break

            if matched_sequence is None:
                seq_index = len(sequences)
                purchase_id = f"{base_name.lower()}_{total_installments}x_{bucket}_{purchase_month}_{seq_index}"
                matched_sequence = {
                    "purchase_id": purchase_id,
                    "first_installment_found": current_installment,
                    "base_name": base_name,
                    "original_name": description,
                    "date": str(row["data"]),
                    "date_obj": row_date,
                    "installment_amount": installment_amount,
                    "current_installment": current_installment,
                    "total_installments": total_installments,
                    "total_estimated": installment_amount * total_installments,
                    "already_paid": installment_amount * current_installment,
                    "remaining": installment_amount * (total_installments - current_installment),
                    "bucket": bucket,
                }
                sequences.append(matched_sequence)
            else:
                first_found = int(matched_sequence["first_installment_found"])
                if current_installment < first_found:
                    first_found = current_installment
                matched_sequence.update(
                    {
                        "first_installment_found": first_found,
                        "original_name": description,
                        "date": str(row["data"]),
                        "date_obj": row_date,
                        "installment_amount": installment_amount,
                        "current_installment": current_installment,
                        "total_installments": total_installments,
                        "total_estimated": installment_amount * total_installments,
                        "already_paid": installment_amount * current_installment,
                        "remaining": installment_amount * (total_installments - current_installment),
                    }
                )

        normalized_items: list[dict[str, object]] = []
        for sequences in grouped.values():
            normalized_items.extend(sequences)

        # ── Mês de contexto ────────────────────────────────────────────
        # Usamos a maior data de transação importada no banco como referência
        # de "mês corrente". Isso evita dependência do relógio do servidor e
        # garante consistência com os dados reais.
        context_date: date | None = None
        for item in normalized_items:
            d = item["date_obj"]
            if context_date is None or d > context_date:
                context_date = d

        # Fallback para a data real do sistema se não houver transações
        if context_date is None:
            context_date = date.today()

        # Tupla (ano, mês) do mês de contexto para comparação
        context_ym = (context_date.year, context_date.month)

        # ── Calcular projected_end_date por item ────────────────────────
        # Para cada grupo, projetamos a data final: last_date + meses_restantes.
        # Se current == total, meses_restantes == 0, data projetada == last_date.
        for item in normalized_items:
            last_x: int = int(item["current_installment"])
            total_y: int = int(item["total_installments"])
            last_date_val: date = item["date_obj"]
            meses_restantes = total_y - last_x
            if meses_restantes > 0:
                projected = self._add_months(last_date_val, meses_restantes)
            else:
                projected = last_date_val  # última parcela — mês de referência é o próprio
            item["projected_end_date"] = self._format_month_year_pt(projected)
            item["projected_end_date_obj"] = projected

        # ── Lógica de status com "sobrevivência no mês" ─────────────────
        # Uma parcela X/X paga NESTE mês permanece ATIVA até o fim do mês.
        # Só migra para 'finalizadas' quando o mês de contexto for estritamente
        # posterior ao mês da última transação registada.
        def _is_active(norm: dict[str, object]) -> bool:
            last_x = int(norm["current_installment"])
            total_y = int(norm["total_installments"])
            if last_x < total_y:
                return True  # ainda tem parcelas futuras → definitivamente ativo
            # last_x == total_y: verifica se ainda estamos no mesmo mês
            last_date_obj: date = norm["date_obj"]
            item_ym = (last_date_obj.year, last_date_obj.month)
            return item_ym >= context_ym  # mesmo mês ou posterior → ativo

        # Construir InstallmentItems com o novo campo projected_end_date
        exclude_keys = {"date_obj", "bucket", "projected_end_date_obj"}

        def _to_item(norm: dict[str, object]) -> InstallmentItem:
            fields = {k: v for k, v in norm.items() if k not in exclude_keys}
            fields["is_active"] = _is_active(norm)
            return InstallmentItem(**fields)

        all_items = [_to_item(n) for n in normalized_items]
        all_items.sort(key=lambda i: (i.remaining, i.total_installments, i.current_installment), reverse=True)

        active_items = [i for i in all_items if i.is_active]
        finished_items = [i for i in all_items if not i.is_active]

        global_estimated = sum(i.total_estimated for i in active_items)
        global_paid = sum(i.already_paid for i in active_items)
        global_remaining = sum(i.remaining for i in active_items)

        # ── last_installment_date global = máximo das projected_end_date dos ativos ──
        active_projections: list[date] = [
            norm["projected_end_date_obj"]
            for norm in normalized_items
            if _is_active(norm)
        ]

        last_installment_date: str | None = None
        if active_projections:
            last_installment_date = self._format_month_year_pt(max(active_projections))

        return InstallmentsSummary(
            month=month or "",
            active_installments=len(active_items),
            finished_installments=len(finished_items),
            global_estimated=global_estimated,
            global_paid=global_paid,
            global_remaining=global_remaining,
            last_installment_date=last_installment_date,
            items=all_items,
        )

    def get_pacing_v2(self, month: str) -> PacingV2:
        base = self.get_expense_pacing(month)
        previous_month = self._month_minus_one(month)

        current_daily_df = self.queries.get_daily_expenses(month)
        previous_daily_df = self.queries.get_daily_expenses(previous_month)

        current_daily_map: dict[str, Decimal] = {}
        previous_daily_map: dict[str, Decimal] = {}

        if not current_daily_df.empty:
            for _, row in current_daily_df.iterrows():
                current_daily_map[row["data"]] = abs(Decimal(str(row["total"])))

        if not previous_daily_df.empty:
            for _, row in previous_daily_df.iterrows():
                previous_daily_map[row["data"]] = abs(Decimal(str(row["total"])))

        year, month_number = map(int, month.split("-"))
        prev_year, prev_month_number = map(int, previous_month.split("-"))

        _, current_last_day = calendar.monthrange(year, month_number)
        _, previous_last_day = calendar.monthrange(prev_year, prev_month_number)

        daily_data: list[DailyDataPoint] = []
        for day in range(1, current_last_day + 1):
            current_date = f"{year}-{month_number:02d}-{day:02d}"

            prev_amount = Decimal("0")
            if day <= previous_last_day:
                previous_date = f"{prev_year}-{prev_month_number:02d}-{day:02d}"
                prev_amount = previous_daily_map.get(previous_date, Decimal("0"))

            daily_data.append(
                DailyDataPoint(
                    date=date.fromisoformat(current_date).isoformat(),
                    current_amount=float(current_daily_map.get(current_date, Decimal("0"))),
                    previous_amount=float(prev_amount),
                )
            )

        current_expenses = float(Decimal(str(base.current_expenses)))
        previous_expenses = float(Decimal(str(base.previous_expenses)))
        delta_percentage = float(Decimal(str(base.delta_percentage)))

        return PacingV2(
            current_month=base.current_month,
            previous_month=base.previous_month,
            current_expenses=current_expenses,
            previous_expenses=previous_expenses,
            delta_percentage=delta_percentage,
            trend=base.trend,
            severity=base.severity,
            message=base.message,
            daily_data=daily_data,
        )