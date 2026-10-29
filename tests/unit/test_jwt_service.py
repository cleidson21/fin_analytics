"""JWT issuance contracts using a synthetic secret and fixed UTC clock."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from jose import jwt

from backend.infrastructure.security import jwt_service


SECRET = "synthetic-jwt-issuance-secret-only-for-tests"
USER_ID = "00000000-0000-0000-0000-000000009102"
FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0)


@pytest.mark.parametrize("minutes,days", [(60, 7), (15, 2)])
def test_issuance_preserves_claims_lifetimes_algorithm_and_unique_jti(monkeypatch, minutes, days):
    monkeypatch.setattr(jwt_service, "datetime", SimpleNamespace(utcnow=lambda: FIXED_NOW))
    service = jwt_service.JWTService(SECRET, minutes, days)
    tokens = [
        (service.create_access_token(USER_ID), "access", timedelta(minutes=minutes)),
        (service.create_refresh_token(USER_ID), "refresh", timedelta(days=days)),
        (service.create_access_token(USER_ID), "access", timedelta(minutes=minutes)),
        (service.create_refresh_token(USER_ID), "refresh", timedelta(days=days)),
    ]
    jtis = set()
    for token, token_type, lifetime in tokens:
        # Fixed historical clock: only expiration comparison is disabled here.
        # Signature verification remains active; expiry is tested at the HTTP boundary.
        claims = jwt.decode(token, SECRET, algorithms=["HS256"], options={"verify_exp": False})
        assert set(claims) == {"sub", "exp", "iat", "jti", "type"}
        assert claims["sub"] == USER_ID
        assert claims["type"] == token_type
        assert claims["iat"] == int(FIXED_NOW.replace(tzinfo=timezone.utc).timestamp())
        assert claims["exp"] - claims["iat"] == int(lifetime.total_seconds())
        assert jwt.get_unverified_header(token)["alg"] == "HS256"
        assert str(UUID(claims["jti"])) == claims["jti"]
        jtis.add(claims["jti"])
    assert len(jtis) == len(tokens)


@pytest.mark.parametrize("kind", ["access", "refresh"])
def test_generic_verifier_keeps_validating_both_token_types(kind):
    service = jwt_service.JWTService(SECRET, 60, 7)
    token = getattr(service, f"create_{kind}_token")(USER_ID)
    assert service.verify_token(token)["type"] == kind


@pytest.mark.parametrize("failure", ["expired", "signature", "algorithm", "malformed"])
def test_generic_verifier_rejects_invalid_tokens(failure):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {"sub": USER_ID, "exp": now + 3600, "iat": now, "jti": "synthetic-jti", "type": "access"}
    secret, algorithm = SECRET, "HS256"
    if failure == "expired":
        claims["exp"] = now - 60
    elif failure == "signature":
        secret = "different-synthetic-secret"
    elif failure == "algorithm":
        algorithm = "HS384"
    token = "not-a-jwt" if failure == "malformed" else jwt.encode(claims, secret, algorithm=algorithm)
    with pytest.raises(ValueError):
        jwt_service.JWTService(SECRET, 60, 7).verify_token(token)
