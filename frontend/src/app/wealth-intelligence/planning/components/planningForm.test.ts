import { describe, expect, it } from "vitest";

import {
  createPlanningInput,
  toInitialWealthSelector,
  toProjectionAssumptions,
} from "./planningForm";

function localSubmittedAt() {
  const value = new Date(0);
  value.setFullYear(2026, 8, 26);
  value.setHours(14, 30, 0, 0);
  return value;
}

describe("Planning form request adapters", () => {
  it("injects local submit-date context and converts human money and percentage inputs", () => {
    const input = {
      ...createPlanningInput(),
      initialWealth: "R$ 1.000,50",
      monthlyContribution: "R$ 250,00",
      expectedReturnRate: "8,5",
      horizonMonths: 24,
    };

    expect(toProjectionAssumptions(input, localSubmittedAt())).toMatchObject({
      as_of_date: "2026-09-26",
      scenario_monthly_contribution: "250.00",
      expected_return_rate: "0.085",
      return_type: "NOMINAL",
      output_mode: "NOMINAL",
      inflation_rate: null,
      horizon_months: 24,
    });
    expect(toInitialWealthSelector(input, localSubmittedAt())).toEqual({
      source: "USER_PROVIDED_SCENARIO",
      amount: "1000.50",
      observed_at: localSubmittedAt().toISOString(),
    });
  });

  it("honors explicit historical context without altering the financial payload", () => {
    const input = {
      ...createPlanningInput(),
      initialWealth: "1.000,00",
      monthlyContribution: "200",
      expectedReturnRate: "0,08",
      asOfDate: "15/08/2026",
      observedAt: "2026-08-14T10:15",
      horizonMonths: 12,
    };

    expect(toProjectionAssumptions(input, localSubmittedAt())).toMatchObject({
      as_of_date: "2026-08-15",
      expected_return_rate: "0.0008",
    });
    expect(toInitialWealthSelector(input, localSubmittedAt())).toEqual({
      source: "USER_PROVIDED_SCENARIO",
      amount: "1000.00",
      observed_at: new Date("2026-08-14T10:15").toISOString(),
    });
  });

  it("builds a source-only portfolio selector even when manual state remains populated", () => {
    const input = {
      ...createPlanningInput(),
      source: "INVESTMENT_PORTFOLIO_SNAPSHOT" as const,
      initialWealth: "999.999,99",
      observedAt: "2026-08-14T10:15",
    };

    expect(toInitialWealthSelector(input, localSubmittedAt())).toEqual({
      source: "INVESTMENT_PORTFOLIO_SNAPSHOT",
    });
  });
});
