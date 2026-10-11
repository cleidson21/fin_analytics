"""Canonical UTC TEXT codec for governed External Context persistence."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from backend.domain.exceptions.base import FINAnalyticsError


UTC_TEXT_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z",
    flags=re.ASCII,
)
UTC_TEXT_LENGTH = 27


class UTCCodecError(FINAnalyticsError):
    """Raised when a timestamp cannot cross the canonical persistence boundary."""

    def __init__(self, message: str, *, field: str = "timestamp") -> None:
        super().__init__(message)
        self.code = "INVALID_UTC_PERSISTENCE_TEXT"
        self.field = field


def encode_utc_timestamp(value: datetime, *, field: str = "timestamp") -> str:
    """Serialize an aware zero-offset datetime to exact 27-byte UTC text."""

    if type(value) is not datetime:
        raise UTCCodecError(f"{field} must be a datetime.", field=field)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise UTCCodecError(
            f"{field} must be timezone-aware with an exact zero UTC offset.",
            field=field,
        )
    canonical = value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if len(canonical) != UTC_TEXT_LENGTH or not canonical.isascii():
        raise UTCCodecError(f"{field} is outside the canonical datetime range.", field=field)
    return canonical


def decode_utc_timestamp(value: str, *, field: str = "timestamp") -> datetime:
    """Validate canonical persisted text and return an aware UTC datetime."""

    if type(value) is not str or len(value) != UTC_TEXT_LENGTH:
        raise UTCCodecError(
            f"{field} must be exactly {UTC_TEXT_LENGTH} ASCII characters.",
            field=field,
        )
    if not value.isascii() or UTC_TEXT_PATTERN.fullmatch(value) is None:
        raise UTCCodecError(f"{field} is not canonical UTC persistence text.", field=field)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise UTCCodecError(f"{field} is not a valid civil UTC instant.", field=field) from exc
    if encode_utc_timestamp(parsed, field=field) != value:
        raise UTCCodecError(f"{field} does not roundtrip canonically.", field=field)
    return parsed
