"use client";

import { useEffect, useState } from "react";

import type { Goal } from "@/app/goals/types";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";

import { GoalPlanningCapability } from "./components/GoalPlanningCapability";
import { ProjectionCapability } from "./components/ProjectionCapability";
import { RequiredContributionCapability } from "./components/RequiredContributionCapability";
import { ScenarioComparisonCapability } from "./components/ScenarioComparisonCapability";
import { TargetCapability } from "./components/TargetCapability";

type PlanningIntention = "simulate" | "objective" | "compare";
type ObjectiveMode = "target" | "required" | "goals";

const intentions: { id: PlanningIntention; label: string }[] = [
  { id: "simulate", label: "Simular" },
  { id: "objective", label: "Objetivo" },
  { id: "compare", label: "Comparar" },
];

const objectiveModes: { id: ObjectiveMode; label: string }[] = [
  { id: "target", label: "Quando alcanço?" },
  { id: "required", label: "Quanto aportar?" },
  { id: "goals", label: "Meta existente" },
];

export default function PlanningPage() {
  const [activeIntention, setActiveIntention] = useState<PlanningIntention>("simulate");
  const [objectiveMode, setObjectiveMode] = useState<ObjectiveMode>("target");
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

  return (
    <PageLayout hideTitle>
      <div className="space-y-6">
        <h1 className="sr-only">Planejamento Financeiro</h1>

        <nav aria-label="Intenções de planejamento" className="grid grid-cols-3 gap-2 border-b border-white/[0.06] pb-4">
          {intentions.map((intention) => {
            const isActive = activeIntention === intention.id;
            return (
              <button
                key={intention.id}
                type="button"
                aria-pressed={isActive}
                onClick={() => setActiveIntention(intention.id)}
                className={`min-h-10 rounded-xl border px-3 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50 ${
                  isActive
                    ? "border-violet-400/35 bg-violet-500/15 text-violet-100"
                    : "border-white/[0.10] bg-white/[0.025] text-zinc-300 hover:bg-white/[0.07] hover:text-white"
                }`}
              >
                {intention.label}
              </button>
            );
          })}
        </nav>

        {activeIntention === "objective" ? (
          <nav aria-label="Tipo de objetivo" className="flex flex-wrap gap-2">
            {objectiveModes.map((mode) => {
              const isActive = objectiveMode === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => setObjectiveMode(mode.id)}
                  className={`min-h-9 rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50 ${
                    isActive
                      ? "border-violet-300/45 bg-violet-300/15 text-violet-100"
                      : "border-white/[0.10] bg-transparent text-zinc-400 hover:bg-white/[0.05] hover:text-zinc-200"
                  }`}
                >
                  {mode.label}
                </button>
              );
            })}
          </nav>
        ) : null}

        {goalsError ? <p role="status" className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] p-3 text-sm text-amber-100">{goalsError}</p> : null}

        {activeIntention === "simulate" ? <ProjectionCapability goals={goals} /> : null}
        {activeIntention === "objective" && objectiveMode === "target" ? <TargetCapability goals={goals} /> : null}
        {activeIntention === "objective" && objectiveMode === "required" ? <RequiredContributionCapability goals={goals} /> : null}
        {activeIntention === "objective" && objectiveMode === "goals" ? <GoalPlanningCapability goals={goals} loadingGoals={loadingGoals} /> : null}
        {activeIntention === "compare" ? <ScenarioComparisonCapability goals={goals} /> : null}
      </div>
    </PageLayout>
  );
}
