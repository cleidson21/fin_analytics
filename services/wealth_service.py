"""Wealth intelligence service combining portfolio, goals, and budgets."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from models.wealth_dto import BudgetDTO, GoalDTO
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository
from services.market_service import MarketDataService


class WealthIntelligenceService:
	"""Compute wealth-centric metrics on top of repository and market data."""

	def __init__(
		self,
		wealth_repository: WealthRepository,
		transactions_repository: TransacoesRepository,
		market_data_service: MarketDataService,
	) -> None:
		self._wealth_repository = wealth_repository
		self._transactions_repository = transactions_repository
		self._market_data_service = market_data_service

	def sync_portfolio_prices(self) -> dict[str, Decimal]:
		"""Update ``FACT_POSITIONS`` with live quotes and recalculated PnL values."""

		positions = self._wealth_repository.fetch_all_positions()
		if not positions:
			return {}

		br_tickers: list[str] = []
		global_tickers: list[str] = []
		for position in positions:
			if self._is_brazilian_ticker(position.ticker):
				br_tickers.append(position.ticker)
			else:
				global_tickers.append(position.ticker)

		quotes: dict[str, Decimal] = {}
		if global_tickers:
			quotes.update(self._market_data_service.fetch_global_quotes(global_tickers))
		if br_tickers:
			quotes.update(self._market_data_service.fetch_br_quotes(br_tickers))

		for position in positions:
			current_price = quotes.get(position.ticker, position.cotacao_atual)
			pnl_absoluto = (current_price - position.preco_medio) * position.quantidade
			custo_total = position.preco_medio * position.quantidade
			if custo_total == 0:
				pnl_percentual = Decimal("0")
			else:
				pnl_percentual = (pnl_absoluto / custo_total) * Decimal("100")

			self._wealth_repository.update_position(
				{
					"ticker": position.ticker,
					"quantidade": position.quantidade,
					"preco_medio": position.preco_medio,
					"cotacao_atual": current_price,
					"pnl_absoluto": pnl_absoluto,
					"pnl_percentual": pnl_percentual,
					"dividend_yield": position.dividend_yield,
				},
			)

		return quotes

	def get_consolidated_net_worth(self) -> dict[str, Decimal]:
		"""Return total net worth combining cash balance and invested assets."""

		caixa_total = self._fetch_cash_balance()
		patrimonio_investido = Decimal("0")

		for position in self._wealth_repository.fetch_all_positions():
			patrimonio_investido += position.quantidade * position.cotacao_atual

		patrimonio_total = caixa_total + patrimonio_investido
		return {
			"caixa_total": caixa_total,
			"patrimonio_investido": patrimonio_investido,
			"patrimonio_total": patrimonio_total,
		}

	def get_goals_intelligence(self) -> list[GoalDTO]:
		"""Return active goals with refreshed completion and monthly contribution."""

		goals = self._wealth_repository.fetch_active_goals()
		updated_goals: list[GoalDTO] = []
		for goal in goals:
			valor_restante = max(goal.valor_alvo - goal.valor_atual, Decimal("0"))
			if goal.valor_alvo == 0:
				percentual_conclusao = Decimal("0")
			else:
				percentual_conclusao = min((goal.valor_atual / goal.valor_alvo) * Decimal("100"), Decimal("100"))

			if goal.prazo_meses <= 0 or valor_restante == 0:
				aporte_mensal_sugerido = Decimal("0")
			else:
				aporte_mensal_sugerido = valor_restante / Decimal(goal.prazo_meses)

			refreshed_goal = GoalDTO.model_validate(
				{
					"id_meta": goal.id_meta,
					"nome": goal.nome,
					"valor_alvo": goal.valor_alvo,
					"valor_atual": goal.valor_atual,
					"prazo_meses": goal.prazo_meses,
					"aporte_mensal_sugerido": aporte_mensal_sugerido,
					"percentual_conclusao": percentual_conclusao,
					"prioridade": goal.prioridade,
					"status": "CONCLUIDA" if percentual_conclusao >= Decimal("100") else goal.status,
				},
			)
			self._wealth_repository.upsert_goal(refreshed_goal)
			updated_goals.append(refreshed_goal)

		return updated_goals

	def get_budgets_intelligence(self, reference_date: date | None = None) -> list[BudgetDTO]:
		"""Return monthly budget usage by crossing configured limits with expenses."""

		reference = reference_date or date.today()
		expenses_by_category = self._fetch_month_expenses_by_category(reference)
		configured_budgets = self._wealth_repository.fetch_budgets()

		results: list[BudgetDTO] = []
		for budget in configured_budgets:
			used = expenses_by_category.get(budget.categoria.upper(), Decimal("0"))
			if budget.teto_mensal <= 0:
				usage_percent = Decimal("0")
			else:
				usage_percent = (used / budget.teto_mensal) * Decimal("100")

			status = self._classify_budget_status(usage_percent)
			results.append(
				BudgetDTO.model_validate(
					{
						"categoria": budget.categoria,
						"teto_mensal": budget.teto_mensal,
						"valor_utilizado": used,
						"percentual_uso": usage_percent,
						"status_alerta": status,
					},
				),
			)

		return results

	def _fetch_cash_balance(self) -> Decimal:
		"""Return the current cash balance from BASE_GERAL transactions."""

		self._transactions_repository.init_tables()
		row = self._transactions_repository._connection.execute(  # noqa: SLF001
			"""
			SELECT
				COALESCE(SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END), 0)
				- COALESCE(SUM(CASE WHEN Tipo IN ('GASTO', 'INVESTIMENTO') THEN ABS(Valor) ELSE 0 END), 0)
			FROM BASE_GERAL
			""",
		).fetchone()
		return self._to_decimal(row[0] if row else 0)

	def _fetch_month_expenses_by_category(self, reference_date: date) -> dict[str, Decimal]:
		"""Aggregate current-month expenses per category from transactions."""

		month_start = reference_date.replace(day=1)
		if reference_date.month == 12:
			next_month_start = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
		else:
			next_month_start = reference_date.replace(month=reference_date.month + 1, day=1)

		rows = self._transactions_repository._connection.execute(  # noqa: SLF001
			"""
			SELECT UPPER(Categoria) AS categoria, COALESCE(SUM(ABS(Valor)), 0) AS valor_utilizado
			FROM BASE_GERAL
			WHERE Tipo = 'GASTO'
			  AND Data >= ?
			  AND Data < ?
			GROUP BY 1
			""",
			[month_start, next_month_start],
		).fetchall()

		return {str(row[0]).upper(): self._to_decimal(row[1]) for row in rows}

	@staticmethod
	def _classify_budget_status(usage_percent: Decimal) -> str:
		"""Classify budget consumption into operational alert buckets."""

		if usage_percent >= Decimal("100"):
			return "CRITICO"
		if usage_percent >= Decimal("85"):
			return "ALERTA"
		return "OK"

	@staticmethod
	def _is_brazilian_ticker(ticker: str) -> bool:
		"""Heuristic to route tickers to BRAPI when they look Brazilian."""

		upper_ticker = str(ticker).strip().upper()
		if upper_ticker.endswith(".SA"):
			return True
		if len(upper_ticker) < 5:
			return False
		prefix = upper_ticker[:4]
		suffix = upper_ticker[-1]
		return prefix.isalpha() and suffix.isdigit()

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert mixed numeric values to ``Decimal`` consistently."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		return Decimal("0")