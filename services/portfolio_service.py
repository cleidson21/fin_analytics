"""Portfolio intelligence service for pricing, allocation, and dividend yield."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import yfinance as yf

from config.constants import ClasseAtivo
from repositories.wealth_repository import WealthRepository


class PortfolioService:
	"""Compute portfolio analytics using market quotes and repository holdings."""

	def __init__(self, repository: WealthRepository) -> None:
		self._repository = repository
		self._price_cache: dict[str, Decimal] = {}

	def sync_market_prices(self) -> dict[str, Decimal]:
		"""Fetch current market prices for all tickers stored in the portfolio.

		The method prefers a batch market download for performance and falls back
		to per-ticker lookups only when the batch response does not provide a
		usable quote.
		"""

		portfolio = self._repository.fetch_portfolio()
		tickers = [str(asset.get("ticker", "")).strip().upper() for asset in portfolio if asset.get("ticker")]
		if not tickers:
			self._price_cache = {}
			return {}

		prices = self._fetch_batch_prices(tickers)
		missing_tickers = [ticker for ticker in tickers if ticker not in prices]
		if missing_tickers:
			prices.update(self._fetch_fallback_prices(missing_tickers))

		self._price_cache = prices
		return prices

	def get_portfolio_summary(self) -> dict[str, Any]:
		"""Return total portfolio value, P/L, and allocation by asset class."""

		portfolio = self._repository.fetch_portfolio()
		prices = self._price_cache or self.sync_market_prices()

		asset_rows: list[dict[str, Any]] = []
		total_market_value = Decimal("0")
		total_cost_basis = Decimal("0")
		allocation_by_class: dict[ClasseAtivo, Decimal] = {}

		for asset in portfolio:
			ticker = str(asset.get("ticker", "")).strip().upper()
			classe = self._coerce_class(asset.get("classe"))
			quantidade = self._to_decimal(asset.get("quantidade"))
			preco_medio = self._to_decimal(asset.get("preco_medio"))
			preco_atual = prices.get(ticker, preco_medio)
			market_value = quantidade * preco_atual
			cost_basis = quantidade * preco_medio
			profit_loss = market_value - cost_basis

			total_market_value += market_value
			total_cost_basis += cost_basis
			allocation_by_class[classe] = allocation_by_class.get(classe, Decimal("0")) + market_value

			asset_rows.append(
				{
					"ticker": ticker,
					"classe": classe.value,
					"quantidade": quantidade,
					"preco_medio": preco_medio,
					"preco_atual": preco_atual,
					"valor_mercado": market_value,
					"lucro_prejuizo": profit_loss,
				},
			)

		return {
			"patrimonio_total": total_market_value,
			"lucro_prejuizo_total": total_market_value - total_cost_basis,
			"distribuicao_por_classe": self._build_allocation(allocation_by_class, total_market_value),
			"ativos": asset_rows,
		}

	def get_dividend_yield(self) -> dict[str, Any]:
		"""Calculate trailing monthly and annual dividend yields."""

		summary = self.get_portfolio_summary()
		patrimonio_total = self._to_decimal(summary.get("patrimonio_total"))
		if patrimonio_total <= 0:
			return {
				"yield_mensal": Decimal("0"),
				"yield_anual": Decimal("0"),
				"dividendos_30_dias": Decimal("0"),
				"dividendos_365_dias": Decimal("0"),
				"base_calculo": patrimonio_total,
			}

		today = date.today()
		dividendos_30 = self._sum_dividends(today - timedelta(days=30), today)
		dividendos_365 = self._sum_dividends(today - timedelta(days=365), today)

		return {
			"yield_mensal": (dividendos_30 / patrimonio_total) * Decimal("100"),
			"yield_anual": (dividendos_365 / patrimonio_total) * Decimal("100"),
			"dividendos_30_dias": dividendos_30,
			"dividendos_365_dias": dividendos_365,
			"base_calculo": patrimonio_total,
		}

	def _fetch_batch_prices(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fetch prices in a single market request when possible."""

		try:
			market_data = yf.download(
				tickers=" ".join(tickers),
				period="5d",
				interval="1d",
				auto_adjust=False,
				progress=False,
				threads=True,
				group_by="ticker",
			)
		except Exception:
			return {}

		prices: dict[str, Decimal] = {}
		if getattr(market_data, "empty", True):
			return prices

		columns = getattr(market_data, "columns", None)
		has_multiindex = bool(getattr(columns, "nlevels", 1) > 1)

		for ticker in tickers:
			price = self._extract_close_price(market_data, ticker, has_multiindex)
			if price is not None:
				prices[ticker] = price

		return prices

	def _fetch_fallback_prices(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fetch missing tickers individually when the batch response is incomplete."""

		prices: dict[str, Decimal] = {}
		for ticker in tickers:
			try:
				info = yf.Ticker(ticker).fast_info
				raw_price = info.get("lastPrice") if isinstance(info, Mapping) else None
				if raw_price is None:
					raw_price = info.get("regularMarketPreviousClose") if isinstance(info, Mapping) else None
				if raw_price is not None:
					prices[ticker] = self._to_decimal(raw_price)
			except Exception:
				continue

		return prices

	def _extract_close_price(self, market_data: Any, ticker: str, has_multiindex: bool) -> Decimal | None:
		"""Extract the most recent close price from a yfinance response."""

		try:
			if has_multiindex:
				ticker_frame = market_data[ticker]
				close_series = ticker_frame["Close"].dropna()
			else:
				if ticker in getattr(market_data, "columns", []):
					close_series = market_data[ticker].dropna()
				elif "Close" in getattr(market_data, "columns", []):
					close_series = market_data["Close"].dropna()
				else:
					return None

			if close_series.empty:
				return None

			return self._to_decimal(close_series.iloc[-1])
		except Exception:
			return None

	def _build_allocation(
		self,
		allocation_by_class: dict[ClasseAtivo, Decimal],
		total_market_value: Decimal,
	) -> list[dict[str, Any]]:
		"""Convert class allocations into percentage-based summary rows."""

		rows: list[dict[str, Any]] = []
		for classe, total in sorted(allocation_by_class.items(), key=lambda item: item[0].value):
			percentual = (total / total_market_value) * Decimal("100") if total_market_value > 0 else Decimal("0")
			rows.append(
				{
					"classe": classe.value,
					"valor": total,
					"percentual": percentual,
				}
			)

		return rows

	def _sum_dividends(self, start_date: date, end_date: date) -> Decimal:
		"""Aggregate dividends in the requested interval directly from DuckDB."""

		self._repository.init_wealth_tables()
		row = self._repository._connection.execute(  # noqa: SLF001
			"""
			SELECT COALESCE(SUM(valor_recebido), 0)
			FROM FACT_DIVIDENDS
			WHERE data_pagamento BETWEEN ? AND ?
			""",
			[start_date, end_date],
		).fetchone()
		return self._to_decimal(row[0] if row else 0)

	@staticmethod
	def _coerce_class(value: object) -> ClasseAtivo:
		"""Normalize stored class values to ``ClasseAtivo``."""

		if isinstance(value, ClasseAtivo):
			return value
		return ClasseAtivo(str(value))

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert numeric values to ``Decimal`` without float drift."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		return Decimal("0")