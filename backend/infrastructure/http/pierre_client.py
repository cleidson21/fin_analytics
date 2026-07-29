"""
PierreClient — HTTP client para comunicação com a API REST do Pierre Finance.

Responsabilidades (Infrastructure / HTTP):
  - Autenticação via API key (Bearer token)
  - Suporte a retry exponencial com jitter
  - Timeout configurável via Settings
  - Paginação implícita (data-range chunking)
  - Logging estruturado
  - Nunca expõe dict cru para a camada de Application
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import settings
from backend.application.ports.pierre_provider import IPierreProvider
from backend.application.dtos.provider_dtos import ProviderTransactionDTO, ProviderAccountDTO
from backend.infrastructure.http.pierre_dtos import (
    PierreAccountDTO,
    PierreTransactionDTO,
    PierreTransactionsResponseDTO,
    PierreAccountsResponseDTO,
)

logger = logging.getLogger("pierre.client")

_PIERRE_BASE_URL = "https://www.pierre.finance"
_DEFAULT_TIMEOUT_SECONDS = 30
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0   # seconds (exponential: 2, 4, 8 …)
_CHUNK_DAYS = 90      # max days per request (large enough, API has no explicit pagination)


def _exponential_backoff(attempt: int) -> float:
    """Returns wait time in seconds with jitter for attempt N (0-indexed)."""
    import random
    base = _BACKOFF_BASE ** attempt
    jitter = random.uniform(0, base * 0.3)
    return base + jitter


class PierreClientError(Exception):
    """Raised when Pierre API returns an unexpected response."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class PierreAuthError(PierreClientError):
    """Raised when the API key is invalid or the subscription is expired."""
    pass


class PierreClient(IPierreProvider):
    """Async HTTP client for the Pierre Finance REST API.

    Usage (within a context manager):
        async with PierreClient() as client:
            transactions = await client.get_transactions(start_date, end_date)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = _PIERRE_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or settings.PIERRE_API_KEY
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------ #
    #  Context-manager support
    # ------------------------------------------------------------------ #

    async def __aenter__(self) -> "PierreClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._default_headers(),
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *_args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    async def get_accounts(self) -> List[ProviderAccountDTO]:
        """Returns all accounts from Pierre."""
        raw = await self._request("GET", "/tools/api/get-accounts")
        response = PierreAccountsResponseDTO.model_validate(raw)
        return [
            ProviderAccountDTO(
                id=acc.id,
                name=acc.name,
                type=acc.type or "BANK",
                currency_code=acc.currency_code or "BRL",
                status="ACTIVE",
            )
            for acc in response.data
        ]

    async def get_transactions(
        self,
        start_date: date,
        end_date: date,
        account_type: Optional[str] = None,
    ) -> List[ProviderTransactionDTO]:
        """Returns all transactions between start_date and end_date.

        Chunks the range by _CHUNK_DAYS to avoid server-side limits.
        """
        all_transactions: List[ProviderTransactionDTO] = []
        current_start = start_date

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=_CHUNK_DAYS - 1), end_date)
            params: Dict[str, Any] = {
                "startDate": current_start.isoformat(),
                "endDate": current_end.isoformat(),
                "format": "raw",
            }
            if account_type:
                params["accountType"] = account_type

            t0 = time.monotonic()
            raw = await self._request("GET", "/tools/api/get-transactions", params=params)
            elapsed = time.monotonic() - t0

            response = PierreTransactionsResponseDTO.model_validate(raw)
            chunk_count = len(response.data)

            logger.info(
                "pierre.get_transactions chunk_fetched",
                extra={
                    "start": current_start.isoformat(),
                    "end": current_end.isoformat(),
                    "count": chunk_count,
                    "elapsed_ms": round(elapsed * 1000),
                },
            )

            for dto in response.data:
                provider_dto = ProviderTransactionDTO(
                    id=dto.id,
                    account_id=dto.account_id,
                    amount=float(dto.amount),
                    direction=dto.direction,
                    description=dto.description,
                    transaction_date=dto.transaction_date,
                    type=dto.type,
                    status=dto.status,
                    original_description=dto.original_description,
                    category=dto.category,
                    posted_date=dto.posted_date,
                    is_recurring=dto.is_recurring,
                    currency_code=dto.currency_code,
                )
                
                # Monkey-patching effective methods because ProviderTransactionDTO is simple dataclass
                provider_dto.effective_installment_count = dto.effective_installment_count
                provider_dto.effective_installment_current = dto.effective_installment_current
                provider_dto.effective_purchase_id = dto.effective_purchase_id

                all_transactions.append(provider_dto)
                
            current_start = current_end + timedelta(days=1)

        logger.info(
            "pierre.get_transactions complete",
            extra={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "total": len(all_transactions),
            },
        )
        return all_transactions

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _default_headers(self) -> Dict[str, str]:
        if not self._api_key:
            raise PierreAuthError("PIERRE_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes an HTTP request with retry logic.

        Returns:
            Parsed JSON dict (guaranteed to be a dict — never None).

        Raises:
            PierreAuthError: on 401/403
            PierreClientError: on other HTTP or parsing errors
        """
        if not self._client:
            raise RuntimeError(
                "PierreClient must be used as an async context manager"
            )

        last_error: Optional[Exception] = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.request(
                    method, path, params=params, json=json
                )

                logger.debug(
                    "pierre.http_response",
                    extra={
                        "method": method,
                        "path": path,
                        "status": response.status_code,
                        "attempt": attempt + 1,
                    },
                )

                if response.status_code in (401, 403):
                    raise PierreAuthError(
                        f"Pierre authentication failed ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                    )

                if response.status_code == 429:
                    # Rate limit: always retry
                    wait = _exponential_backoff(attempt)
                    logger.warning(
                        "pierre.rate_limited — backing off",
                        extra={"wait_seconds": wait, "attempt": attempt + 1},
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code >= 500:
                    raise PierreClientError(
                        f"Pierre server error ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                    )

                response.raise_for_status()
                return response.json()

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _exponential_backoff(attempt)
                    logger.warning(
                        "pierre.network_error — retrying",
                        extra={
                            "error": str(exc),
                            "wait_seconds": wait,
                            "attempt": attempt + 1,
                        },
                    )
                    await asyncio.sleep(wait)
            except PierreAuthError:
                raise
            except PierreClientError:
                raise

        raise PierreClientError(
            f"Pierre request failed after {_MAX_RETRIES} attempts: {last_error}"
        )
