export type PlanningIntention = "simulate" | "objective" | "compare";
export type PlanningObjectiveMode = "target" | "required" | "goals";

const INTENTIONS = new Set<PlanningIntention>([
  "simulate",
  "objective",
  "compare",
]);
const OBJECTIVE_MODES = new Set<PlanningObjectiveMode>([
  "target",
  "required",
  "goals",
]);

export interface PlanningRouteState {
  intention: PlanningIntention;
  objectiveMode: PlanningObjectiveMode;
  goalId: string | null;
  needsNormalization: boolean;
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function parsePlanningGoalId(value: string | null): string | null {
  return value !== null && UUID_PATTERN.test(value) ? value.toLowerCase() : null;
}

export function resolvePlanningRoute(
  searchParams: URLSearchParams,
): PlanningRouteState {
  const rawIntention = searchParams.get("intent");
  const rawTask = searchParams.get("task");
  const rawGoal = searchParams.get("goal");
  const intention = INTENTIONS.has(rawIntention as PlanningIntention)
    ? (rawIntention as PlanningIntention)
    : "simulate";
  const objectiveMode = OBJECTIVE_MODES.has(rawTask as PlanningObjectiveMode)
    ? (rawTask as PlanningObjectiveMode)
    : "target";
  const taskIsAllowed = intention === "objective" ? rawTask === objectiveMode : rawTask === null;
  const goalIsAllowed = intention === "objective" && objectiveMode === "goals";
  const goalId = goalIsAllowed ? parsePlanningGoalId(rawGoal) : null;
  const goalNeedsNormalization = goalIsAllowed
    ? rawGoal !== null && goalId === null
    : rawGoal !== null;

  return {
    intention,
    objectiveMode,
    goalId,
    needsNormalization:
      rawIntention !== intention || !taskIsAllowed || goalNeedsNormalization,
  };
}

export function buildPlanningHref(
  pathname: string,
  currentSearchParams: URLSearchParams,
  intention: PlanningIntention,
  objectiveMode: PlanningObjectiveMode = "target",
  goalId?: string | null,
): string {
  const next = new URLSearchParams(currentSearchParams);
  const currentGoalId = parsePlanningGoalId(next.get("goal"));
  next.set("intent", intention);
  next.delete("goal");
  if (intention === "objective") {
    next.set("task", objectiveMode);
    if (objectiveMode === "goals") {
      const normalizedGoalId = parsePlanningGoalId(goalId ?? currentGoalId);
      if (normalizedGoalId !== null) next.set("goal", normalizedGoalId);
    }
  } else {
    next.delete("task");
  }
  return `${pathname}?${next.toString()}`;
}
