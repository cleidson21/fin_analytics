import { formatBRLDecimalString } from "@/lib/planningLocale";
import type { PlanningGoalContext } from "@/lib/planning";

import type { PlanningInputState } from "./planningForm";

/** Apply only the two approved editable presets; Goal facts remain read-only context. */
export function applyGoalContextPreset(
  input: PlanningInputState,
  context: PlanningGoalContext,
): PlanningInputState {
  return {
    ...input,
    source: context.current_amount === null
      ? "USER_PROVIDED_SCENARIO"
      : "GOAL_CURRENT_AMOUNT",
    initialWealth: "",
    observedAt: "",
    goalId: "",
    monthlyContribution: context.planned_monthly_contribution === null
      ? ""
      : formatBRLDecimalString(context.planned_monthly_contribution),
  };
}
