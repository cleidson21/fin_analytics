"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  CalendarClock,
  CircleDollarSign,
  Flag,
  GitCompareArrows,
  Target,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import type { Goal } from "@/app/goals/types";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";

import { GoalPlanningCapability } from "./components/GoalPlanningCapability";
import { ProjectionCapability } from "./components/ProjectionCapability";
import { RequiredContributionCapability } from "./components/RequiredContributionCapability";
import { ScenarioComparisonCapability } from "./components/ScenarioComparisonCapability";
import { TargetCapability } from "./components/TargetCapability";
import {
  buildPlanningHref,
  resolvePlanningRoute,
  type PlanningIntention,
  type PlanningObjectiveMode,
} from "./planningNavigation";

type PlanningIntentionOption = {
  value: PlanningIntention;
  label: string;
  icon: LucideIcon;
};

const intentionOptions: PlanningIntentionOption[] = [
  {
    value: "simulate",
    label: "Simular",
    icon: TrendingUp,
  },
  {
    value: "objective",
    label: "Objetivo",
    icon: Target,
  },
  {
    value: "compare",
    label: "Comparar",
    icon: GitCompareArrows,
  },
];

const objectiveOptions: Array<{
  value: PlanningObjectiveMode;
  label: string;
  icon: LucideIcon;
}> = [
  { value: "target", label: "Quando alcanço?", icon: CalendarClock },
  { value: "required", label: "Quanto aportar?", icon: CircleDollarSign },
  { value: "goals", label: "Meta cadastrada", icon: Flag },
];

function PlanningPageContent() {
  const intentionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const objectiveRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsString = searchParams.toString();
  const routeState = resolvePlanningRoute(new URLSearchParams(searchParamsString));
  const activeIntention = routeState.intention;
  const objectiveMode = routeState.objectiveMode;
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loadingGoals, setLoadingGoals] = useState(true);
  const [goalsError, setGoalsError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadGoals() {
      try {
        const response = await fetchFromAPI<Goal[]>("/goals");
        if (!response) throw new Error("Goals response is unavailable");
        if (active) setGoals(response);
      } catch {
        if (active) setGoalsError("As metas não puderam ser carregadas. As análises com valor informado continuam disponíveis.");
      } finally {
        if (active) setLoadingGoals(false);
      }
    }

    void loadGoals();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!routeState.needsNormalization) return;
    router.replace(
      buildPlanningHref(
        pathname,
        new URLSearchParams(searchParamsString),
        activeIntention,
        objectiveMode,
      ),
      { scroll: false },
    );
  }, [
    activeIntention,
    objectiveMode,
    pathname,
    routeState.needsNormalization,
    router,
    searchParamsString,
  ]);

  function selectIntention(intention: PlanningIntention) {
    router.push(
      buildPlanningHref(
        pathname,
        new URLSearchParams(searchParamsString),
        intention,
        intention === "objective" ? objectiveMode : "target",
      ),
      { scroll: false },
    );
  }

  function selectObjectiveMode(nextObjectiveMode: PlanningObjectiveMode) {
    router.push(
      buildPlanningHref(
        pathname,
        new URLSearchParams(searchParamsString),
        "objective",
        nextObjectiveMode,
      ),
      { scroll: false },
    );
  }

  function moveTabFocus<T>(
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
    options: readonly T[],
    refs: React.RefObject<Array<HTMLButtonElement | null>>,
    select: (option: T) => void,
  ) {
    const lastIndex = options.length - 1;
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = index === lastIndex ? 0 : index + 1;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = index === 0 ? lastIndex : index - 1;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = lastIndex;
    if (nextIndex === null) return;

    event.preventDefault();
    select(options[nextIndex]);
    refs.current[nextIndex]?.focus();
  }

  return (
    <PageLayout hideTitle>
      <div className="space-y-4">
        <h1 className="sr-only">Planejamento Financeiro</h1>

        <section aria-labelledby="planning-mode-title" className="border-b border-border pb-4">
          <div className="mb-2">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-violet-700 dark:text-violet-300">Planejamento</p>
              <h2 id="planning-mode-title" className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                O que você quer descobrir?
              </h2>
            </div>
          </div>
          <div role="tablist" aria-label="Intenções de planejamento" className="grid grid-cols-3 gap-1 rounded-xl border border-border bg-muted/35 p-1">
          {intentionOptions.map((option, index) => {
            const isActive = activeIntention === option.value;
            const Icon = option.icon;
            return (
              <button
                key={option.value}
                ref={(node) => { intentionRefs.current[index] = node; }}
                id={`planning-intention-${option.value}`}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls="planning-result-panel"
                tabIndex={isActive ? 0 : -1}
                onClick={() => selectIntention(option.value)}
                onKeyDown={(event) => moveTabFocus(event, index, intentionOptions, intentionRefs, (next) => selectIntention(next.value))}
                className={`group flex min-h-11 min-w-0 items-center justify-center gap-2 rounded-lg border px-2 py-2 text-center text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none ${
                  isActive
                    ? "border-border bg-background text-foreground shadow-sm"
                    : "border-transparent text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                <Icon aria-hidden="true" className={`size-4 shrink-0 ${isActive ? "text-violet-600 dark:text-violet-300" : "text-muted-foreground"}`} />
                <span className="truncate">{option.label}</span>
              </button>
            );
          })}
          </div>

          {activeIntention === "objective" ? (
            <div className="mt-3 flex flex-wrap items-center gap-2" role="tablist" aria-label="Tipo de objetivo">
              {objectiveOptions.map((option, index) => {
                const isActive = objectiveMode === option.value;
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    ref={(node) => { objectiveRefs.current[index] = node; }}
                    id={`planning-objective-${option.value}`}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    aria-controls="planning-result-panel"
                    tabIndex={isActive ? 0 : -1}
                    onClick={() => selectObjectiveMode(option.value)}
                    onKeyDown={(event) => moveTabFocus(event, index, objectiveOptions, objectiveRefs, (next) => selectObjectiveMode(next.value))}
                    className={`inline-flex min-h-10 items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold transition focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none sm:text-sm ${
                      isActive
                        ? "border-violet-500/35 bg-violet-500/10 text-violet-700 dark:text-violet-200"
                        : "border-border bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}
                  >
                    <Icon aria-hidden="true" className="size-3.5" />
                    {option.label}
                  </button>
                );
              })}
            </div>
          ) : null}
        </section>

        {goalsError ? <p role="status" className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] p-3 text-sm text-warning-foreground">{goalsError}</p> : null}

        <div
          id="planning-result-panel"
          role="tabpanel"
          aria-labelledby={activeIntention === "objective" ? `planning-objective-${objectiveMode}` : `planning-intention-${activeIntention}`}
          aria-live="polite"
        >
          {activeIntention === "simulate" ? <ProjectionCapability goals={goals} /> : null}
          {activeIntention === "objective" && objectiveMode === "target" ? <TargetCapability goals={goals} /> : null}
          {activeIntention === "objective" && objectiveMode === "required" ? <RequiredContributionCapability goals={goals} /> : null}
          {activeIntention === "objective" && objectiveMode === "goals" ? <GoalPlanningCapability goals={goals} loadingGoals={loadingGoals} /> : null}
          {activeIntention === "compare" ? <ScenarioComparisonCapability goals={goals} /> : null}
        </div>
      </div>
    </PageLayout>
  );
}

function PlanningPageFallback() {
  return (
    <PageLayout hideTitle>
      <div aria-label="Carregando Planejamento" className="space-y-4 py-4">
        <div className="h-12 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
        <div className="h-80 animate-pulse rounded-xl bg-muted/60 motion-reduce:animate-none" />
      </div>
    </PageLayout>
  );
}

export default function PlanningPage() {
  return (
    <Suspense fallback={<PlanningPageFallback />}>
      <PlanningPageContent />
    </Suspense>
  );
}
