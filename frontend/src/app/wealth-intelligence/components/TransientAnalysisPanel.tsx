"use client";

import { Trash2 } from "lucide-react";

import { FireResults } from "../fire/components/FireResults";
import {
  GoalPlanningResult,
  ProjectionResult,
  RequiredContributionResult,
  ScenarioComparisonResult,
  TargetResult,
} from "../planning/components/PlanningResults";
import { useTransientAnalysis } from "../TransientAnalysisContext";
import { transientAnalysisLabel, type TransientAnalysisSelection } from "../transientAnalysis";

function SelectedResult({ selection }: { selection: TransientAnalysisSelection }) {
  if (selection.domain === "FIRE") {
    return <FireResults result={selection.result} />;
  }
  switch (selection.kind) {
    case "PROJECTION":
      return <ProjectionResult result={selection.result} />;
    case "TARGET":
      return <TargetResult result={selection.result} />;
    case "REQUIRED_CONTRIBUTION":
      return <RequiredContributionResult result={selection.result} />;
    case "GOAL":
      return <GoalPlanningResult result={selection.result} />;
    case "COMPARISON":
      return <ScenarioComparisonResult result={selection.result} />;
  }
}

export function TransientAnalysisPanel() {
  const { selection, clearSelection } = useTransientAnalysis();
  if (selection === null) return null;

  return (
    <section
      aria-labelledby="transient-analysis-title"
      className="rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.025] p-4 sm:p-5"
    >
      <div className="mb-4 flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.13em] text-success-foreground">
              Resultado transitório
            </span>
            <span className="rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.13em] text-muted-foreground">
              Resposta validada
            </span>
          </div>
          <h2 id="transient-analysis-title" className="mt-2 text-lg font-semibold text-foreground">
            {transientAnalysisLabel(selection)}
          </h2>
          <p className="mt-1 text-[11px] text-muted-foreground">API determinística de {selection.domain === "FIRE" ? "FIRE" : "Planning"} · apenas nesta navegação · não é patrimônio atual</p>
        </div>
        <button
          type="button"
          onClick={clearSelection}
          className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-border px-3 text-xs font-semibold text-foreground/90 hover:bg-muted/45 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/50"
        >
          <Trash2 aria-hidden="true" size={15} />
          Limpar seleção
        </button>
      </div>
      <SelectedResult selection={selection} />
    </section>
  );
}
