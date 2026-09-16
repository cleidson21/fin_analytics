from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.domains.pierre.models import Transaction


_MONEY_QUANTUM = Decimal("0.01")


def _normalize_money_total(value: Any) -> Decimal:
    """Normalize SQLite numeric aggregates to the transaction monetary scale."""
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)

class HealthFinancialQuery:
    """
    Certified Read-Only Query Layer para o domínio de Financial Health (Lote 10.2).

    Regras estritas:
      - Utiliza EXCLUSIVAMENTE governance_status == 'CLASSIFIED'.
      - Filtra temporalmente APENAS por transactions.date (exclusão de governed_at).
      - PENDING e IGNORAR não participam dos cálculos financeiros.
      - Valores monetários são agregados usando func.abs() para respeitar a semântica de ENTRADA/SAIDA,
        dado que valores originais podem possuir sinais arbitrários.
      - ISOLAMENTO: O schema atual (Transaction) carece de `user_id` ou vínculo direto validável na query.
        O isolamento se dá pela premissa Single-Tenant do banco SQLite atual, refletindo o comportamento
        da `GovernedFinancialQuery`. Não impõe FK inexistente.
    """

    def get_cashflow(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Decimal]:
        """
        Retorna o fluxo de caixa agregado para um período exato.
        Limites: start_date <= date < end_date
        """
        results = (
            db.query(
                Transaction.economic_classification,
                func.sum(func.abs(Transaction.amount)).label('total')
            )
            .filter(
                Transaction.governance_status == 'CLASSIFIED',
                Transaction.economic_classification.in_(['ENTRADA', 'SAIDA']),
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
            .group_by(Transaction.economic_classification)
            .all()
        )

        income = Decimal("0.00")
        expense = Decimal("0.00")
        for classification, total in results:
            if classification == 'ENTRADA':
                income = _normalize_money_total(total)
            elif classification == 'SAIDA':
                expense = _normalize_money_total(total)

        return {
            "income_total": income,
            "expense_total": expense
        }

    def get_monthly_totals(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Agrupa os totais de receitas e despesas por mês dentro do período informado.
        Limites: start_date <= date < end_date
        Retorna a string no formato 'YYYY-MM'.
        """
        results = (
            db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                Transaction.economic_classification,
                func.sum(func.abs(Transaction.amount)).label('total')
            )
            .filter(
                Transaction.governance_status == 'CLASSIFIED',
                Transaction.economic_classification.in_(['ENTRADA', 'SAIDA']),
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
            .group_by('month', Transaction.economic_classification)
            .order_by('month')
            .all()
        )

        months_data = {}
        for month_str, classification, total in results:
            if not month_str:
                continue
            if month_str not in months_data:
                months_data[month_str] = {
                    "month": month_str,
                    "income": Decimal("0.00"),
                    "expense": Decimal("0.00"),
                }

            if classification == 'ENTRADA':
                months_data[month_str]["income"] = _normalize_money_total(total)
            elif classification == 'SAIDA':
                months_data[month_str]["expense"] = _normalize_money_total(total)

        return list(months_data.values())

    def get_category_expenses(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Agrega o total de DESPESAS (SAIDA) por categoria em um período exato.
        Ignora receitas e transações não classificadas/ignoradas.
        Limites: start_date <= date < end_date

        Se category for NULL, mapeia para "Uncategorized" na saída
        sem persistir essa alteração no banco.
        """
        results = (
            db.query(
                Transaction.category,
                func.sum(func.abs(Transaction.amount)).label('total')
            )
            .filter(
                Transaction.governance_status == 'CLASSIFIED',
                Transaction.economic_classification == 'SAIDA',
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
            .group_by(Transaction.category)
            .order_by(func.sum(func.abs(Transaction.amount)).desc())
            .all()
        )

        categories_data = []
        for cat, total in results:
            categories_data.append({
                "category": cat if cat is not None else "Uncategorized",
                "expense_total": _normalize_money_total(total)
            })

        return categories_data
