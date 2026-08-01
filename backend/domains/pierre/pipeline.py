"""
pipeline.py — Domínio Pierre

Lógica central de mapeamento Pierre API → estruturas do banco.

Responsabilidade única:
  Dado um PierreTransactionRaw (payload validado), extrair:
    - dict de account (para AccountRepository.upsert_many)
    - dict de transaction (para TransactionRepository.upsert_many)
    - str de category name (para CategoryRepository.insert_ignore_many)

Regras absolutas:
  - Nenhum campo calculado ou deduzido
  - Nenhum enriquecimento de dados
  - Persistir exatamente o que foi recebido
  - Campos não mapeados → extra_json (via build_extra_json())
  - O pipeline não sabe nada sobre frontend ou outros domínios
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from backend.domains.pierre.schemas import PierreTransactionRaw


PROVIDER = "pierre"


def map_account(txn: PierreTransactionRaw, sync_at: datetime) -> dict:
    """
    Extrai os dados de conta a partir de uma transação bruta.

    A Pierre entrega dados de conta desnormalizados em cada transação.
    Usamos esses campos para fazer UPSERT na tabela accounts.
    account_credit_data é serializado como JSON bruto em credit_metadata_json.
    """
    credit_meta = None
    if txn.account_credit_data is not None:
        try:
            credit_meta = json.dumps(txn.account_credit_data, default=str)
        except (TypeError, ValueError):
            credit_meta = str(txn.account_credit_data)

    return {
        "provider": PROVIDER,
        "external_id": txn.account_id,
        "name": txn.account_name or "",
        "type": txn.account_type or "",
        "subtype": txn.account_subtype,
        "bank": txn.item_bank_name,
        "connector": txn.connector_name,
        "credit_metadata_json": credit_meta,
        "last_sync": sync_at,
    }


def map_transaction(txn: PierreTransactionRaw) -> dict:
    """
    Extrai os dados de transação a partir do payload bruto.

    Mapeamento 1:1 conforme docs/16_PIERRE_REFERENCE.md:
      Pierre.id               → external_id
      Pierre.account_id       → account_external_id
      Pierre.currency_code    → currency
      Pierre.credit_card_data → installment_number, total_installments, etc.
      Pierre.payment_data     → payer_name, receiver_name
      Pierre.merchant.name    → merchant_name
      Demais campos           → extra_json (via build_extra_json())
    """
    ccd = txn.credit_card_data

    return {
        "provider": PROVIDER,
        "external_id": txn.id,
        "account_provider": PROVIDER,
        "account_external_id": txn.account_id,
        # Dados canônicos
        "description": txn.description,
        "original_description": txn.original_description,
        "category": txn.category,
        "original_category": txn.original_category,
        "amount": txn.amount,
        "currency": txn.currency_code,
        "date": txn.date,
        "status": txn.status,
        "type": txn.type,
        # Dados desnormalizados pesquisáveis
        "merchant_name": txn.merchant_name,
        "bill_id": ccd.billId if ccd else txn.bill_id,
        "installment_number": ccd.installmentNumber if ccd else None,
        "total_installments": ccd.totalInstallments if ccd else None,
        "purchase_date": ccd.purchaseDate if ccd else None,
        "receiver_name": txn.receiver_name,
        "payer_name": txn.payer_name,
        # Flags
        "manual_transaction": txn.manual_transaction,
        # Escape hatch — campos não mapeados
        "extra_json": txn.build_extra_json(),
    }


def map_category_name(txn: PierreTransactionRaw) -> Optional[str]:
    """Retorna o nome da categoria da transação, se existir."""
    return txn.category if txn.category else None


def build_account_dedup_key(account_dict: dict) -> str:
    """Chave de deduplicação para evitar UPSERTs redundantes da mesma conta."""
    return f"{account_dict['provider']}:{account_dict['external_id']}"


def process_payload(
    transactions_raw: list[PierreTransactionRaw],
    sync_at: datetime,
) -> tuple[list[dict], list[dict], list[str]]:
    """
    Processa lista de transações brutas e retorna tupla com:
      (accounts_to_upsert, transactions_to_upsert, category_names)

    Deduplicação de accounts: uma conta pode aparecer em muitas transações,
    mas fazemos UPSERT apenas uma vez por conta única.
    """
    accounts_map: dict[str, dict] = {}
    transactions: list[dict] = []
    categories: list[str] = []

    for txn in transactions_raw:
        # Deduplica accounts por (provider, account_id)
        acc_dict = map_account(txn, sync_at)
        key = build_account_dedup_key(acc_dict)
        accounts_map[key] = acc_dict  # Última versão prevalece (mais recente no payload)

        # Transações — sem deduplicação aqui, o UPSERT cuida disso no banco
        transactions.append(map_transaction(txn))

        # Categorias
        cat = map_category_name(txn)
        if cat:
            categories.append(cat)

    return list(accounts_map.values()), transactions, categories
