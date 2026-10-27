import { describe, expect, it } from "vitest";

import type { PlanningGoalContext } from "@/lib/planning";

import { applyGoalContextPreset } from "./goalContext";
import { createPlanningInput } from "./planningForm";

const context: PlanningGoalContext = {
  goal_id: "abcdefab-1234-5678-90ab-abcdefabcdef",
  name: "Reserva de emergência",
  goal_type: "EMERGENCY_RESERVE",
  status: "ACTIVE",
  target_amount: "50000.00",
  current_amount: "12500.00",
  planned_monthly_contribution: "750.00",
  target_date: "2028-12-31",
};

describe("Goal Planning presets", () => {
  it("selects the Goal origin without copying its current amount into manual wealth", () => {
    const result = applyGoalContextPreset(
      { ...createPlanningInput(), initialWealth: "R$ 9.999,00" },
      context,
    );

    expect(result.source).toBe("GOAL_CURRENT_AMOUNT");
    expect(result.initialWealth).toBe("");
    expect(result.monthlyContribution).toBe("R$ 750,00");
    expect(JSON.stringify(result)).not.toContain("12500.00");
  });

  it("preserves explicit zero while keeping absence distinct", () => {
    const zero = applyGoalContextPreset(createPlanningInput(), {
      ...context,
      current_amount: "0.00",
      planned_monthly_contribution: "0",
    });
    const absent = applyGoalContextPreset(createPlanningInput(), {
      ...context,
      current_amount: null,
      planned_monthly_contribution: null,
    });

    expect(zero.source).toBe("GOAL_CURRENT_AMOUNT");
    expect(zero.monthlyContribution).toBe("R$ 0,00");
    expect(absent.source).toBe("USER_PROVIDED_SCENARIO");
    expect(absent.initialWealth).toBe("");
    expect(absent.monthlyContribution).toBe("");
  });

  it("does not derive a horizon or expected return from the Goal target date", () => {
    const input = {
      ...createPlanningInput(),
      expectedReturnRate: "8,5",
      horizonMonths: 36,
    };

    expect(applyGoalContextPreset(input, context)).toMatchObject({
      expectedReturnRate: "8,5",
      horizonMonths: 36,
    });
  });
});
