import { describe, expect, it } from "vitest";
import { createGoalBudgetForm, GoalBudgetInputError, toGoalBudgetRequest, type GoalBudgetFormState } from "./goalBudgetForm";

const id = "00000000-0000-0000-0000-000000000001";
const valid: GoalBudgetFormState = {
  monthlyBudget: "1.500,01", horizonMonths: "120", expectedReturnRate: "5,125",
  asOfDate: "28/10/2026", allocations: [{ goalId: id, A: "800,10", B: "800,10" }],
};

describe("Goal budget lexical form adapter", () => {
  it("starts with no financial or horizon defaults", () => {
    expect(createGoalBudgetForm()).toEqual({ monthlyBudget: "", horizonMonths: "", expectedReturnRate: "", asOfDate: "", allocations: [] });
  });

  it("matches the exact nominal API request without per-scenario premises", () => {
    expect(toGoalBudgetRequest(valid)).toEqual({
      goal_ids: [id], monthly_budget: "1500.01", target_value_basis: "NOMINAL",
      assumptions: { as_of_date: "2026-10-28", expected_return_rate: "0.05125", return_type: "NOMINAL", output_mode: "NOMINAL", horizon_months: 120, rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" },
      scenarios: ["A", "B"].map((scenario_id) => ({ scenario_id, allocations: [{ goal_id: id, scenario_monthly_contribution: "800.10" }] })),
    });
  });

  it("preserves zero and large money digits as strings", () => {
    const request = toGoalBudgetRequest({ ...valid, monthlyBudget: "90071992547409931234567890,01", expectedReturnRate: "0", allocations: [{ goalId: id, A: "0", B: "0,00" }] });
    expect(request.monthly_budget).toBe("90071992547409931234567890.01");
    expect(request.assumptions.expected_return_rate).toBe("0");
    expect(request.scenarios[0].allocations[0].scenario_monthly_contribution).toBe("0.00");
  });

  it("leaves unequal totals and negative financial-domain validation to the backend", () => {
    const request = toGoalBudgetRequest({ ...valid, monthlyBudget: "-1", allocations: [{ goalId: id, A: "100", B: "200" }] });
    expect(request.monthly_budget).toBe("-1.00");
    expect(request.scenarios[1].allocations[0].scenario_monthly_contribution).toBe("200.00");
  });

  it("uses the local submit date without deriving a horizon from Goal dates", () => {
    const request = toGoalBudgetRequest({ ...valid, asOfDate: "" }, new Date(2026, 9, 29, 12));
    expect(request.assumptions.as_of_date).toBe("2026-10-29");
    expect(request.assumptions.horizon_months).toBe(120);
  });

  it.each([
    ["monthlyBudget", ""], ["monthlyBudget", "1,001"], ["expectedReturnRate", ""],
    ["expectedReturnRate", "1e2"], ["asOfDate", "31/02/2026"],
    ["horizonMonths", ""], ["horizonMonths", "0"], ["horizonMonths", "1201"], ["horizonMonths", "1.5"],
  ])("rejects missing or invalid %s input", (field, value) => {
    expect(() => toGoalBudgetRequest({ ...valid, [field]: value })).toThrow(GoalBudgetInputError);
  });

  it("rejects omitted allocations rather than converting them to zero", () => {
    expect(() => toGoalBudgetRequest({ ...valid, allocations: [{ goalId: id, A: "", B: "0" }] })).toThrow(GoalBudgetInputError);
    expect(() => toGoalBudgetRequest({ ...valid, allocations: [] })).toThrow(GoalBudgetInputError);
  });
});
