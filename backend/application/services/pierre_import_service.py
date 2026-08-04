"""
PierreImportService — Orquestra a importação de transações do Pierre.

Camada: Application / Services

Responsabilidades:
  - Consumir IPierreProvider
  - Converter ProviderTransactionDTO → Transaction (Domain Entity)
  - Normalizar descrições, datas e valores
  - Gerar hash determinístico para idempotência
  - Executar importação em lotes via ITransactionRepository.bulk_upsert
  - Retornar SyncResultDTO para a camada API

Regras arquiteturais:
  - Zero lógica HTTP aqui (tudo delegado ao IPierreProvider)
  - Zero lógica SQL aqui (tudo delegado ao Repository)
  - Esta classe nunca é instanciada diretamente pelo Router
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Any
from uuid import UUID, uuid5, NAMESPACE_URL

from backend.domain.entities.transaction import Transaction
from backend.domain.entities.account import Account
from backend.domain.enums.provider_type import ProviderType
from backend.domain.enums.transaction_type import TransactionType
from backend.domain.enums.transaction_status import TransactionStatus
from backend.domain.enums.movement_type import MovementType

from backend.application.ports.pierre_provider import IPierreProvider
from backend.application.ports.transaction_repository import ITransactionRepository
from backend.application.ports.account_repository import IAccountRepository
from backend.application.dtos.provider_dtos import ProviderTransactionDTO
from backend.application.dtos.sync_result_dto import SyncResultDTO

logger = logging.getLogger("pierre.import_service")

# ------------------------------------------------------------------ #
#  Constantes de normalização
# ------------------------------------------------------------------ #
_PROVIDER = ProviderType.PIERRE
_DEFAULT_CURRENCY = "BRL"
_BATCH_SIZE = 100  # transações por lote de upsert
_DEFAULT_LOOKBACK_DAYS = 90  # janela padrão se não especificado datas


class PierreImportService:
    """Serviço de Application responsável pela importação Pierre → DB."""

    def __init__(
        self,
        pierre_provider: IPierreProvider,
        transaction_repo: ITransactionRepository,
        account_repo: IAccountRepository,
        category_repo: ICategoryRepository,
        sync_log_repo: ISyncLogRepository,
    ) -> None:
        self._provider = pierre_provider
        self._tx_repo = transaction_repo
        self._account_repo = account_repo
        self._category_repo = category_repo
        self._sync_log_repo = sync_log_repo

    # ================================================================= #
    #  Public API
    # ================================================================= #

    async def import_transactions(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> SyncResultDTO:
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=_DEFAULT_LOOKBACK_DAYS))

        t0 = time.monotonic()
        
        # Create SyncLog initially
        from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
        from backend.domain.entities.category import Category
        
        sync_log = SyncLogModel(
            user_id=str(user_id),
            provider=_PROVIDER,
            status=SyncStatus.RUNNING
        )
        sync_log = await self._sync_log_repo.create(sync_log)

        logger.info(
            "pierre.import.start",
            extra={"start": start_date.isoformat(), "end": end_date.isoformat(), "sync_id": sync_log.id},
        )

        imported = skipped = errors = accounts_synced = categories_synced = 0
        error_message = None

        # try:
        async with self._provider as provider:
            # 1. Sync accounts to avoid FK constraint errors
            raw_accounts = await provider.get_accounts()
            for acc_dto in raw_accounts:
                account_uuid = self._deterministic_uuid(f"pierre_account_{acc_dto.id}")
                # Upsert Account
                from backend.domain.enums.account_type import AccountType
                acc_type_str = acc_dto.type.upper() if acc_dto.type else "BANK"
                try:
                    acc_type = AccountType(acc_type_str)
                except ValueError:
                    acc_type = AccountType.BANK

                from backend.domain.enums.currency_code import CurrencyCode
                currency_str = acc_dto.currency_code.upper() if acc_dto.currency_code else "BRL"
                try:
                    currency = CurrencyCode(currency_str)
                except ValueError:
                    currency = CurrencyCode.BRL

                acc_entity = Account(
                    id=account_uuid,
                    user_id=user_id,
                    external_id=acc_dto.id,
                    provider=_PROVIDER,
                    institution_id=None,
                    name=acc_dto.name,
                    type=acc_type,
                    subtype=None,
                    currency_code=currency,
                    balance=acc_dto.balance if hasattr(acc_dto, "balance") and acc_dto.balance else Decimal("0"),
                    balance_updated_at=datetime.now(timezone.utc),
                    is_active=True,
                    provider_code=None,
                    provider_metadata=None,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                await self._account_repo.upsert(acc_entity)
                accounts_synced += 1

            # 2. Sync transactions
            raw_transactions = await provider.get_transactions(start_date, end_date)
            
        # 3. Extract unique categories and upsert them
        unique_categories = set(t.category for t in raw_transactions if t.category)
        category_map: dict[str, UUID] = {}
        for cat_name in unique_categories:
            cat_slug = cat_name.lower().replace(" ", "-")
            cat_uuid = self._deterministic_uuid(f"category_{cat_slug}")
            cat_entity = Category(
                id=cat_uuid,
                name=cat_name,
                slug=cat_slug,
                is_system=False,
            )
            await self._category_repo.save(cat_entity)
            category_map[cat_name] = cat_uuid
            categories_synced += 1

        logger.info(
            "pierre.import.fetched",
            extra={"count": len(raw_transactions)},
        )

        # Process in batches
        for batch_start in range(0, len(raw_transactions), _BATCH_SIZE):
            batch = raw_transactions[batch_start : batch_start + _BATCH_SIZE]
            b_imported, b_skipped, b_errors = await self._process_batch(batch, user_id, category_map)
            imported += b_imported
            skipped += b_skipped
            errors += b_errors

        # except Exception as exc:
        #     logger.error("pierre.import.failed", extra={"error": str(exc)})
        #     error_message = str(exc)

        duration = round(time.monotonic() - t0, 2)
        if error_message:
            status = SyncStatus.FAILED
        else:
            status = SyncStatus.SUCCESS if errors == 0 else SyncStatus.PARTIAL

        # Update SyncLog
        sync_log.end_time = datetime.utcnow()
        sync_log.duration_seconds = duration
        sync_log.status = status
        sync_log.accounts_synced = accounts_synced
        sync_log.transactions_synced = len(raw_transactions) if not error_message else 0
        sync_log.categories_synced = categories_synced
        sync_log.inserted = imported
        sync_log.updated = 0  # In our implementation inserted holds the upserted total
        sync_log.ignored = skipped
        sync_log.error_message = error_message
        await self._sync_log_repo.create(sync_log)  # will just update due to session logic

        logger.info(
            "pierre.import.complete",
            extra={
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
                "accounts_synced": accounts_synced,
                "duration_seconds": duration,
                "status": status.value,
            },
        )

        return SyncResultDTO(
            status=status.value.lower(),
            imported=imported,
            skipped=skipped,
            errors=errors,
            accounts_synced=accounts_synced,
            date_range_start=start_date,
            date_range_end=end_date,
            duration_seconds=duration,
            error_message=error_message,
        )

    # ================================================================= #
    #  Private helpers
    # ================================================================= #

    async def _process_batch(
        self, batch: List[ProviderTransactionDTO], user_id: UUID, category_map: dict[str, UUID]
    ) -> Tuple[int, int, int]:
        entities: List[Transaction] = []
        errors = 0

        for dto in batch:
            try:
                entity = self._to_entity(dto, user_id, category_map)
                entities.append(entity)
            except Exception as exc:
                errors += 1
                logger.warning(
                    "pierre.import.conversion_error",
                    extra={"pierre_id": dto.id, "error": str(exc)},
                )

        if not entities:
            return 0, 0, errors

        result = await self._tx_repo.bulk_upsert(entities)
        return result["inserted"], result["skipped"], errors

    def _to_entity(self, dto: ProviderTransactionDTO, user_id: UUID, category_map: dict[str, UUID]) -> Transaction:
        description = self._normalize_description(dto.description)
        transaction_date = self._ensure_date(dto.transaction_date)
        amount = self._normalize_amount(dto.amount)

        inst_count = dto.effective_installment_count()
        inst_current = dto.effective_installment_current()
        raw_purchase_id = dto.effective_purchase_id()

        if inst_count and inst_current and inst_current > inst_count:
            inst_current = inst_count

        purchase_uuid: Optional[UUID] = None
        if raw_purchase_id:
            purchase_uuid = self._deterministic_uuid(raw_purchase_id)
        elif inst_count and inst_count > 1:
            key = f"{description}|{amount}|{inst_count}"
            purchase_uuid = self._deterministic_uuid(key)

        account_uuid = self._deterministic_uuid(f"pierre_account_{dto.account_id}")
        
        category_id = None
        if dto.category and dto.category in category_map:
            category_id = category_map[dto.category]

        return Transaction(
            id=self._deterministic_uuid(f"pierre_tx_{dto.id}"),
            user_id=user_id,
            provider=_PROVIDER,
            external_id=dto.id,
            account_id=account_uuid,
            amount=amount,
            direction=self._normalize_direction(dto.direction),
            currency_code=dto.currency_code or _DEFAULT_CURRENCY,
            description=description,
            original_description=dto.original_description or dto.description,
            category_id=category_id,
            type=self._normalize_type(dto.type, dto.direction),
            status=self._normalize_status(dto.status),
            transaction_date=transaction_date,
            posted_date=self._ensure_date(dto.posted_date),
            is_recurring=dto.is_recurring or False,
            installment_count=inst_count,
            installment_current=inst_current,
            purchase_id=purchase_uuid,
            provider_metadata={"pierre_category": dto.category} if dto.category else None,
            hash=self._compute_hash(dto.id, _PROVIDER.value, transaction_date, amount),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------ #
    #  Normalização de campos
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalize_description(raw: str) -> str:
        if not raw or not raw.strip():
            return "Sem descrição"
        text = unicodedata.normalize("NFC", raw)
        text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return "Sem descrição"
        return text[:512]

    @staticmethod
    def _normalize_amount(v: Any) -> Decimal:
        try:
            return Decimal(str(v)).copy_abs()
        except Exception:
            return Decimal("0")

    @staticmethod
    def _normalize_direction(direction: str) -> MovementType:
        if not direction:
            return MovementType.DEBIT
        upper = direction.upper()
        if upper in ("CREDIT", "IN", "INCOME", "ENTRADA"):
            return MovementType.CREDIT
        return MovementType.DEBIT

    @staticmethod
    def _normalize_type(raw_type: Optional[str], direction: str) -> TransactionType:
        if not raw_type:
            return TransactionType.PURCHASE if direction == "DEBIT" else TransactionType.OTHER
        mapping = {
            "purchase": TransactionType.PURCHASE,
            "compra": TransactionType.PURCHASE,
            "transfer": TransactionType.TRANSFER,
            "transferência": TransactionType.TRANSFER,
            "transferencia": TransactionType.TRANSFER,
            "payment": TransactionType.PAYMENT,
            "pagamento": TransactionType.PAYMENT,
            "pix": TransactionType.PIX,
            "ted": TransactionType.TED,
            "doc": TransactionType.DOC,
            "refund": TransactionType.REFUND,
            "estorno": TransactionType.REFUND,
        }
        return mapping.get(raw_type.lower(), TransactionType.OTHER)

    @staticmethod
    def _normalize_status(status: Optional[str]) -> TransactionStatus:
        if not status:
            return TransactionStatus.POSTED
        if status.upper() in ("PENDING", "PENDENTE"):
            return TransactionStatus.PENDING
        return TransactionStatus.POSTED

    @staticmethod
    def _ensure_date(v: Any) -> date:
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        return date.today()

    @staticmethod
    def _deterministic_uuid(seed: str) -> UUID:
        return uuid5(NAMESPACE_URL, seed)

    @staticmethod
    def _compute_hash(external_id: str, provider: str, tx_date: date, amount: Decimal) -> str:
        """Gera hash SHA-256 determinístico para idempotência."""
        raw = f"{external_id}|{provider}|{tx_date.isoformat()}|{amount}"
        return hashlib.sha256(raw.encode()).hexdigest()

