"""Strict public DTOs for the authenticated transient FIRE analysis API."""

from datetime import date
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from backend.application.dtos.planning_dto import (
    InitialWealthFactResponseDTO,
    InvestmentPortfolioSnapshotInitialWealthRequestDTO,
    RequiredContributionResponseDTO,
    StrictDecimalString,
    StrictISODate,
    TargetAchievementResponseDTO,
    UserProvidedInitialWealthRequestDTO,
)
from backend.application.services.fire_analysis_service import FireAnalysisType
from backend.domains.fire.summary import FireSummaryStatus
from backend.domains.planning.assumptions import OutputMode, ReturnType


class _FireRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


FireInitialWealthSelectorRequestDTO = Annotated[
    Union[
        InvestmentPortfolioSnapshotInitialWealthRequestDTO,
        UserProvidedInitialWealthRequestDTO,
    ],
    Field(discriminator="source"),
]


class _FireCommonRequestDTO(_FireRequestDTO):
    as_of_date: StrictISODate
    initial_wealth: FireInitialWealthSelectorRequestDTO
    monthly_retirement_spending: StrictDecimalString
    assumed_annual_withdrawal_rate: StrictDecimalString


class FireSummaryRequestDTO(_FireCommonRequestDTO):
    analysis_type: Literal[FireAnalysisType.SUMMARY]


class _FireProjectionRequestDTO(_FireCommonRequestDTO):
    expected_return_rate: StrictDecimalString
    return_type: ReturnType
    inflation_rate: StrictDecimalString | None = None

    @model_validator(mode="after")
    def _validate_return_inflation_matrix(self):
        if self.return_type is ReturnType.REAL and self.inflation_rate is not None:
            raise ValueError("inflation_rate is forbidden for REAL return")
        if self.return_type is ReturnType.NOMINAL and self.inflation_rate is None:
            raise ValueError("inflation_rate is required for NOMINAL return")
        return self


class FireProjectedDateRequestDTO(_FireProjectionRequestDTO):
    analysis_type: Literal[FireAnalysisType.PROJECTED_DATE]
    scenario_monthly_contribution: StrictDecimalString
    horizon_months: StrictInt


class FireRequiredContributionRequestDTO(_FireProjectionRequestDTO):
    analysis_type: Literal[FireAnalysisType.REQUIRED_CONTRIBUTION]
    desired_fire_date: StrictISODate


FireAnalysisRequestDTO = Annotated[
    Union[
        FireSummaryRequestDTO,
        FireProjectedDateRequestDTO,
        FireRequiredContributionRequestDTO,
    ],
    Field(discriminator="analysis_type"),
]


class FireSummaryResponseDTO(BaseModel):
    monthly_retirement_spending: str
    annual_required_spending: str
    assumed_annual_withdrawal_rate: str
    fire_target: str
    eligible_investment_wealth: str
    gap_to_fire: str
    progress_ratio: str
    supported_annual_withdrawal: str
    supported_monthly_withdrawal: str
    summary_status: FireSummaryStatus


class FireAssumptionsResponseDTO(BaseModel):
    monthly_retirement_spending: str
    assumed_annual_withdrawal_rate: str
    expected_return_rate: str | None
    return_type: ReturnType | None
    inflation_rate: str | None
    scenario_monthly_contribution: str | None
    horizon_months: int | None
    desired_fire_date: date | None


class FireProvenanceResponseDTO(BaseModel):
    initial_wealth_fact: InitialWealthFactResponseDTO


class FireAnalysisResponseDTO(BaseModel):
    analysis_type: FireAnalysisType
    as_of_date: date
    basis: Literal[OutputMode.REAL]
    summary: FireSummaryResponseDTO
    projection: TargetAchievementResponseDTO | None
    required_contribution: RequiredContributionResponseDTO | None
    assumptions: FireAssumptionsResponseDTO
    provenance: FireProvenanceResponseDTO
