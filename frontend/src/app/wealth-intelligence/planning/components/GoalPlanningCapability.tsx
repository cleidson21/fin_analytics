"use client";

import { type FormEvent, useState } from "react";
import { LoaderCircle, Target } from "lucide-react";

import type { Goal } from "@/app/goals/types";
import { ShowOnWealthHomeButton } from "@/app/wealth-intelligence/components/ShowOnWealthHomeButton";
import {
  projectGoal,
  type GoalPlanningRequest,
  type GoalPlanningResponse,
  type TargetValueBasis,
} from "@/lib/planning";

import { CapabilityEmpty, CapabilityError, CapabilityPanel, CapabilityResultState } from "./CapabilityPanel";
import { PlanningInputs } from "./PlanningInputs";
import { GoalPlanningResult } from "./PlanningResults";
import {
  createPlanningInput,
  PlanningInputError,
  portfolioSourceUnavailableMessage,
  toGoalPathInitialWealthSelector,
  toProjectionAssumptions,
  type PlanningInputField,
  type PlanningInputState,
} from "./planningForm";

export function GoalPlanningCapability({
  goals,
  loadingGoals,
}: {
  goals: Goal[];
  loadingGoals: boolean;
}) {
  const [goalId, setGoalId] = useState("");
  const [input, setInput] = useState<PlanningInputState>(createPlanningInput);
  const [targetBasis, setTargetBasis] = useState<TargetValueBasis | "">("");
  const [result, setResult] = useState<GoalPlanningResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<PlanningInputField, string>>>({});
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const currentSnapshot = JSON.stringify({ goalId, input, targetBasis });

  function clearFieldError(field: PlanningInputField) {
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  const selectedGoal = goals.find((goal) => goal.id === goalId);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!goalId) return;
    setError(null);

    const submittedAt = new Date();
    let request: GoalPlanningRequest;
    try {
      request = {
        initial_wealth: toGoalPathInitialWealthSelector(input, submittedAt),
        assumptions: toProjectionAssumptions(input, submittedAt),
        target_value_basis: targetBasis || null,
      };
    } catch (caught) {
      if (caught instanceof PlanningInputError) {
        setFieldErrors({ [caught.field]: caught.message });
        return;
      }
      throw caught;
    }

    setLoading(true);
    try {
      const response = await projectGoal(goalId, request);
      if (!response) throw new Error("Goal planning response is unavailable");
      setResult(response);
      setSubmittedSnapshot(currentSnapshot);
    } catch {
      setError(portfolioSourceUnavailableMessage(input) ?? "Não foi possível analisar esta meta. Verifique a meta e as premissas informadas.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <CapabilityPanel title="Metas existentes">
      <form className="space-y-5" onSubmit={handleSubmit}>
        <label className="flex max-w-xl flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Meta
          <select required value={goalId} onChange={(event) => setGoalId(event.target.value)} disabled={loadingGoals} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-400/10 disabled:opacity-60">
            <option value="">{loadingGoals ? "Carregando metas..." : "Selecione uma meta"}</option>
            {goals.map((goal) => (
              <option key={goal.id} value={goal.id}>
                {goal.name} · {goal.goal_type} · {goal.status}
              </option>
            ))}
          </select>
        </label>
        {selectedGoal ? (
          <p className="rounded-xl border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
            Tipo: {selectedGoal.goal_type} · Status: {selectedGoal.status} · Alvo: {String(selectedGoal.target_amount)} · Prazo: {selectedGoal.target_date ?? "não informado"}
          </p>
        ) : null}
        <PlanningInputs value={input} onChange={setInput} goals={goals} idPrefix="goal-planning" goalSourceMode="path" fieldErrors={fieldErrors} onFieldChange={clearFieldError} />
        <label className="flex max-w-xl flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Base do alvo da meta (opcional)
          <select value={targetBasis} onChange={(event) => setTargetBasis(event.target.value as TargetValueBasis | "")} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-400/10">
            <option value="">Não informar</option>
            <option value="NOMINAL">Nominal</option>
            <option value="REAL">Real</option>
          </select>
        </label>
        <div className="flex justify-end border-t border-border pt-4">
        <button type="submit" disabled={loading || loadingGoals || goals.length === 0} className="inline-flex min-h-10 min-w-36 items-center justify-center gap-2 rounded-xl bg-violet-300 px-4 text-sm font-semibold text-zinc-950 transition-colors hover:bg-violet-200 disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <Target aria-hidden="true" size={16} />}
          {loading ? "Analisando..." : "Analisar meta"}
        </button>
        </div>
      </form>
      {error ? <CapabilityError message={error} onDismiss={() => setError(null)} /> : null}
      <CapabilityResultState hasResult={result !== null} loading={loading} dirty={result !== null && submittedSnapshot !== currentSnapshot} loadingLabel="Analisando meta existente" empty={<CapabilityEmpty>Escolha uma meta para analisar seu status de planejamento.</CapabilityEmpty>} action={result && error === null ? <ShowOnWealthHomeButton analysis={{ domain: "PLANNING", kind: "GOAL", result }} /> : null}>
        {result ? <GoalPlanningResult result={result} /> : null}
      </CapabilityResultState>
    </CapabilityPanel>
  );
}
