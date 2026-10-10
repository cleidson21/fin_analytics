"""Closed semantic codes for the R3-C External Context domain."""

from enum import Enum


class Provider(str, Enum):
    BCB_SGS = "BCB_SGS"


class RegistryKey(str, Enum):
    BCB_SGS_SELIC_TARGET = "BCB_SGS_SELIC_TARGET"
    BCB_SGS_SELIC_EFFECTIVE = "BCB_SGS_SELIC_EFFECTIVE"
    BCB_SGS_CDI = "BCB_SGS_CDI"
    BCB_SGS_IPCA_MONTHLY = "BCB_SGS_IPCA_MONTHLY"
    BCB_SGS_USD_SELL = "BCB_SGS_USD_SELL"


class Frequency(str, Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


class Unit(str, Enum):
    PERCENT_PER_YEAR = "PERCENT_PER_YEAR"
    PERCENT_PER_DAY = "PERCENT_PER_DAY"
    PERCENT_MONTHLY_CHANGE = "PERCENT_MONTHLY_CHANGE"
    BRL_PER_USD = "BRL_PER_USD"


class Scope(str, Enum):
    BR = "BR"


class SemanticClass(str, Enum):
    EXTERNAL_OBSERVATION = "EXTERNAL_OBSERVATION"
    EXTERNAL_EXPECTATION = "EXTERNAL_EXPECTATION"


class RegistryEligibility(str, Enum):
    MVP_ELIGIBLE = "MVP_ELIGIBLE"
    MVP_ELIGIBLE_REFERENCE_ONLY = "MVP_ELIGIBLE_REFERENCE_ONLY"


class SeriesUse(str, Enum):
    EXTERNAL_REFERENCE = "EXTERNAL_REFERENCE"
    REFERENCE_ONLY = "REFERENCE_ONLY"


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class EconomicFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class AcquisitionHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
