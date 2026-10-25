import type { FireAnalysisResponse } from "@/lib/fire";
import type {
  ForwardProjectionResponse,
  GoalPlanningResponse,
  RequiredContributionResponse,
  ScenarioComparisonResponse,
  TargetAchievementResponse,
} from "@/lib/planning";

export type TransientAnalysisCandidate =
  | { domain: "PLANNING"; kind: "PROJECTION"; result: ForwardProjectionResponse }
  | { domain: "PLANNING"; kind: "TARGET"; result: TargetAchievementResponse }
  | { domain: "PLANNING"; kind: "REQUIRED_CONTRIBUTION"; result: RequiredContributionResponse }
  | { domain: "PLANNING"; kind: "GOAL"; result: GoalPlanningResponse }
  | { domain: "PLANNING"; kind: "COMPARISON"; result: ScenarioComparisonResponse }
  | { domain: "FIRE"; kind: "FIRE_ANALYSIS"; result: FireAnalysisResponse };

export type TransientAnalysisSelection = TransientAnalysisCandidate & {
  selectedAt: string;
  validation: "VALIDATED_API_RESPONSE";
};

export function isSelectableAnalysis(candidate: TransientAnalysisCandidate): boolean {
  if (candidate.domain === "FIRE") {
    if (candidate.result.analysis_type === "PROJECTED_DATE") {
      return candidate.result.projection !== null;
    }
    if (candidate.result.analysis_type === "REQUIRED_CONTRIBUTION") {
      return candidate.result.required_contribution !== null;
    }
    return candidate.result.analysis_type === "SUMMARY";
  }

  if (candidate.kind === "GOAL") {
    return (
      candidate.result.status !== "INSUFFICIENT_DATA" &&
      candidate.result.status !== "NOT_APPLICABLE" &&
      candidate.result.initial_wealth_fact !== null &&
      candidate.result.target_achievement_result !== null
    );
  }

  if (candidate.kind === "COMPARISON") {
    return candidate.result.entries.length >= 2;
  }

  return true;
}

export function transientAnalysisLabel(selection: TransientAnalysisSelection): string {
  if (selection.domain === "FIRE") return "Independência financeira";
  return {
    PROJECTION: "Projeção patrimonial",
    TARGET: "Prazo para o patrimônio-alvo",
    REQUIRED_CONTRIBUTION: "Aporte necessário",
    GOAL: "Planejamento de meta",
    COMPARISON: "Comparação de cenários",
  }[selection.kind];
}
