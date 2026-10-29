import type { GoalBudgetPreviewRequest } from "@/lib/planning";
import {
  formatFinancialInputError,
  formatLocalISODate,
  parseBRDateInput,
  parseBRLMoneyInput,
  parseBRPercentInputToFraction,
} from "@/lib/planningLocale";

export interface GoalBudgetFormState {
  monthlyBudget: string;
  horizonMonths: string;
  expectedReturnRate: string;
  asOfDate: string;
  allocations: Array<{ goalId: string; A: string; B: string }>;
}

export class GoalBudgetInputError extends Error {
  constructor(public readonly field: string, message: string) {
    super(message);
  }
}

export function createGoalBudgetForm(): GoalBudgetFormState {
  return { monthlyBudget: "", horizonMonths: "", expectedReturnRate: "", asOfDate: "", allocations: [] };
}

function money(value: string, field: string): string {
  const parsed = parseBRLMoneyInput(value);
  if (!parsed.ok) throw new GoalBudgetInputError(field, formatFinancialInputError(parsed.code, "money"));
  return parsed.value;
}

/** Lexical input adaptation only; equality, budget arithmetic and financial rules stay server-side. */
export function toGoalBudgetRequest(
  form: GoalBudgetFormState,
  submittedAt = new Date(),
): GoalBudgetPreviewRequest {
  if (form.allocations.length === 0) throw new GoalBudgetInputError("goals", "Selecione pelo menos uma meta.");
  if (form.allocations.length > 20) throw new GoalBudgetInputError("goals", "Selecione até 20 metas.");
  if (!/^\d+$/.test(form.horizonMonths) || !Number.isInteger(Number(form.horizonMonths)) || Number(form.horizonMonths) < 1 || Number(form.horizonMonths) > 1200) {
    throw new GoalBudgetInputError("horizonMonths", "Informe um horizonte de 1 a 1.200 meses.");
  }
  const rate = parseBRPercentInputToFraction(form.expectedReturnRate);
  if (!rate.ok) throw new GoalBudgetInputError("expectedReturnRate", formatFinancialInputError(rate.code, "rate"));
  const date = form.asOfDate.trim() === "" ? null : parseBRDateInput(form.asOfDate);
  if (date && !date.ok) throw new GoalBudgetInputError("asOfDate", formatFinancialInputError(date.code, "date"));

  return {
    goal_ids: form.allocations.map((allocation) => allocation.goalId),
    monthly_budget: money(form.monthlyBudget, "monthlyBudget"),
    assumptions: {
      as_of_date: date?.ok ? date.value : formatLocalISODate(submittedAt),
      expected_return_rate: rate.value,
      return_type: "NOMINAL",
      output_mode: "NOMINAL",
      horizon_months: Number(form.horizonMonths),
      rate_basis: "EFFECTIVE_ANNUAL",
      contribution_timing: "END_OF_MONTH",
    },
    target_value_basis: "NOMINAL",
    scenarios: ["A", "B"].map((scenarioId) => ({
      scenario_id: scenarioId as "A" | "B",
      allocations: form.allocations.map((allocation) => ({
        goal_id: allocation.goalId,
        scenario_monthly_contribution: money(allocation[scenarioId as "A" | "B"], `${allocation.goalId}-${scenarioId}`),
      })),
    })) as GoalBudgetPreviewRequest["scenarios"],
  };
}
