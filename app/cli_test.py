"""Small CLI smoke test for the analytical service layer."""

from __future__ import annotations

import sys
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from repositories.transacoes_repository import TransacoesRepository
from services.finance_service import FinanceService


def _format_money(value: Decimal) -> str:
	"""Format Decimal values as a human-friendly currency string."""

	quantized = value.quantize(Decimal("0.01"))
	formatted = f"{quantized:,.2f}"
	return f"R$ {formatted.replace(',', 'X').replace('.', ',').replace('X', '.')}"


def _print_section(title: str) -> None:
	print()
	print(title)
	print("-" * len(title))


def main() -> None:
	"""Run a formatted analytical preview for the current period."""

	repository = TransacoesRepository()
	repository.init_tables()
	service = FinanceService(repository)

	today = date.today()
	start_date = today.replace(day=1)
	_, last_day = monthrange(today.year, today.month)
	end_date = today.replace(day=last_day)

	print(f"Período analisado: {start_date.isoformat()} -> {end_date.isoformat()}")

	cashflow = service.get_cashflow_summary(start_date, end_date)
	expenses = service.get_expenses_breakdown(start_date, end_date)
	savings = service.get_savings_metrics(start_date, end_date)
	investments = service.get_investment_summary(start_date, end_date)

	_print_section("Cashflow")
	print(f"Receitas      : {_format_money(cashflow.receitas)}")
	print(f"Gastos        : {_format_money(cashflow.gastos)}")
	print(f"Saldo líquido : {_format_money(cashflow.saldo_liquido)}")

	_print_section("Top Gastos por Categoria")
	if not expenses:
		print("Sem gastos no período.")
	else:
		for item in expenses:
			print(f"- {item.categoria:<24} {_format_money(item.total):>15}  ({item.percentual.quantize(Decimal('0.01'))}%)")

	_print_section("Métricas de Poupança")
	print(f"Receitas               : {_format_money(savings.receitas)}")
	print(f"Gastos                 : {_format_money(savings.gastos)}")
	print(f"Investimentos          : {_format_money(savings.investimentos)}")
	print(f"Taxa de poupança       : {savings.taxa_poupanca_percentual.quantize(Decimal('0.01'))}%")

	_print_section("Resumo de Investimentos")
	print(f"Aportes    : {_format_money(investments.aportes)}")
	print(f"Dividendos : {_format_money(investments.dividendos)}")
	print(f"Total      : {_format_money(investments.total)}")

	repository.close()


if __name__ == "__main__":
	main()