"""Market data integration for real-time wealth analytics.

The service batches quote requests whenever possible and keeps a lightweight
in-memory cache so it can fall back to the last known price when a provider is
temporarily unavailable.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

import requests
import yfinance as yf


class MarketDataService:
	"""Fetch real-time market quotes from global and Brazilian providers."""

	_BRAPI_URL = "https://brapi.dev/api/quote/{tickers}"

	def __init__(
		self,
		*,
		timeout_seconds: float = 6.0,
		session: requests.Session | None = None,
		brapi_token: str | None = None,
	) -> None:
		self._timeout_seconds = timeout_seconds
		self._session = session or requests.Session()
		self._owns_session = session is None
		self._brapi_token = brapi_token or os.getenv("BRAPI_TOKEN") or os.getenv("BRAPI_API_KEY")
		self._last_known_quotes: dict[str, Decimal] = {}

	def close(self) -> None:
		"""Release the underlying HTTP session if the service created it."""

		if self._owns_session:
			self._session.close()

	def fetch_global_quotes(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fetch international, crypto, and ETF quotes using ``yfinance``.

		The method uses a batch request first and then falls back to per-ticker
		lookup only for the missing symbols. When the provider fails entirely,
		the last known cached prices are returned.
		"""

		normalized_tickers = self._normalize_tickers(tickers)
		if not normalized_tickers:
			return {}

		quotes = self._fetch_yfinance_batch(normalized_tickers)
		missing_tickers = [ticker for ticker in normalized_tickers if ticker not in quotes]
		if missing_tickers:
			quotes.update(self._fetch_yfinance_fallback(missing_tickers))

		return self._complete_with_cache(quotes, normalized_tickers)

	def fetch_br_quotes(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fetch Brazilian equities and FIIs using the public BRAPI endpoint.

		The method batches symbols into chunks so it stays efficient for larger
		portfolios. If the API request fails or partially omits a symbol, the
		service falls back to the last known quote cache.
		"""

		normalized_tickers = self._normalize_tickers(tickers)
		if not normalized_tickers:
			return {}

		quotes: dict[str, Decimal] = {}
		for chunk in self._chunked(normalized_tickers, 100):
			try:
				response = self._session.get(
					self._BRAPI_URL.format(tickers=",".join(chunk)),
					params=self._build_brapi_params(),
					timeout=self._timeout_seconds,
				)
				response.raise_for_status()
				payload = response.json()
				for ticker, price in self._parse_brapi_quotes(payload).items():
					quotes[ticker] = price
			except Exception:
				continue

		return self._complete_with_cache(quotes, normalized_tickers)

	def _fetch_yfinance_batch(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fetch a batch of quotes from ``yfinance`` in one network round-trip."""

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
			market_data = None

		quotes: dict[str, Decimal] = {}
		if market_data is not None and not getattr(market_data, "empty", True):
			columns = getattr(market_data, "columns", None)
			has_multiindex = bool(getattr(columns, "nlevels", 1) > 1)
			for ticker in tickers:
				price = self._extract_yfinance_price(market_data, ticker, has_multiindex)
				if price is not None:
					quotes[ticker] = price

		return quotes

	def _fetch_yfinance_fallback(self, tickers: list[str]) -> dict[str, Decimal]:
		"""Fallback to per-ticker lookup when the batch response is incomplete."""

		quotes: dict[str, Decimal] = {}
		for ticker in tickers:
			try:
				info = yf.Ticker(ticker).fast_info
				raw_price = None
				if isinstance(info, Mapping):
					raw_price = info.get("lastPrice") or info.get("regularMarketPreviousClose")
				if raw_price is None:
					history = yf.Ticker(ticker).history(period="5d", interval="1d")
					if not history.empty and "Close" in history:
						raw_price = history["Close"].dropna().iloc[-1]
				if raw_price is not None:
					quotes[ticker] = self._to_decimal(raw_price)
			except Exception:
				continue

		return quotes

	def _extract_yfinance_price(self, market_data: Any, ticker: str, has_multiindex: bool) -> Decimal | None:
		"""Extract the latest close price from a ``yfinance`` payload."""

		try:
			if has_multiindex:
				ticker_frame = market_data[ticker]
				close_series = ticker_frame["Close"].dropna()
			else:
				columns = getattr(market_data, "columns", [])
				if ticker in columns:
					close_series = market_data[ticker].dropna()
				elif "Close" in columns:
					close_series = market_data["Close"].dropna()
				else:
					return None

			if close_series.empty:
				return None

			return self._to_decimal(close_series.iloc[-1])
		except Exception:
			return None

	def _parse_brapi_quotes(self, payload: Mapping[str, Any]) -> dict[str, Decimal]:
		"""Convert BRAPI responses into a ticker-to-price mapping."""

		result: dict[str, Decimal] = {}
		entries = payload.get("results") or payload.get("result") or []
		if isinstance(entries, Mapping):
			entries = list(entries.values())

		for entry in entries:
			if not isinstance(entry, Mapping):
				continue
			ticker = str(entry.get("stock") or entry.get("symbol") or entry.get("code") or "").strip().upper()
			if not ticker:
				continue
			raw_price = (
				entry.get("regularMarketPrice")
				or entry.get("lastPrice")
				or entry.get("close")
				or entry.get("regularMarketPreviousClose")
			)
			if raw_price is None:
				continue
			result[ticker] = self._to_decimal(raw_price)

		return result

	def _complete_with_cache(self, quotes: dict[str, Decimal], requested_tickers: list[str]) -> dict[str, Decimal]:
		"""Backfill missing symbols using the last known cached quotes."""

		for ticker in requested_tickers:
			if ticker not in quotes and ticker in self._last_known_quotes:
				quotes[ticker] = self._last_known_quotes[ticker]

		self._last_known_quotes.update(quotes)
		return quotes

	def _build_brapi_params(self) -> dict[str, str]:
		"""Build the query parameters for BRAPI requests."""

		params: dict[str, str] = {}
		if self._brapi_token:
			params["token"] = self._brapi_token
		return params

	@staticmethod
	def _normalize_tickers(tickers: Iterable[str]) -> list[str]:
		"""Normalize, deduplicate, and preserve ticker order."""

		seen: set[str] = set()
		normalized: list[str] = []
		for ticker in tickers:
			candidate = str(ticker).strip().upper()
			if not candidate or candidate in seen:
				continue
			seen.add(candidate)
			normalized.append(candidate)
		return normalized

	@staticmethod
	def _chunked(items: list[str], chunk_size: int) -> Iterable[list[str]]:
		"""Yield consecutive chunks from a list."""

		for index in range(0, len(items), chunk_size):
			yield items[index:index + chunk_size]

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert numeric provider output into a precise ``Decimal``."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		return Decimal(str(value))