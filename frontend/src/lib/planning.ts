import { fetchFromAPI } from "@/lib/api";

/** Planning API contracts. Financial values remain exact JSON decimal strings. */
export type DecimalString = string;
export type ISODateString = string;
export type ISODatetimeString = string;

/** The authenticated Planning API exposes only certified initial-wealth origins. */
export type InitialWealthSource =
  | "USER_PROVIDED_SCENARIO"
  | "GOAL_CURRENT_AMOUNT"
  | "INVESTMENT_PORTFOLIO_SNAPSHOT";
export type InitialWealthScope =
  | "USER_PROVIDED_SCENARIO"
  | "GOAL"
  | "INVESTMENT_PORTFOLIO";
export type RateBasis = "EFFECTIVE_ANNUAL";
export type ReturnType = "NOMINAL" | "REAL";
export type OutputMode = "NOMINAL" | "REAL";
export type ContributionTiming = "END_OF_MONTH";
export type TargetValueBasis = "NOMINAL" | "REAL";
export type ScenarioArchetype = "CONSERVATIVE" | "BASE" | "OPTIMISTIC";
export type TargetAchievementStatus =
  | "ALREADY_ACHIEVED"
  | "ACHIEVED"
  | "UNREACHABLE"
  | "NOT_REACHED_WITHIN_HORIZON";
export type RequiredContributionStatus =
  | "ALREADY_ACHIEVED"
  | "ZERO_CONTRIBUTION_REQUIRED"
  | "SOLVED"
  | "IMPOSSIBLE_HORIZON"
  | "OUT_OF_SUPPORTED_RANGE";
export type GoalPlanningStatus =
  | "PROJECTED_EARLY"
  | "PROJECTED_ON_TIME"
  | "PROJECTED_LATE"
  | "ALREADY_ACHIEVED"
  | "NOT_REACHED_WITHIN_HORIZON"
  | "INSUFFICIENT_DATA"
  | "NOT_APPLICABLE";
export type GoalStatus = "ACTIVE" | "ACHIEVED" | "PAUSED" | "CANCELLED";
export type GoalType =
  | "EMERGENCY_RESERVE"
  | "RETIREMENT"
  | "TRAVEL"
  | "PURCHASE"
  | "CUSTOM"
  | "WEALTH_TARGET"
  | "INVESTMENT_TARGET"
  | "DIVIDEND_INCOME"
  | "FINANCIAL_INDEPENDENCE";

export interface PlanningFactAsOf {
  reference_month: string | null;
  observed_at: ISODatetimeString | null;
}

export interface PlanningFactProvenance {
  source_type: string | null;
  goal_id: string | null;
  account_id: string | null;
  reference_month: string | null;
  run_id: string | null;
  created_at: ISODatetimeString | null;
  updated_at: ISODatetimeString | null;
}

export interface InitialWealthFact {
  source: InitialWealthSource;
  amount: DecimalString;
  scope: InitialWealthScope;
  as_of: PlanningFactAsOf;
  provenance: PlanningFactProvenance;
}

export interface UserProvidedInitialWealthSelector {
  source: "USER_PROVIDED_SCENARIO";
  amount: DecimalString;
  observed_at: ISODatetimeString;
}

export interface GoalCurrentAmountInitialWealthSelector {
  source: "GOAL_CURRENT_AMOUNT";
  goal_id: string;
}

/** The backend resolves the authenticated MyProfit portfolio; clients supply no facts. */
export interface InvestmentPortfolioSnapshotInitialWealthSelector {
  source: "INVESTMENT_PORTFOLIO_SNAPSHOT";
}

export type InitialWealthSelector =
  | UserProvidedInitialWealthSelector
  | GoalCurrentAmountInitialWealthSelector
  | InvestmentPortfolioSnapshotInitialWealthSelector;

export interface GoalPathCurrentAmountInitialWealthSelector {
  source: "GOAL_CURRENT_AMOUNT";
}

export type GoalPlanningInitialWealthSelector =
  | UserProvidedInitialWealthSelector
  | GoalPathCurrentAmountInitialWealthSelector
  | InvestmentPortfolioSnapshotInitialWealthSelector;

export interface ProjectionAssumptions {
  as_of_date: ISODateString;
  scenario_monthly_contribution: DecimalString;
  expected_return_rate: DecimalString;
  return_type: ReturnType;
  output_mode: OutputMode;
  inflation_rate: DecimalString | null;
  horizon_months: number | null;
  target_date: ISODateString | null;
  rate_basis: RateBasis;
  contribution_timing: ContributionTiming;
}

export interface ProjectionPeriod {
  period: number;
  period_end: ISODateString;
  opening_wealth: DecimalString;
  contribution: DecimalString;
  projected_return: DecimalString;
  ending_wealth: DecimalString;
  cumulative_contributions: DecimalString;
  cumulative_projected_growth: DecimalString;
}

export interface ForwardProjectionResponse {
  initial_wealth_fact: InitialWealthFact;
  assumptions: ProjectionAssumptions;
  effective_projection_annual_rate: DecimalString;
  monthly_equivalent_rate: DecimalString;
  periods: ProjectionPeriod[];
  initial_wealth: DecimalString;
  final_wealth: DecimalString;
  total_contributions: DecimalString;
  total_projected_growth: DecimalString;
  as_of_date: ISODateString;
  horizon_months: number;
}

export interface ProjectionRequest {
  initial_wealth: InitialWealthSelector;
  assumptions: ProjectionAssumptions;
}

export interface TargetAchievementResult {
  status: TargetAchievementStatus;
  target_amount: DecimalString;
  initial_wealth_fact: InitialWealthFact;
  assumptions: ProjectionAssumptions;
  achievement_period: number | null;
  achievement_date: ISODateString | null;
  months_required: number | null;
  achieved_wealth: DecimalString | null;
  projection_result: ForwardProjectionResponse | null;
}

export interface TargetAchievementRequest extends ProjectionRequest {
  target_amount: DecimalString;
  target_value_basis: TargetValueBasis;
}

export interface TargetAchievementResponse extends TargetAchievementResult {
  target_value_basis: TargetValueBasis;
}

export interface RequiredContributionRequest extends ProjectionRequest {
  target_amount: DecimalString;
  target_value_basis: TargetValueBasis;
}

export interface RequiredContributionResponse {
  status: RequiredContributionStatus;
  target_amount: DecimalString;
  target_value_basis: TargetValueBasis;
  initial_wealth_fact: InitialWealthFact;
  assumptions_template: ProjectionAssumptions;
  required_monthly_contribution: DecimalString;
  solved_assumptions: ProjectionAssumptions;
  target_achievement_result: TargetAchievementResult;
}

export interface GoalPlanningFact {
  goal_id: string;
  name: string;
  description: string | null;
  goal_type: GoalType;
  status: GoalStatus;
  target_amount: DecimalString;
  target_date: ISODateString | null;
  current_amount: DecimalString | null;
  goal_planned_monthly_contribution: DecimalString | null;
  priority: number | null;
  linked_account_id: string | null;
  created_at: ISODatetimeString;
  updated_at: ISODatetimeString;
}

export interface GoalPlanningRequest {
  initial_wealth: GoalPlanningInitialWealthSelector;
  assumptions: ProjectionAssumptions;
  target_value_basis: TargetValueBasis | null;
}

export interface GoalPlanningResponse {
  status: GoalPlanningStatus;
  goal_fact: GoalPlanningFact;
  initial_wealth_fact: InitialWealthFact | null;
  assumptions: ProjectionAssumptions;
  target_value_basis: TargetValueBasis | null;
  target_achievement_result: TargetAchievementResult | null;
}

export interface ScenarioDefinitionRequest {
  scenario_id: string;
  initial_wealth: InitialWealthSelector;
  assumptions: ProjectionAssumptions;
  label: string | null;
  archetype: ScenarioArchetype | null;
}

export interface ScenarioComparisonRequest {
  scenarios: ScenarioDefinitionRequest[];
  reference_scenario_id: string;
  target_amount: DecimalString | null;
  target_value_basis: TargetValueBasis | null;
}

export interface ScenarioComparisonEntry {
  scenario_id: string;
  label: string | null;
  archetype: ScenarioArchetype | null;
  initial_wealth_fact: InitialWealthFact;
  assumptions: ProjectionAssumptions;
  projection_result: ForwardProjectionResponse;
  target_achievement_result: TargetAchievementResult | null;
  final_wealth_delta: DecimalString;
  total_contributions_delta: DecimalString;
  total_projected_growth_delta: DecimalString;
  months_saved_or_lost: number | null;
}

export interface ScenarioComparisonResponse {
  reference_scenario_id: string;
  entries: ScenarioComparisonEntry[];
  as_of_date: ISODateString;
  horizon_months: number;
  output_mode: OutputMode;
  contribution_timing: ContributionTiming;
  target_amount: DecimalString | null;
  target_value_basis: TargetValueBasis | null;
}

function postPlanning<T>(path: string, payload: unknown): Promise<T | null> {
  return fetchFromAPI<T>(path, { method: "POST", body: JSON.stringify(payload) });
}

export function projectPlanning(request: ProjectionRequest) {
  return postPlanning<ForwardProjectionResponse>("/planning/projection", request);
}

export function solveTargetAchievement(request: TargetAchievementRequest) {
  return postPlanning<TargetAchievementResponse>("/planning/target-achievement", request);
}

export function solveRequiredContribution(request: RequiredContributionRequest) {
  return postPlanning<RequiredContributionResponse>("/planning/required-contribution", request);
}

export function projectGoal(goalId: string, request: GoalPlanningRequest) {
  return postPlanning<GoalPlanningResponse>(`/planning/goals/${goalId}/projection`, request);
}

export function comparePlanningScenarios(request: ScenarioComparisonRequest) {
  return postPlanning<ScenarioComparisonResponse>("/planning/scenarios/compare", request);
}
