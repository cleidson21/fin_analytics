import {
  formatFinancialInputError,
  formatLocalISODate,
  parseBRDateInput,
} from "@/lib/planningLocale";
import type {
  OutputMode,
  ScenarioArchetype,
  ScenarioComparisonRequest,
} from "@/lib/planning";

import {
  PlanningInputError,
  toInitialWealthSelector,
  toProjectionAssumptions,
  toTargetAmount,
  type PlanningInputField,
  type PlanningInputState,
} from "./planningForm";

export type ScenarioComparisonSharedContext = {
  asOfDate: string;
  horizonMonths: number | undefined;
  outputMode: OutputMode;
  includeTarget: boolean;
  targetAmount: string;
};

export type ScenarioComparisonDraftInput = {
  scenarioId: string;
  label: string;
  archetype: ScenarioArchetype | "";
  input: PlanningInputState;
};

export class ScenarioComparisonBuildError extends Error {
  constructor(
    public readonly scope: "shared" | "scenario",
    public readonly field: PlanningInputField,
    message: string,
    public readonly scenarioId?: string,
  ) {
    super(message);
    this.name = "ScenarioComparisonBuildError";
  }
}

export function createScenarioComparisonSharedContext(): ScenarioComparisonSharedContext {
  return {
    asOfDate: "",
    horizonMonths: undefined,
    outputMode: "NOMINAL",
    includeTarget: false,
    targetAmount: "",
  };
}

export function referenceAfterScenarioRemoval(
  referenceScenarioId: string,
  removedScenarioId: string,
) {
  return referenceScenarioId === removedScenarioId ? "" : referenceScenarioId;
}

function resolveSharedAsOfDate(value: string, submittedAt: Date) {
  if (value.trim() === "") return formatLocalISODate(submittedAt);

  const parsed = parseBRDateInput(value);
  if (!parsed.ok) {
    throw new ScenarioComparisonBuildError(
      "shared",
      "asOfDate",
      formatFinancialInputError(parsed.code, "date"),
    );
  }
  return parsed.value;
}

function validateSharedContext(
  context: ScenarioComparisonSharedContext,
  scenarios: readonly ScenarioComparisonDraftInput[],
  submittedAt: Date,
) {
  if (context.horizonMonths === undefined) {
    throw new ScenarioComparisonBuildError("shared", "horizonMonths", "Preencha este campo.");
  }

  const asOfDate = resolveSharedAsOfDate(context.asOfDate, submittedAt);
  if (context.outputMode === "NOMINAL" && scenarios.some((scenario) => scenario.input.returnType === "REAL")) {
    throw new ScenarioComparisonBuildError(
      "shared",
      "outputMode",
      "Para retorno real, use valores reais como base de saída.",
    );
  }
  return asOfDate;
}

export function buildScenarioComparisonRequest(
  scenarios: readonly ScenarioComparisonDraftInput[],
  sharedContext: ScenarioComparisonSharedContext,
  referenceScenarioId: string,
  submittedAt: Date = new Date(),
): ScenarioComparisonRequest {
  validateSharedContext(sharedContext, scenarios, submittedAt);

  let targetAmount = null;
  if (sharedContext.includeTarget) {
    try {
      targetAmount = toTargetAmount(sharedContext.targetAmount);
    } catch (caught) {
      if (caught instanceof PlanningInputError) {
        throw new ScenarioComparisonBuildError("shared", caught.field, caught.message);
      }
      throw caught;
    }
  }

  return {
    scenarios: scenarios.map((scenario) => {
      const scenarioInput: PlanningInputState = {
        ...scenario.input,
        asOfDate: sharedContext.asOfDate,
        horizonMonths: sharedContext.horizonMonths,
        outputMode: sharedContext.outputMode,
      };

      try {
        return {
          scenario_id: scenario.scenarioId,
          initial_wealth: toInitialWealthSelector(scenarioInput, submittedAt),
          assumptions: toProjectionAssumptions(scenarioInput, submittedAt),
          label: scenario.label.trim() || null,
          archetype: scenario.archetype || null,
        };
      } catch (caught) {
        if (caught instanceof PlanningInputError) {
          throw new ScenarioComparisonBuildError("scenario", caught.field, caught.message, scenario.scenarioId);
        }
        throw caught;
      }
    }),
    reference_scenario_id: referenceScenarioId,
    target_amount: targetAmount,
    target_value_basis: sharedContext.includeTarget ? sharedContext.outputMode : null,
  };
}
