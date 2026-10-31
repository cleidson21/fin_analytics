"""Offline operator: python -m scripts.certify_local_ledger --help.

Never calls Pierre or changes SQLite. Stop the application before issuing or
revoking certificates. Review files contain local account identifiers/names;
keep them private. No password, API key or token is an argument or output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.application.services.local_ledger_scope import (
    CAPABILITIES, LedgerCertificate, LedgerScopeDenied, ReviewedAccount, ReviewedAccountCollision,
    collision_ids, validate_collision_reviews,
    connection_fingerprint, database_identity, fingerprint, inventory,
)
from backend.application.services.single_tenant_user_scope import SingleTenantUserScopeGuard
from backend.core.config import settings
from backend.database.url import sync_database_url
from backend.infrastructure.persistence.models.user import UserModel


def write_new(path: Path, value: object) -> None:
    # Exclusive create: never clobber an existing review/manifest/installation.
    with path.open("x", encoding="utf-8") as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass  # Windows uses inherited directory ACLs; operator must restrict them.


def installation_path() -> Path:
    if not settings.LOCAL_LEDGER_INSTALLATION_FILE:
        raise ValueError("Configure LOCAL_LEDGER_INSTALLATION_FILE with a private absolute path")
    path = Path(settings.LOCAL_LEDGER_INSTALLATION_FILE)
    if not path.is_absolute():
        raise ValueError("Installation path must be absolute")
    return path


def reviewed_inventory(db: Session) -> dict:
    users = tuple(db.execute(select(UserModel.id)).scalars())
    if len(users) != 1:
        raise ValueError("Certification requires exactly one stored application user")
    owner = SingleTenantUserScopeGuard().resolve(db, UUID(str(users[0])))
    marker = json.loads(installation_path().read_text(encoding="utf-8"))
    return {
        "version": 1, "user_id": str(owner.user_id),
        "installation_id": str(UUID(marker["installation_id"])),
        "generation": str(UUID(marker["generation"])),
        "database_identity": database_identity(db),
        "connection_fingerprint": connection_fingerprint(),
        "inventory": inventory(db),
    }


def issue_certificate(db: Session, review: dict, *, days: int, capabilities: set[str]) -> LedgerCertificate:
    current = reviewed_inventory(db)
    reviewed = {k: v for k, v in review.items() if k not in {
        "account_confirmations", "connection_evidence", "account_collision_confirmations"
    }}
    if current != reviewed or not 1 <= days <= 30 or not capabilities or not capabilities <= CAPABILITIES:
        raise ValueError("Review is stale/inconsistent, lifetime invalid, or capabilities invalid")
    confirmations = review.get("account_confirmations", [])
    connection_evidence = review.get("connection_evidence", "")
    if not isinstance(connection_evidence, str) or not connection_evidence.strip() or connection_evidence == "PENDING OWNER REVIEW":
        raise ValueError("Explicit connection review evidence is required")
    accounts = tuple(ReviewedAccount.model_validate(account) for account in confirmations)
    expected = current["inventory"]["accounts"]
    if ([{"provider": a.provider, "external_id": a.external_id, "name": a.name} for a in accounts] != expected
            or any(not a.evidence.strip() or a.evidence == "PENDING OWNER REVIEW" for a in accounts)):
        raise ValueError("Explicit evidence is required for every reviewed account")
    collisions = tuple(ReviewedAccountCollision.model_validate(c)
                       for c in review.get("account_collision_confirmations", []))
    validate_collision_reviews(accounts, collisions)
    if "import" in capabilities and any(c.import_provider is None for c in collisions):
        raise ValueError("Explicit connection import namespace is required for every collision")
    now = datetime.now(timezone.utc)
    return LedgerCertificate(
        version=1, certificate_id=uuid4(), installation_id=UUID(current["installation_id"]),
        generation=UUID(current["generation"]), user_id=UUID(current["user_id"]),
        database_identity=current["database_identity"], connection_id=uuid4(),
        connection_fingerprint=current["connection_fingerprint"], accounts=accounts,
        account_collision_confirmations=collisions,
        connection_evidence=connection_evidence,
        capabilities=frozenset(capabilities),
        reviewed_inventory_digest=fingerprint("local-ledger-review-v1", current),
        issued_at=now, expires_at=now + timedelta(days=days),
    )


def envelope(cert: LedgerCertificate) -> dict:
    payload = cert.model_dump(mode="json")
    return {"payload": payload, "signature": fingerprint("local-ledger-certificate-v1", payload)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "prepare", "certify", "revoke"))
    parser.add_argument("--review", type=Path)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--capability", action="append", choices=sorted(CAPABILITIES))
    parser.add_argument("--confirm-reviewed-accounts", action="store_true")
    parser.add_argument("--confirm-reviewed-connection", action="store_true")
    args = parser.parse_args(argv)
    try:
        if settings.ENVIRONMENT != "development":
            raise ValueError("Personal-local certification is restricted to development")
        marker_path = installation_path()
        if args.action == "init":
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            write_new(marker_path, {"installation_id": str(uuid4()), "generation": str(uuid4())})
        elif args.action == "revoke":
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            if set(marker) != {"installation_id", "generation"}:
                raise ValueError("Invalid installation marker")
            UUID(marker["installation_id"])
            UUID(marker["generation"])
            marker["generation"] = str(uuid4())
            replacement = marker_path.with_name(marker_path.name + "." + uuid4().hex + ".tmp")
            write_new(replacement, marker)
            os.replace(replacement, marker_path)
        else:
            if args.review is None or not args.review.is_absolute():
                raise ValueError("--review requires a private absolute path")
            url = sync_database_url(settings.DATABASE_URL)
            if url.get_backend_name() != "sqlite" or not url.database:
                raise ValueError("An existing local SQLite database is required")
            path = Path(url.database).resolve(strict=True)
            # SQLite cannot create or write the operational database here.
            engine = create_engine(url, creator=lambda: __import__("sqlite3").connect(
                path.as_uri() + "?mode=ro", uri=True))
            try:
                with Session(engine) as db:
                    if args.action == "prepare":
                        review = reviewed_inventory(db)
                        review["connection_evidence"] = "PENDING OWNER REVIEW"
                        review["account_confirmations"] = [
                            {**a, "evidence": "PENDING OWNER REVIEW"} for a in review["inventory"]["accounts"]
                        ]
                        review["account_collision_confirmations"] = [
                            {"external_id": i, "relationship": "PENDING OWNER REVIEW",
                             "evidence": "PENDING OWNER REVIEW", "import_provider": None}
                            for i in sorted(collision_ids({(a["provider"], a["external_id"])
                                                           for a in review["inventory"]["accounts"]}))
                        ]
                        write_new(args.review, review)
                    else:
                        if not args.confirm_reviewed_accounts or not args.confirm_reviewed_connection or not args.capability:
                            raise ValueError("Explicit account confirmation and capabilities are required")
                        cert = issue_certificate(db, json.loads(args.review.read_text(encoding="utf-8")),
                                                 days=args.days, capabilities=set(args.capability))
                        if not settings.LOCAL_LEDGER_CERTIFICATE_FILE:
                            raise ValueError("Configure LOCAL_LEDGER_CERTIFICATE_FILE")
                        target = Path(settings.LOCAL_LEDGER_CERTIFICATE_FILE)
                        if not target.is_absolute():
                            raise ValueError("Certificate path must be absolute")
                        write_new(target, envelope(cert))
            finally:
                engine.dispose()
        print("Local certification procedure completed. No financial records were modified.")
        return 0
    except (OSError, ValueError, KeyError, LedgerScopeDenied, SQLAlchemyError):
        print("Certification refused. Check local configuration, inventory and explicit account evidence; no secrets are required.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
