"""Neutral target-value basis contract shared by Planning consumers."""

from enum import Enum


class TargetValueBasis(str, Enum):
    """Explicit purchasing-power basis of a Planning target amount."""

    NOMINAL = "NOMINAL"
    REAL = "REAL"
