import {
  formatFinancialInputError,
  formatLocalISODate,
  parseBRDateInput,
  parseBRLMoneyInput,
  parseBRPercentInputToFraction,
} from "@/lib/planningLocale";
import type {
  DecimalString,
  GoalPlanningInitialWealthSelector,
  InitialWealthSource,
  InitialWealthSelector,
  OutputMode,
  ProjectionAssumptions,
  ReturnType,
} from "@/lib/planning";

export type PlanningInputField =
  | "initialWealth"
  | "observedAt"
  | "asOfDate"
  | "monthlyContribution"
  | "expectedReturnRate"
  | "inflationRate"
  | "outputMode"
  | "horizonMonths"
  | "targetAmount";

export type PlanningInputState = {
  source: InitialWealthSource;
  initialWealth: string;
  observedAt: string;
  goalId: string;
  asOfDate: string;
  monthlyContribution: string;
  expectedReturnRate: string;
  returnType: ReturnType;
  outputMode: OutputMode;
  inflationRate: string;
  horizonMonths: number | undefined;
};

export class PlanningInputError extends Error {
  constructor(
    public readonly field: PlanningInputField,
    message: string,
  ) {
    super(message);
    this.name = "PlanningInputError";
  }
}

export function createPlanningInput(): PlanningInputState {
  return {
    source: "USER_PROVIDED_SCENARIO",
    initialWealth: "",
    observedAt: "",
    goalId: "",
    asOfDate: "",
    monthlyContribution: "",
    expectedReturnRate: "",
    returnType: "NOMINAL",
    outputMode: "NOMINAL",
    inflationRate: "",
    horizonMonths: undefined,
  };
}

export function requiresInflation(input: PlanningInputState) {
  return input.returnType === "NOMINAL" && input.outputMode === "REAL";
}

export function portfolioSourceUnavailableMessage(input: PlanningInputState) {
  return input.source === "INVESTMENT_PORTFOLIO_SNAPSHOT"
    ? "Não foi possível utilizar a carteira de investimentos para esta data-base."
    : null;
}

function parseMoney(value: string, field: PlanningInputField): DecimalString {
  const parsed = parseBRLMoneyInput(value);
  if (!parsed.ok) {
    throw new PlanningInputError(field, formatFinancialInputError(parsed.code, "money"));
  }
  return parsed.value;
}

function parseRate(value: string, field: PlanningInputField): DecimalString {
  const parsed = parseBRPercentInputToFraction(value);
  if (!parsed.ok) {
    throw new PlanningInputError(field, formatFinancialInputError(parsed.code, "rate"));
  }
  return parsed.value;
}

function resolveAsOfDate(value: string, submittedAt: Date) {
  if (value.trim() === "") {
    return formatLocalISODate(submittedAt);
  }

  const parsed = parseBRDateInput(value);
  if (!parsed.ok) {
    throw new PlanningInputError("asOfDate", formatFinancialInputError(parsed.code, "date"));
  }
  return parsed.value;
}

function resolveObservedAt(value: string, submittedAt: Date) {
  if (value.trim() === "") {
    return submittedAt.toISOString();
  }

  const historical = new Date(value);
  if (historical.toString() === "Invalid Date") {
    throw new PlanningInputError("observedAt", "Informe uma data e hora válidas.");
  }
  return historical.toISOString();
}

export function toProjectionAssumptions(
  input: PlanningInputState,
  submittedAt: Date = new Date(),
): ProjectionAssumptions {
  if (input.horizonMonths === undefined) {
    throw new PlanningInputError("horizonMonths", "Preencha este campo.");
  }

  return {
    as_of_date: resolveAsOfDate(input.asOfDate, submittedAt),
    scenario_monthly_contribution: parseMoney(input.monthlyContribution, "monthlyContribution"),
    expected_return_rate: parseRate(input.expectedReturnRate, "expectedReturnRate"),
    return_type: input.returnType,
    output_mode: input.outputMode,
    inflation_rate: requiresInflation(input) ? parseRate(input.inflationRate, "inflationRate") : null,
    horizon_months: input.horizonMonths,
    target_date: null,
    rate_basis: "EFFECTIVE_ANNUAL",
    contribution_timing: "END_OF_MONTH",
  };
}

export function toInitialWealthSelector(
  input: PlanningInputState,
  submittedAt: Date = new Date(),
): InitialWealthSelector {
  if (input.source === "GOAL_CURRENT_AMOUNT") {
    return {
      source: "GOAL_CURRENT_AMOUNT",
      goal_id: input.goalId,
    };
  }

  if (input.source === "INVESTMENT_PORTFOLIO_SNAPSHOT") {
    return { source: "INVESTMENT_PORTFOLIO_SNAPSHOT" };
  }

  return {
    source: "USER_PROVIDED_SCENARIO",
    amount: parseMoney(input.initialWealth, "initialWealth"),
    observed_at: resolveObservedAt(input.observedAt, submittedAt),
  };
}

export function toGoalPathInitialWealthSelector(
  input: PlanningInputState,
  submittedAt: Date = new Date(),
): GoalPlanningInitialWealthSelector {
  if (input.source === "GOAL_CURRENT_AMOUNT") {
    return { source: "GOAL_CURRENT_AMOUNT" };
  }

  if (input.source === "INVESTMENT_PORTFOLIO_SNAPSHOT") {
    return { source: "INVESTMENT_PORTFOLIO_SNAPSHOT" };
  }

  return {
    source: "USER_PROVIDED_SCENARIO",
    amount: parseMoney(input.initialWealth, "initialWealth"),
    observed_at: resolveObservedAt(input.observedAt, submittedAt),
  };
}

export function toTargetAmount(value: string): DecimalString {
  return parseMoney(value, "targetAmount");
}
