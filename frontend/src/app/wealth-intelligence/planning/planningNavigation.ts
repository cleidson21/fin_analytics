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
  needsNormalization: boolean;
}

export function resolvePlanningRoute(
  searchParams: URLSearchParams,
): PlanningRouteState {
  const rawIntention = searchParams.get("intent");
  const rawTask = searchParams.get("task");
  const intention = INTENTIONS.has(rawIntention as PlanningIntention)
    ? (rawIntention as PlanningIntention)
    : "simulate";
  const objectiveMode = OBJECTIVE_MODES.has(rawTask as PlanningObjectiveMode)
    ? (rawTask as PlanningObjectiveMode)
    : "target";
  const taskIsAllowed = intention === "objective" ? rawTask === objectiveMode : rawTask === null;

  return {
    intention,
    objectiveMode,
    needsNormalization: rawIntention !== intention || !taskIsAllowed,
  };
}

export function buildPlanningHref(
  pathname: string,
  currentSearchParams: URLSearchParams,
  intention: PlanningIntention,
  objectiveMode: PlanningObjectiveMode = "target",
): string {
  const next = new URLSearchParams(currentSearchParams);
  next.set("intent", intention);
  if (intention === "objective") {
    next.set("task", objectiveMode);
  } else {
    next.delete("task");
  }
  return `${pathname}?${next.toString()}`;
}
