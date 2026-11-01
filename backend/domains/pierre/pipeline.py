"""One certified RAW-preserving importer shared by both public Pierre routes."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from time import monotonic
from uuid import uuid4

from backend.application.services.local_ledger_scope import (
    CertifiedLedgerScope, DENIED, LedgerScopeDenied, PIERRE_NAMESPACES, canonical,
)
from backend.domains.pierre.connector import PierreConnector
from backend.domains.pierre.mapper import PierreMapper
from backend.domains.pierre.repository import AccountRepository, CategoryRepository, TransactionRepository
from backend.domain.enums.provider_type import ProviderType
from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus


class PierreImportPipeline:
    """Import the inclusive civil-date interval of RAW ``date``, not purchaseDate.

    Pierre documents YYYY-MM-DD filters, but its raw response can include older
    transactions even while echoing the requested filters (observed 2026-11-01).
    For ISO timestamps, retain the date in the supplied offset, as the mapper
    and persisted ledger already do; never shift it using the host timezone.
    Validate every returned row and identity before excluding out-of-range rows.
    See https://docs.pierre.finance/api-reference/rest/get-transactions.
    """

    def __init__(self, scope: CertifiedLedgerScope):
        self.scope = scope

    async def run(self, start_date=None, end_date=None):
        started = monotonic()
        started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date or date.today()
        start = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date or end - timedelta(days=90)
        if start > end:
            raise ValueError("Invalid date range")
        self.scope.revalidate("import")
        self.scope.db.rollback()  # Release the read snapshot before provider I/O.
        # Construct the existing provider only AFTER authorization. Finish fetching
        # and validating the complete response BEFORE any financial mutation.
        payload = await PierreConnector().get_transactions(start.isoformat(), end.isoformat())
        if (not isinstance(payload, dict) or payload.get("success") is not True
                or not isinstance(payload.get("data"), list)
                or payload.get("has_more") or payload.get("next_cursor") or payload.get("next_page")
                or payload.get("partial") or payload.get("errors")):
            raise ValueError("Incomplete provider response")
        raw_rows = payload["data"]
        for count_field in ("total", "count"):
            if count_field in payload and (type(payload[count_field]) is not int
                                          or payload[count_field] != len(raw_rows)):
                raise ValueError("Incomplete provider response")
        allowed = {(a.provider, a.external_id) for a in self.scope.certificate.accounts}
        # Never collapse a colliding set with last-wins dict construction.
        accounts_by_external_id = {}
        for provider, external_id in allowed:
            candidates = {p for p, i in allowed if i == external_id}
            if len(candidates) == 1:
                accounts_by_external_id[external_id] = provider
        for collision in self.scope.certificate.account_collision_confirmations:
            if collision.import_provider is None:
                raise LedgerScopeDenied(DENIED)
            accounts_by_external_id[collision.external_id] = collision.import_provider
        prepared = {}
        for raw in raw_rows:
            if not isinstance(raw, dict) or not all(raw.get(k) is not None for k in (
                "id", "account_id", "description", "amount", "currency_code", "date", "status", "type"
            )):
                raise ValueError("Incomplete transaction")
            if not isinstance(raw["id"], str) or not raw["id"] or not isinstance(raw["account_id"], str):
                raise ValueError("Invalid transaction identity")
            if any(not isinstance(raw[k], str) or not raw[k] for k in (
                "description", "currency_code", "date", "status", "type"
            )):
                raise ValueError("Invalid transaction attributes")
            if raw["account_id"] not in accounts_by_external_id:
                raise LedgerScopeDenied(DENIED)
            try:
                if isinstance(raw["amount"], (float, bool)):
                    raise ValueError("Lossy monetary input")
                amount = Decimal(raw["amount"])
                if (not amount.is_finite() or abs(amount) > Decimal("9999999999.99")
                        or amount != amount.quantize(Decimal("0.01"))):
                    raise ValueError("Invalid money")
                account, transaction, category = PierreMapper.map_transaction(raw)
                # Use the reviewed account's exact namespace; never relabel history.
                account["provider"] = accounts_by_external_id[raw["account_id"]]
                transaction["account_provider"] = account["provider"]
                transaction["provider"] = account["provider"]
                transaction["amount"] = amount
            except (InvalidOperation, TypeError, OverflowError) as error:
                raise ValueError("Invalid transaction") from error
            # Omitted or null optional identity/RAW fields cannot erase prior data.
            for target, source in {
                "name": "account_name", "type": "account_type", "subtype": "account_subtype",
                "bank": "item_bank_name", "connector": "connector_name", "credit_metadata_json": "account_credit_data",
            }.items():
                if source not in raw or (source in {"account_name", "account_type"} and raw[source] is None):
                    account.pop(target, None)
            for field in ("original_description", "original_category", "manual_transaction"):
                if field not in raw or (field == "original_description" and raw[field] is None):
                    transaction.pop(field, None)
            if "merchant" not in raw:
                transaction.pop("merchant_name", None)
            if "payment_data" not in raw:
                transaction.pop("receiver_name", None)
                transaction.pop("payer_name", None)
            if "credit_card_data" not in raw:
                for field in ("installment_number", "total_installments", "purchase_date"):
                    transaction.pop(field, None)
                if "bill_id" not in raw:
                    transaction.pop("bill_id", None)
            if raw.get("category") is None:
                transaction.pop("category", None)
            if not transaction["extra_json"]:
                transaction.pop("extra_json")
            key = transaction["external_id"]
            row = (account, transaction, category)
            if key in prepared:
                # Aware datetimes may compare equal as instants while carrying
                # different civil dates/times. Those cannot be last-wins inputs
                # to either period selection or the existing naive ledger date.
                previous = prepared[key]
                if (previous != row or previous[1]["date"].replace(tzinfo=None)
                        != transaction["date"].replace(tzinfo=None)):
                    raise ValueError("Conflicting duplicate provider identity")
            prepared[key] = row

        db = self.scope.db
        try:
            self.scope.begin_write("import")
            accounts, categories, transactions = AccountRepository(), CategoryRepository(), TransactionRepository()
            from backend.domains.pierre.models import Category, Transaction
            existing_transactions = {}
            # Validate the complete existing-to-destination relation before writes.
            for _, transaction, _ in prepared.values():
                existing = db.query(Transaction).filter(
                    Transaction.external_id == transaction["external_id"],
                    Transaction.provider.in_(PIERRE_NAMESPACES),
                ).one_or_none()
                existing_transactions[transaction["external_id"]] = existing
                if existing and (existing.account_provider, existing.account_external_id) not in allowed:
                    raise LedgerScopeDenied(DENIED)
                if existing and existing.account_provider != transaction["account_provider"]:
                    # Even confirmed financial equivalence grants no permission
                    # to move historical transactions across stored namespaces.
                    raise LedgerScopeDenied(DENIED)
                if existing is not None:
                    transaction["provider"] = existing.provider
            # Filter only after validating the complete provider response AND
            # existing identity bindings, including rows outside the interval.
            # Excluded rows never reach any account/category/transaction upsert.
            validated_count = len(prepared)
            prepared = {key: row for key, row in prepared.items()
                        if start <= row[1]["date"].date() <= end}
            out_of_range = validated_count - len(prepared)
            inserted = updated = skipped = 0
            effects = []
            for account, transaction, category in prepared.values():
                existing = existing_transactions[transaction["external_id"]]
                if existing is not None and "extra_json" in transaction and existing.extra_json:
                    previous_extra = json.loads(existing.extra_json)
                    if not isinstance(previous_extra, dict):
                        raise ValueError("Invalid existing RAW metadata")
                    transaction["extra_json"] = json.dumps({**previous_extra, **json.loads(transaction["extra_json"])}, default=str)
                equal = existing is not None and all(
                    getattr(existing, k) == (v.replace(tzinfo=None) if isinstance(v, datetime) else v)
                    for k, v in transaction.items()
                )
                effect = "INSERT" if existing is None else "SKIP" if equal else "UPDATE"
                effects.append({"provider": transaction["provider"], "external_id": transaction["external_id"],
                                "account_provider": transaction["account_provider"],
                                "account_external_id": transaction["account_external_id"], "action": effect})
                if existing is None:
                    inserted += 1
                elif equal:
                    skipped += 1
                    continue
                else:
                    updated += 1
                # The account already exists by certification; preserve absent data.
                current_account = accounts.get_by_external_id(db, account["provider"], account["external_id"])
                account.setdefault("name", current_account.name)
                account.setdefault("type", current_account.type)
                accounts.upsert(db, account)
                if transaction.get("category") is not None and not db.query(Category).filter(
                    Category.name == category["name"]
                ).count():
                    categories.insert_if_not_exists(db, category)
                transactions.upsert(db, transaction)
                db.flush()
            duration = round(monotonic() - started, 3)
            run_id = str(uuid4())
            db.add(SyncLogModel(
                id=run_id, user_id=str(self.scope.certificate.user_id), provider=ProviderType.PIERRE,
                status=SyncStatus.SUCCESS, start_time=started_at,
                end_time=datetime.now(timezone.utc).replace(tzinfo=None),
                duration_seconds=duration, accounts_synced=len({(r[1]["account_provider"], r[1]["account_external_id"])
                                                               for r in prepared.values()}),
                transactions_synced=len(prepared), categories_synced=len({r[2]["name"] for r in prepared.values()}),
                inserted=inserted, updated=updated, ignored=skipped,
                provider_metadata={
                    "certificate_id": str(self.scope.certificate.certificate_id), "certificate_version": 1,
                    "connection_id": str(self.scope.certificate.connection_id),
                    "date_filter": {
                        "basis": "raw.date/civil-date-as-supplied", "inclusive": True,
                        "start": start.isoformat(), "end": end.isoformat(),
                        "received_rows": len(raw_rows), "validated_unique_transactions": validated_count,
                        "selected_transactions": len(prepared), "excluded_out_of_range": out_of_range,
                    },
                    "effects": effects,
                    "effect_identity_digest": sha256(canonical(effects)).hexdigest(),
                },
            ))
            db.flush()
            self.scope.revalidate("import")
            db.commit()  # Ledger and successful provenance run commit together.
        except Exception:
            db.rollback()
            raise
        return {
            "accounts": len({(r[1]["account_provider"], r[1]["account_external_id"]) for r in prepared.values()}),
            "categories": len({r[2]["name"] for r in prepared.values()}),
            "transactions": inserted + updated, "inserted": inserted, "updated": updated,
            "skipped": skipped, "out_of_range": out_of_range, "run_id": run_id, "duration_seconds": duration,
            "date_range_start": start, "date_range_end": end,
        }
