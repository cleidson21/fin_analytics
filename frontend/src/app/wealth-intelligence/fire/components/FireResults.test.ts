import { describe, expect, it } from "vitest";

import type { FireAnalysisResponse } from "@/lib/fire";

import {
  beginFireSubmission,
  completeFireSubmission,
  createFireResultState,
  failFireSubmission,
  fireSummaryStatusCopy,
  formatFireProgressRatio,
  isFireResultDirty,
  projectedDateStatusCopy,
  requiredContributionStatusCopy,
  selectFireModeResult,
} from "./FireResults";

const initialWealthFact = {
  source: "INVESTMENT_PORTFOLIO_SNAPSHOT" as const,
  amount: "800000.00",
  scope: "INVESTMENT_PORTFOLIO" as const,
  as_of: { reference_month: "2026-09", observed_at: null },
  provenance: { source_type: "MYPROFIT", goal_id: null, account_id: null, reference_month: "2026-09", run_id: null, created_at: null, updated_at: null },
};

function response(analysis_type: FireAnalysisResponse["analysis_type"] = "SUMMARY"): FireAnalysisResponse {
  return {
    analysis_type,
    as_of_date: "2026-09-30",
    basis: "REAL",
    summary: {
      monthly_retirement_spending: "5000.00",
      annual_required_spending: "60000.00",
      assumed_annual_withdrawal_rate: "0.04",
      fire_target: "1500000.00",
      eligible_investment_wealth: "800000.00",
      gap_to_fire: "700000.00",
      progress_ratio: "0.53333333",
      supported_annual_withdrawal: "32000.00",
      supported_monthly_withdrawal: "2666.67",
      summary_status: "BELOW_FIRE_TARGET",
    },
    projection: analysis_type === "PROJECTED_DATE" ? {
      status: "ACHIEVED",
      target_amount: "1500000.00",
      initial_wealth_fact: initialWealthFact,
      assumptions: { as_of_date: "2026-09-30", scenario_monthly_contribution: "1000.00", expected_return_rate: "0.05", return_type: "REAL", output_mode: "REAL", inflation_rate: null, horizon_months: 120, target_date: null, rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" },
      achievement_period: 96,
      achievement_date: "2034-09-30",
      months_required: 96,
      achieved_wealth: "1500000.01",
      projection_result: null,
      target_value_basis: "REAL",
    } : null,
    required_contribution: analysis_type === "REQUIRED_CONTRIBUTION" ? {
      status: "SOLVED",
      target_amount: "1500000.00",
      target_value_basis: "REAL",
      initial_wealth_fact: initialWealthFact,
      assumptions_template: { as_of_date: "2026-09-30", scenario_monthly_contribution: "0.00", expected_return_rate: "0.05", return_type: "REAL", output_mode: "REAL", inflation_rate: null, horizon_months: null, target_date: "2034-09-30", rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" },
      required_monthly_contribution: "1234.56",
      solved_assumptions: { as_of_date: "2026-09-30", scenario_monthly_contribution: "1234.56", expected_return_rate: "0.05", return_type: "REAL", output_mode: "REAL", inflation_rate: null, horizon_months: null, target_date: "2034-09-30", rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" },
      target_achievement_result: { status: "ACHIEVED", target_amount: "1500000.00", initial_wealth_fact: initialWealthFact, assumptions: { as_of_date: "2026-09-30", scenario_monthly_contribution: "1234.56", expected_return_rate: "0.05", return_type: "REAL", output_mode: "REAL", inflation_rate: null, horizon_months: 96, target_date: null, rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" }, achievement_period: 96, achievement_date: "2034-09-30", months_required: 96, achieved_wealth: "1500000.01", projection_result: null },
    } : null,
    assumptions: { monthly_retirement_spending: "5000.00", assumed_annual_withdrawal_rate: "0.04", expected_return_rate: analysis_type === "SUMMARY" ? null : "0.05", return_type: analysis_type === "SUMMARY" ? null : "REAL", inflation_rate: null, scenario_monthly_contribution: analysis_type === "PROJECTED_DATE" ? "1000.00" : null, horizon_months: analysis_type === "PROJECTED_DATE" ? 120 : null, desired_fire_date: analysis_type === "REQUIRED_CONTRIBUTION" ? "2034-09-30" : null },
    provenance: { initial_wealth_fact: initialWealthFact },
  };
}

describe("FIRE result presentation helpers", () => {
  it("formats API money and unbounded progress without JavaScript number conversion", async () => {
    const { formatBRLDecimalString } = await import("@/lib/planningLocale");
    expect(formatBRLDecimalString("1500000.00")).toBe("R$ 1.500.000,00");
    expect(formatFireProgressRatio("0.00000000")).toBe("0,00%");
    expect(formatFireProgressRatio("0.73500000")).toBe("73,50%");
    expect(formatFireProgressRatio("1.00000000")).toBe("100,00%");
    expect(formatFireProgressRatio("1.20000000")).toBe("120,00%");
  });

  it("uses factual, non-guarantee status wording", () => {
    expect(fireSummaryStatusCopy("ALREADY_FINANCIALLY_INDEPENDENT")).toBe("Meta alcançada pelas premissas informadas");
    expect(fireSummaryStatusCopy("BELOW_FIRE_TARGET")).toBe("Em construção");
    expect(projectedDateStatusCopy("NOT_REACHED_WITHIN_HORIZON")).toBe("Meta não alcançada dentro do horizonte analisado.");
    expect(requiredContributionStatusCopy("ZERO_CONTRIBUTION_REQUIRED")).toBe("Nenhum aporte adicional é necessário pelas premissas informadas.");
    expect(`${fireSummaryStatusCopy("ALREADY_FINANCIALLY_INDEPENDENT")} ${projectedDateStatusCopy("UNREACHABLE")}`).not.toMatch(/garant|segur|aposentar/i);
  });

  it("selects only the server-provided section for each analysis mode", () => {
    expect(selectFireModeResult(response("SUMMARY")).kind).toBe("SUMMARY");
    expect(selectFireModeResult(response("PROJECTED_DATE")).kind).toBe("PROJECTED_DATE");
    expect(selectFireModeResult(response("REQUIRED_CONTRIBUTION")).kind).toBe("REQUIRED_CONTRIBUTION");
  });
});

describe("FIRE result state", () => {
  it("distinguishes first-submit loading from a prior result", () => {
    const pending = beginFireSubmission(createFireResultState());
    expect(pending.pending).toBe(true);
    expect(pending.result).toBeNull();
  });

  it("preserves a result and marks it dirty when the form changes", () => {
    const completed = completeFireSubmission(createFireResultState(), response(), "submitted");
    expect(completed.result).not.toBeNull();
    expect(isFireResultDirty(completed, "changed")).toBe(true);
  });

  it("replaces the prior result and clears dirty/error after a successful recalculation", () => {
    const prior = { ...completeFireSubmission(createFireResultState(), response(), "old"), error: "Falha anterior" };
    const recalculated = completeFireSubmission(prior, response("PROJECTED_DATE"), "new");
    expect(recalculated.result?.analysis_type).toBe("PROJECTED_DATE");
    expect(recalculated.error).toBeNull();
    expect(isFireResultDirty(recalculated, "new")).toBe(false);
  });

  it("preserves the last result when recalculation fails", () => {
    const prior = completeFireSubmission(createFireResultState(), response(), "submitted");
    const failed = failFireSubmission(beginFireSubmission(prior), "Serviço indisponível");
    expect(failed.result).toBe(prior.result);
    expect(failed.error).toBe("Serviço indisponível");
    expect(failed.pending).toBe(false);
  });
});
