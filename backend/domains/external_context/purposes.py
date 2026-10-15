"""Closed R3-F1 purposes and immutable access matrix."""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping

from .enums import RegistryKey


class ExternalReferencePurpose(str, Enum):
    MARKET_INTEREST_RATE_REFERENCE = "MARKET_INTEREST_RATE_REFERENCE"
    MARKET_INFLATION_REFERENCE = "MARKET_INFLATION_REFERENCE"
    MARKET_FX_REFERENCE = "MARKET_FX_REFERENCE"


EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST: Mapping[
    ExternalReferencePurpose,
    frozenset[RegistryKey],
] = MappingProxyType(
    {
        ExternalReferencePurpose.MARKET_INTEREST_RATE_REFERENCE: frozenset(
            {
                RegistryKey.BCB_SGS_SELIC_TARGET,
                RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
                RegistryKey.BCB_SGS_CDI,
            }
        ),
        ExternalReferencePurpose.MARKET_INFLATION_REFERENCE: frozenset(
            {RegistryKey.BCB_SGS_IPCA_MONTHLY}
        ),
        ExternalReferencePurpose.MARKET_FX_REFERENCE: frozenset(
            {RegistryKey.BCB_SGS_USD_SELL}
        ),
    }
)


__all__ = [
    "EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST",
    "ExternalReferencePurpose",
]
