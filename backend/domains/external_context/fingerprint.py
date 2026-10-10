"""Normative Content Fingerprint V1 serialization and hashing."""

from __future__ import annotations

import hashlib
import json

from .models import ContentFingerprintV1, NormalizedExternalContent
from .normalization import validate_and_normalize_content


CONTENT_FINGERPRINT_VERSION = 1
DOMAIN_PREFIX_V1 = b"FINANALYTICS/EXTERNAL_CONTEXT/CONTENT_FINGERPRINT/V1\x00"


def canonical_json_v1(
    payload: object | NormalizedExternalContent,
) -> str:
    normalized = validate_and_normalize_content(
        payload.as_payload_v1()
        if isinstance(payload, NormalizedExternalContent)
        else payload
    )
    return json.dumps(
        normalized.as_payload_v1(),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def build_content_fingerprint_v1(payload: object) -> ContentFingerprintV1:
    normalized = validate_and_normalize_content(payload)
    canonical_json = canonical_json_v1(normalized)
    digest = hashlib.sha256(DOMAIN_PREFIX_V1 + canonical_json.encode("utf-8"))
    return ContentFingerprintV1(
        content_fingerprint_version=CONTENT_FINGERPRINT_VERSION,
        content_fingerprint=f"sha256:{digest.hexdigest()}",
        canonical_json=canonical_json,
        normalized_content=normalized,
    )
