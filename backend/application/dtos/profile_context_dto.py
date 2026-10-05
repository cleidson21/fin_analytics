from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from backend.application.dtos.planning_dto import (
    StrictDecimalString,
    StrictISODate,
)
from backend.domains.smart_context import IncomeBasis, IncomeCurrency, IncomePeriod


class ProfileDeclaredContextPatchDTO(BaseModel):
    """Strict public mutation for the one approved declared financial fact."""

    model_config = ConfigDict(extra="forbid")

    declared_monthly_gross_income: StrictDecimalString | None
    income_as_of_date: StrictISODate | None = None

    @model_validator(mode="after")
    def _validate_declared_income(self):
        amount = self.declared_monthly_gross_income
        if amount is None:
            if self.income_as_of_date is not None:
                raise ValueError("A cleared declaration cannot retain an as-of date.")
            return self
        if amount <= 0:
            raise ValueError("Declared monthly gross income must be positive.")
        if amount.as_tuple().exponent < -2:
            raise ValueError("Declared monthly gross income must use cent scale.")
        return self


class ProfileDeclaredContextResponseDTO(BaseModel):
    """Purpose-limited Profile response without internal ownership identifiers."""

    name: str
    email: str
    declared_monthly_gross_income: str | None
    semantic_type: Literal["DECLARED"]
    source: Literal["USER_PROFILE"]
    currency: IncomeCurrency | None
    income_period: IncomePeriod | None
    income_basis: IncomeBasis | None
    income_as_of_date: date | None
    declared_at: datetime | None
    updated_at: datetime | None
