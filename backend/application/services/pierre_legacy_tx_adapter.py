"""
PierreLegacyTransactionAdapter
================================
Adapter que implementa `ITransactionRepository` (interface canônica usada pelo
`PierreImportService`) mas persiste utilizando o repositório legado do domínio
Pierre (`domains/pierre/repository.py`).

Por que este adapter existe
---------------------------
O `PierreImportService` produz entidades do tipo `domain.entities.transaction.Transaction`
(dataclass canônica) e precisa de um repositório com `.bulk_upsert()`.

A Governança (`governance_router.py`) lê da tabela `transactions` através do
`domains/pierre/repository.py :: TransactionRepository`, que usa o ORM legado
(`domains/pierre/models.py :: Transaction`) com PK composta `(provider, external_id)`.

Sem este adapter, o `PierreImportService` grava via `SQLAlchemyTransactionRepository`
(canônico), que usa `TransactionModel` com schema incompatível com o legado, tornando
as transações importadas invisíveis para a Governança.

Este adapter resolve a divergência sem:
  - Migrar dados;
  - Alterar o schema legado;
  - Alterar contratos da API;
  - Alterar o PierreImportService.

Regras de preservação de governança herdadas do legado
------------------------------------------------------
O `TransactionRepository.upsert()` legado já implementa:
  - Transação nova  → INSERT com governance_status = PENDING
  - Transação existente → UPDATE apenas ALLOWED_RAW_FIELDS (governança intocável)

Este adapter herda essas regras.
"""

from __future__ import annotations

import logging
from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from backend.application.ports.transaction_repository import ITransactionRepository
from backend.domain.entities.transaction import Transaction

logger = logging.getLogger("pierre.legacy_tx_adapter")

# Campos RAW permitidos no upsert — deve estar alinhado com ALLOWED_RAW_FIELDS
# do repositório legado (domains/pierre/repository.py)
_ALLOWED_RAW_FIELDS = frozenset({
    'account_provider', 'account_external_id',
    'description', 'original_description',
    'category', 'original_category',
    'amount', 'currency', 'date', 'status', 'type',
    'merchant_name', 'bill_id',
    'installment_number', 'total_installments',
    'purchase_date', 'receiver_name', 'payer_name',
    'manual_transaction', 'extra_json',
})


def _entity_to_legacy_dict(tx: Transaction) -> dict:
    """Converte a entidade canônica para o dict esperado pelo repositório legado.

    Mapeamento crítico de campos:
      - tx.transaction_date (date)  → 'date' (datetime, meia-noite)
      - tx.currency_code            → 'currency'
      - tx.direction.value          → não gravado diretamente (legado não tem)
      - tx.status.value             → 'status'
      - tx.type.value               → 'type'
      - tx.account_id               → 'account_external_id' via provider_metadata
    """
    # Recuperar account_external_id da metadata (gravada pelo PierreImportService)
    metadata = tx.provider_metadata or {}
    account_ext_id = metadata.get("account_external_id", "")

    # Converter date → datetime (meia-noite) para campo DATETIME do legado
    tx_date = tx.transaction_date
    if isinstance(tx_date, datetime):
        date_val = tx_date
    else:
        date_val = datetime.combine(tx_date, time.min)

    # Normalizar enums para string
    provider_str = tx.provider.value if hasattr(tx.provider, "value") else str(tx.provider)
    status_str = tx.status.value if hasattr(tx.status, "value") else str(tx.status)
    type_str = tx.type.value if hasattr(tx.type, "value") else str(tx.type)

    return {
        # Identity
        "provider": provider_str,
        "external_id": tx.external_id or str(tx.id),

        # Raw account reference
        "account_provider": provider_str,
        "account_external_id": account_ext_id,

        # Raw transaction data
        "description": tx.description,
        "original_description": tx.original_description,
        "category": metadata.get("pierre_category"),
        "original_category": metadata.get("pierre_category"),
        "amount": float(tx.amount),
        "currency": tx.currency_code,
        "date": date_val,            # DATA REAL da transação, não timestamp de importação
        "status": status_str,
        "type": type_str,

        # Installments
        "installment_number": tx.installment_current,
        "total_installments": tx.installment_count,

        # Defaults
        "manual_transaction": False,
    }


class PierreLegacyTransactionAdapter(ITransactionRepository):
    """Implementa ITransactionRepository gravando via repositório legado Pierre.

    Deve ser injetado no PierreImportService em substituição ao
    SQLAlchemyTransactionRepository (canônico).
    """

    def __init__(self) -> None:
        # Import lazy para evitar ciclo de importação e conflito de MetaData
        from backend.domains.pierre.repository import TransactionRepository as LegacyRepo
        from backend.domains.pierre.repository import AccountRepository as LegacyAccRepo
        from backend.database.session import SessionLocal
        self._legacy_repo = LegacyRepo()
        self._legacy_acc_repo = LegacyAccRepo()
        self._SessionLocal = SessionLocal

    # ------------------------------------------------------------------ #
    #  ITransactionRepository contract
    # ------------------------------------------------------------------ #

    async def create(self, transaction: Transaction) -> Transaction:
        """Insere uma transação via upsert legado."""
        tx_dict = _entity_to_legacy_dict(transaction)
        db = self._SessionLocal()
        try:
            self._legacy_repo.upsert(db, tx_dict)
            db.commit()
        finally:
            db.close()
        return transaction

    async def get_by_id(self, id: UUID) -> Optional[Transaction]:
        """Não implementado — a Governança usa (provider, external_id) como identidade."""
        return None

    async def get_by_hash(self, hash: str) -> Optional[Transaction]:
        """Não implementado — o legado usa (provider, external_id) como chave."""
        return None

    async def update(self, transaction: Transaction) -> Transaction:
        """Atualiza via upsert legado (preserva governança automaticamente)."""
        tx_dict = _entity_to_legacy_dict(transaction)
        db = self._SessionLocal()
        try:
            self._legacy_repo.upsert(db, tx_dict)
            db.commit()
        finally:
            db.close()
        return transaction

    async def bulk_upsert(self, transactions: List[Transaction]) -> Dict[str, int]:
        """Upsert em lote via repositório legado.

        Regras herdadas do legado:
          - Transação nova  → INSERT com governance_status = PENDING
          - Existente       → UPDATE apenas campos RAW (governança preservada)

        Idempotência: baseada em (provider, external_id) — mesmo que seja chamado
        duas vezes com os mesmos dados, não cria duplicatas.

        Returns:
            {'inserted': N, 'skipped': M}  — compatível com a interface canônica
        """
        if not transactions:
            return {"inserted": 0, "skipped": 0}

        inserted = skipped = 0
        db = self._SessionLocal()
        try:
            for tx in transactions:
                tx_dict = _entity_to_legacy_dict(tx)
                provider = tx_dict["provider"]
                external_id = tx_dict["external_id"]

                existing = self._legacy_repo.get_by_external_id(db, provider, external_id)
                if existing:
                    skipped += 1
                else:
                    inserted += 1

                # upsert preserva governança se existente
                self._legacy_repo.upsert(db, tx_dict)

            db.commit()
            logger.info(
                "pierre.legacy_adapter.bulk_upsert",
                extra={"inserted": inserted, "skipped": skipped},
            )
        except Exception as exc:
            db.rollback()
            logger.error("pierre.legacy_adapter.bulk_upsert.error", extra={"error": str(exc)})
            raise
        finally:
            db.close()

        return {"inserted": inserted, "skipped": skipped}
