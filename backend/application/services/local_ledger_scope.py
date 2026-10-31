"""Revocable personal-local certification; not general multi-user ownership.

No import-time I/O, schema creation, provider calls or automatic certification.
The offline operator signs a reviewed inventory. JWT remains the auth owner.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.application.services.single_tenant_user_scope import SingleTenantUserScopeGuard
from backend.core.config import settings
from backend.domains.pierre.models import Account, Category, GovernanceAuditLog, Transaction

CAPABILITIES = frozenset({"read", "import", "governance.write", "history"})
PIERRE_NAMESPACES = frozenset({"pierre", "PIERRE"})
DENIED = "Legacy financial scope unavailable: ownership is not certified"


class LedgerScopeDenied(Exception):
    """Safe denial without credentials, SQL or financial payloads."""


class ReviewedAccount(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider: Literal["pierre", "PIERRE"]
    external_id: str = Field(min_length=1)
    name: str
    evidence: str = Field(min_length=1, max_length=500)


class ReviewedAccountCollision(BaseModel):
    """Owner decision for both exact namespaces sharing this external ID.

    Equivalence never merges keys. Import routing is a separate, explicit
    binding of this connection's unqualified account_id to one stored key.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)
    external_id: str = Field(min_length=1)
    relationship: Literal["SAME_FINANCIAL_ACCOUNT", "DISTINCT_FINANCIAL_ACCOUNTS"]
    evidence: str = Field(min_length=1, max_length=500)
    import_provider: Literal["pierre", "PIERRE"] | None = None


def collision_ids(keys: set[tuple[str, str]]) -> set[str]:
    return {i for _, i in keys if sum(other == i for _, other in keys) > 1}


def validate_collision_reviews(accounts, collisions) -> None:
    keys = {(a.provider, a.external_id) for a in accounts}
    if (len({c.external_id for c in collisions}) != len(collisions)
            or {c.external_id for c in collisions} != collision_ids(keys)
            or any(not c.evidence.strip() or c.evidence.strip() == "PENDING OWNER REVIEW"
                   or (c.import_provider is not None and (c.import_provider, c.external_id) not in keys)
                   for c in collisions)):
        raise ValueError("Explicit relationship evidence is required for every account collision")


class LedgerCertificate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1]
    certificate_id: UUID
    installation_id: UUID
    generation: UUID
    user_id: UUID
    database_identity: str
    connection_id: UUID
    connection_fingerprint: str
    connection_evidence: str = Field(min_length=1, max_length=500)
    accounts: tuple[ReviewedAccount, ...]
    # Additive V1 field: existing certificates without collisions stay valid.
    account_collision_confirmations: tuple[ReviewedAccountCollision, ...] = ()
    capabilities: frozenset[str]
    reviewed_inventory_digest: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def fingerprint(purpose: str, value: object) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), purpose.encode() + b"\0" + canonical(value), "sha256").hexdigest()


def connection_fingerprint() -> str:
    if not settings.PIERRE_API_KEY:
        raise LedgerScopeDenied(DENIED)
    return fingerprint("local-ledger-connection-v1", settings.PIERRE_API_KEY)


def configured_path(value: str | None) -> Path:
    if not value or not Path(value).is_absolute():
        raise LedgerScopeDenied(DENIED)
    return Path(value).resolve(strict=True)


def database_identity(db: Session) -> str:
    url = db.get_bind().url
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise LedgerScopeDenied(DENIED)
    path = Path(url.database).resolve(strict=True)
    stat = path.stat()
    if not stat.st_ino:
        raise LedgerScopeDenied(DENIED)
    return fingerprint("local-ledger-database-v1", [str(path), stat.st_dev, stat.st_ino])


def inventory(db: Session) -> dict:
    """Certify the complete Pierre-only universe, never hide unknown rows.

    No amounts or transaction descriptions leave the database in this inventory.
    """
    accounts = db.execute(select(Account.provider, Account.external_id, Account.name)).all()
    keys = {(p, i) for p, i, _ in accounts}
    if not keys or len(keys) != len(accounts) or any(p not in PIERRE_NAMESPACES or not i for p, i in keys):
        raise LedgerScopeDenied(DENIED)
    transactions = db.execute(select(Transaction.provider, Transaction.external_id,
                                     Transaction.account_provider, Transaction.account_external_id)).all()
    tx_keys = {(p, i) for p, i, _, _ in transactions}
    if (any(p not in PIERRE_NAMESPACES or not i or (ap, ai) not in keys for p, i, ap, ai in transactions)
            or len({i for _, i in tx_keys}) != len(tx_keys)):
        raise LedgerScopeDenied(DENIED)
    categories = db.execute(select(Category.provider, Category.name)).all()
    if any(p not in PIERRE_NAMESPACES for p, _ in categories):
        raise LedgerScopeDenied(DENIED)
    audits = db.execute(select(GovernanceAuditLog.id, GovernanceAuditLog.provider,
                              GovernanceAuditLog.external_id)).all()
    if any((p, i) not in tx_keys for _, p, i in audits):
        raise LedgerScopeDenied(DENIED)
    return {
        "accounts": [{"provider": p, "external_id": i, "name": n} for p, i, n in sorted(accounts)],
        "transaction_count": len(transactions), "audit_count": len(audits),
        "legacy_identity_digest": sha256(canonical({
            "transactions": sorted(tuple(r) for r in transactions),
            "categories": sorted(tuple(r) for r in categories),
            "audits": sorted(tuple(r) for r in audits),
        })).hexdigest(),
    }


def read_certificate() -> LedgerCertificate:
    try:
        envelope = json.loads(configured_path(settings.LOCAL_LEDGER_CERTIFICATE_FILE).read_text(encoding="utf-8"))
        if set(envelope) != {"payload", "signature"} or not hmac.compare_digest(
            envelope["signature"], fingerprint("local-ledger-certificate-v1", envelope["payload"])
        ):
            raise LedgerScopeDenied(DENIED)
        cert = LedgerCertificate.model_validate(envelope["payload"])
        validate_collision_reviews(cert.accounts, cert.account_collision_confirmations)
        if "import" in cert.capabilities and any(c.import_provider is None for c in cert.account_collision_confirmations):
            raise LedgerScopeDenied(DENIED)
        installation = json.loads(configured_path(settings.LOCAL_LEDGER_INSTALLATION_FILE).read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        if (cert.revoked or cert.issued_at.tzinfo is None or cert.expires_at.tzinfo is None
                or not cert.issued_at <= now < cert.expires_at
                or str(cert.installation_id) != installation["installation_id"]
                or str(cert.generation) != installation["generation"]
                or not cert.capabilities <= CAPABILITIES or not cert.accounts
                or any(not a.evidence.strip() or a.evidence == "PENDING OWNER REVIEW" for a in cert.accounts)
                or not cert.connection_evidence.strip() or cert.connection_evidence == "PENDING OWNER REVIEW"
                or len({(a.provider, a.external_id) for a in cert.accounts}) != len(cert.accounts)
                or not hmac.compare_digest(cert.connection_fingerprint, connection_fingerprint())):
            raise LedgerScopeDenied(DENIED)
        return cert
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise LedgerScopeDenied(DENIED) from error


def resolve_scope(db: Session, user_id: UUID, capability: str) -> LedgerCertificate:
    if not settings.LOCAL_LEDGER_ENABLED or settings.ENVIRONMENT != "development":
        raise LedgerScopeDenied(DENIED)
    cert = read_certificate()
    try:
        owner = SingleTenantUserScopeGuard().resolve(db, user_id)
    except Exception as error:
        # The existing guard owns UUID/count checks; do not invent another one.
        raise LedgerScopeDenied(DENIED) from error
    if owner.user_id != cert.user_id or capability not in cert.capabilities:
        raise LedgerScopeDenied(DENIED)
    if cert.database_identity != database_identity(db):
        raise LedgerScopeDenied(DENIED)
    current = inventory(db)
    if {(a["provider"], a["external_id"]) for a in current["accounts"]} != {
        (a.provider, a.external_id) for a in cert.accounts
    }:
        raise LedgerScopeDenied(DENIED)
    return cert


@dataclass(frozen=True)
class CertifiedLedgerScope:
    db: Session
    certificate: LedgerCertificate

    def revalidate(self, capability: str) -> LedgerCertificate:
        cert = resolve_scope(self.db, self.certificate.user_id, capability)
        if cert != self.certificate:
            raise LedgerScopeDenied(DENIED)
        return cert

    def begin_write(self, capability: str) -> None:
        # Recheck under SQLite's writer lock. Provider I/O happens before this.
        self.db.rollback()
        self.db.execute(text("BEGIN IMMEDIATE"))
        self.revalidate(capability)
