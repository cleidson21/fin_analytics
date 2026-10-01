import { fetchFromAPI } from "@/lib/api";
import type {
  DecimalString,
  InitialWealthFact,
  ISODateString,
  ISODatetimeString,
  RequiredContributionResponse,
  ReturnType,
  TargetAchievementResponse,
} from "@/lib/planning";

export type FireAnalysisType = "SUMMARY" | "PROJECTED_DATE" | "REQUIRED_CONTRIBUTION";
export type FireSummaryStatus = "ALREADY_FINANCIALLY_INDEPENDENT" | "BELOW_FIRE_TARGET";

export type FireInitialWealthSelector =
  | { source: "INVESTMENT_PORTFOLIO_SNAPSHOT" }
  | { source: "USER_PROVIDED_SCENARIO"; amount: DecimalString; observed_at: ISODatetimeString };

type FireCommonRequest = {
  as_of_date: ISODateString;
  initial_wealth: FireInitialWealthSelector;
  monthly_retirement_spending: DecimalString;
  assumed_annual_withdrawal_rate: DecimalString;
};

export type FireAnalysisRequest =
  | (FireCommonRequest & { analysis_type: "SUMMARY" })
  | (FireCommonRequest & {
      analysis_type: "PROJECTED_DATE";
      scenario_monthly_contribution: DecimalString;
      expected_return_rate: DecimalString;
      return_type: ReturnType;
      inflation_rate?: DecimalString;
      horizon_months: number;
    })
  | (FireCommonRequest & {
      analysis_type: "REQUIRED_CONTRIBUTION";
      expected_return_rate: DecimalString;
      return_type: ReturnType;
      inflation_rate?: DecimalString;
      desired_fire_date: ISODateString;
    });

export interface FireSummaryResponse {
  monthly_retirement_spending: DecimalString;
  annual_required_spending: DecimalString;
  assumed_annual_withdrawal_rate: DecimalString;
  fire_target: DecimalString;
  eligible_investment_wealth: DecimalString;
  gap_to_fire: DecimalString;
  progress_ratio: DecimalString;
  supported_annual_withdrawal: DecimalString;
  supported_monthly_withdrawal: DecimalString;
  summary_status: FireSummaryStatus;
}

export interface FireAssumptions {
  monthly_retirement_spending: DecimalString;
  assumed_annual_withdrawal_rate: DecimalString;
  expected_return_rate: DecimalString | null;
  return_type: ReturnType | null;
  inflation_rate: DecimalString | null;
  scenario_monthly_contribution: DecimalString | null;
  horizon_months: number | null;
  desired_fire_date: ISODateString | null;
}

export interface FireAnalysisResponse {
  analysis_type: FireAnalysisType;
  as_of_date: ISODateString;
  basis: "REAL";
  summary: FireSummaryResponse;
  projection: TargetAchievementResponse | null;
  required_contribution: RequiredContributionResponse | null;
  assumptions: FireAssumptions;
  provenance: { initial_wealth_fact: InitialWealthFact };
}

export function analyzeFire(request: FireAnalysisRequest) {
  return fetchFromAPI<FireAnalysisResponse>("/fire/analysis", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
