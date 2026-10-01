"""Pure mapping between FIRE HTTP DTOs and D2 application objects."""

from backend.api.planning_mapping import (
    map_initial_wealth_fact,
    map_required_contribution_result,
    map_target_achievement_response,
    serialize_decimal,
)
from backend.application.dtos.fire_dto import (
    FireAnalysisRequestDTO,
    FireAnalysisResponseDTO,
    FireAssumptionsResponseDTO,
    FireProjectedDateRequestDTO,
    FireProvenanceResponseDTO,
    FireRequiredContributionRequestDTO,
    FireSummaryRequestDTO,
    FireSummaryResponseDTO,
)
from backend.application.dtos.planning_dto import (
    InvestmentPortfolioSnapshotInitialWealthRequestDTO,
    UserProvidedInitialWealthRequestDTO,
)
from backend.application.services.fire_analysis_service import (
    FireAnalysisAssumptions,
    FireAnalysisCommand,
    FireAnalysisResult,
    FireProjectedDateCommand,
    FireRequiredContributionCommand,
    FireSummaryCommand,
    PortfolioInitialWealthSelection,
    UserProvidedInitialWealthSelection,
)
from backend.domains.planning.assumptions import OutputMode


def _map_initial_wealth_selection(request):
    if isinstance(request, InvestmentPortfolioSnapshotInitialWealthRequestDTO):
        return PortfolioInitialWealthSelection()
    if isinstance(request, UserProvidedInitialWealthRequestDTO):
        return UserProvidedInitialWealthSelection(
            amount=request.amount,
            observed_at=request.observed_at,
        )
    raise TypeError("unsupported FIRE initial wealth source")


def map_fire_analysis_request(request: FireAnalysisRequestDTO) -> FireAnalysisCommand:
    """Map structurally valid HTTP input without resolving wealth or calculating."""

    common = {
        "initial_wealth": _map_initial_wealth_selection(request.initial_wealth),
        "as_of_date": request.as_of_date,
        "monthly_retirement_spending": request.monthly_retirement_spending,
        "assumed_annual_withdrawal_rate": request.assumed_annual_withdrawal_rate,
    }
    if isinstance(request, FireSummaryRequestDTO):
        return FireSummaryCommand(**common)
    if isinstance(request, FireProjectedDateRequestDTO):
        return FireProjectedDateCommand(
            **common,
            scenario_monthly_contribution=request.scenario_monthly_contribution,
            expected_return_rate=request.expected_return_rate,
            return_type=request.return_type,
            inflation_rate=request.inflation_rate,
            horizon_months=request.horizon_months,
        )
    if isinstance(request, FireRequiredContributionRequestDTO):
        return FireRequiredContributionCommand(
            **common,
            expected_return_rate=request.expected_return_rate,
            return_type=request.return_type,
            inflation_rate=request.inflation_rate,
            desired_fire_date=request.desired_fire_date,
        )
    raise TypeError("unsupported FIRE analysis type")


def _map_summary(result: FireAnalysisResult) -> FireSummaryResponseDTO:
    summary = result.summary
    return FireSummaryResponseDTO(
        monthly_retirement_spending=serialize_decimal(
            summary.monthly_retirement_spending
        ),
        annual_required_spending=serialize_decimal(summary.annual_required_spending),
        assumed_annual_withdrawal_rate=serialize_decimal(
            summary.assumed_annual_withdrawal_rate
        ),
        fire_target=serialize_decimal(summary.fire_target),
        eligible_investment_wealth=serialize_decimal(
            summary.eligible_investment_wealth
        ),
        gap_to_fire=serialize_decimal(summary.gap_to_fire),
        progress_ratio=serialize_decimal(summary.progress_ratio),
        supported_annual_withdrawal=serialize_decimal(
            summary.supported_annual_withdrawal
        ),
        supported_monthly_withdrawal=serialize_decimal(
            summary.supported_monthly_withdrawal
        ),
        summary_status=summary.status,
    )


def _map_assumptions(
    assumptions: FireAnalysisAssumptions,
) -> FireAssumptionsResponseDTO:
    return FireAssumptionsResponseDTO(
        monthly_retirement_spending=serialize_decimal(
            assumptions.monthly_retirement_spending
        ),
        assumed_annual_withdrawal_rate=serialize_decimal(
            assumptions.assumed_annual_withdrawal_rate
        ),
        expected_return_rate=(
            None
            if assumptions.expected_return_rate is None
            else serialize_decimal(assumptions.expected_return_rate)
        ),
        return_type=assumptions.return_type,
        inflation_rate=(
            None
            if assumptions.inflation_rate is None
            else serialize_decimal(assumptions.inflation_rate)
        ),
        scenario_monthly_contribution=(
            None
            if assumptions.scenario_monthly_contribution is None
            else serialize_decimal(assumptions.scenario_monthly_contribution)
        ),
        horizon_months=assumptions.horizon_months,
        desired_fire_date=assumptions.desired_fire_date,
    )


def map_fire_analysis_result(result: FireAnalysisResult) -> FireAnalysisResponseDTO:
    """Serialize certified D1/D2 and Planning facts without financial recalculation."""

    return FireAnalysisResponseDTO(
        analysis_type=result.analysis_type,
        as_of_date=result.as_of_date,
        basis=OutputMode.REAL,
        summary=_map_summary(result),
        projection=(
            None
            if result.projection is None
            else map_target_achievement_response(
                result.projection,
                result.target_value_basis,
            )
        ),
        required_contribution=(
            None
            if result.required_contribution is None
            else map_required_contribution_result(
                result.required_contribution,
                result.target_value_basis,
            )
        ),
        assumptions=_map_assumptions(result.assumptions),
        provenance=FireProvenanceResponseDTO(
            initial_wealth_fact=map_initial_wealth_fact(result.initial_wealth_fact)
        ),
    )
