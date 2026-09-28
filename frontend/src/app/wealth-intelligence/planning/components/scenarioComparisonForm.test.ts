import { describe, expect, it } from "vitest";

import { createPlanningInput } from "./planningForm";
import {
  buildScenarioComparisonRequest,
  createScenarioComparisonSharedContext,
  referenceAfterScenarioRemoval,
  type ScenarioComparisonDraftInput,
} from "./scenarioComparisonForm";

function submittedAt() {
  const value = new Date(0);
  value.setFullYear(2026, 8, 26);
  value.setHours(14, 30, 0, 0);
  return value;
}

function manualScenario(
  scenarioId: string,
  monthlyContribution: string,
  expectedReturnRate: string,
): ScenarioComparisonDraftInput {
  return {
    scenarioId,
    label: "",
    archetype: "",
    input: {
      ...createPlanningInput(),
      initialWealth: "R$ 1.000,00",
      monthlyContribution,
      expectedReturnRate,
    },
  };
}

describe("Scenario Comparison shared context builder", () => {
  it("expands one shared horizon, as-of date, output mode, and target pair in request order", () => {
    const shared = {
      ...createScenarioComparisonSharedContext(),
      asOfDate: "15/08/2026",
      horizonMonths: 24,
      outputMode: "REAL" as const,
      includeTarget: true,
      targetAmount: "R$ 10.000,00",
    };
    const scenarios = [
      manualScenario("scenario-a", "100", "8"),
      manualScenario("scenario-b", "200", "9"),
      manualScenario("scenario-c", "300", "10"),
    ];
    scenarios.forEach((scenario) => {
      scenario.input = { ...scenario.input, inflationRate: "4" };
    });
    const request = buildScenarioComparisonRequest(scenarios, shared, "scenario-b", submittedAt());

    expect(request.scenarios.map((scenario) => scenario.scenario_id)).toEqual(["scenario-a", "scenario-b", "scenario-c"]);
    expect(request.scenarios.map((scenario) => scenario.assumptions.as_of_date)).toEqual(["2026-08-15", "2026-08-15", "2026-08-15"]);
    expect(request.scenarios.map((scenario) => scenario.assumptions.horizon_months)).toEqual([24, 24, 24]);
    expect(request.scenarios.map((scenario) => scenario.assumptions.output_mode)).toEqual(["REAL", "REAL", "REAL"]);
    expect(request.scenarios.map((scenario) => scenario.assumptions.scenario_monthly_contribution)).toEqual(["100.00", "200.00", "300.00"]);
    expect(request.scenarios.map((scenario) => scenario.assumptions.expected_return_rate)).toEqual(["0.08", "0.09", "0.1"]);
    expect(request.reference_scenario_id).toBe("scenario-b");
    expect(request.target_amount).toBe("10000.00");
    expect(request.target_value_basis).toBe("REAL");
  });

  it("preserves mixed sources and never leaks stale manual fields into a portfolio selector", () => {
    const portfolio = manualScenario("portfolio", "100", "8");
    portfolio.input = {
      ...portfolio.input,
      source: "INVESTMENT_PORTFOLIO_SNAPSHOT",
      initialWealth: "R$ 999.999,99",
      observedAt: "2026-08-14T10:15",
    };
    const goal = manualScenario("goal", "150", "7");
    goal.input = {
      ...goal.input,
      source: "GOAL_CURRENT_AMOUNT",
      goalId: "owned-goal-id",
    };

    const request = buildScenarioComparisonRequest([
      manualScenario("manual", "50", "6"),
      portfolio,
      goal,
    ], {
      ...createScenarioComparisonSharedContext(),
      horizonMonths: 12,
    }, "manual", submittedAt());

    expect(request.scenarios[0]?.initial_wealth).toMatchObject({ source: "USER_PROVIDED_SCENARIO", amount: "1000.00" });
    expect(request.scenarios[1]?.initial_wealth).toEqual({ source: "INVESTMENT_PORTFOLIO_SNAPSHOT" });
    expect(request.scenarios[2]?.initial_wealth).toEqual({ source: "GOAL_CURRENT_AMOUNT", goal_id: "owned-goal-id" });
  });

  it("keeps return type and inflation scenario-specific under a shared real output", () => {
    const nominal = manualScenario("nominal", "100", "8");
    nominal.input = { ...nominal.input, inflationRate: "4" };
    const real = manualScenario("real", "100", "3");
    real.input = { ...real.input, returnType: "REAL" };

    const request = buildScenarioComparisonRequest([nominal, real], {
      ...createScenarioComparisonSharedContext(),
      horizonMonths: 12,
      outputMode: "REAL",
    }, "nominal", submittedAt());

    expect(request.scenarios[0]?.assumptions).toMatchObject({ return_type: "NOMINAL", inflation_rate: "0.04" });
    expect(request.scenarios[1]?.assumptions).toMatchObject({ return_type: "REAL", inflation_rate: null });
  });

  it("requires a fresh explicit reference after its selected scenario is removed", () => {
    expect(referenceAfterScenarioRemoval("scenario-a", "scenario-b")).toBe("scenario-a");
    expect(referenceAfterScenarioRemoval("scenario-a", "scenario-a")).toBe("");
  });
});
