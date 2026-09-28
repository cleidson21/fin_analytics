"use client";

import { type FormEvent, useState } from "react";
import { Flag, LoaderCircle } from "lucide-react";

import type { Goal } from "@/app/goals/types";
import {
  solveTargetAchievement,
  type TargetAchievementRequest,
  type TargetAchievementResponse,
  type TargetValueBasis,
} from "@/lib/planning";

import { CapabilityEmpty, CapabilityError, CapabilityPanel, CapabilityResultState } from "./CapabilityPanel";
import { PlanningInputs } from "./PlanningInputs";
import { TargetResult } from "./PlanningResults";
import {
  createPlanningInput,
  PlanningInputError,
  portfolioSourceUnavailableMessage,
  toTargetAmount,
  toInitialWealthSelector,
  toProjectionAssumptions,
  type PlanningInputField,
  type PlanningInputState,
} from "./planningForm";

export function TargetCapability({ goals }: { goals: Goal[] }) {
  const [input, setInput] = useState<PlanningInputState>(createPlanningInput);
  const [targetAmount, setTargetAmount] = useState("");
  const [targetBasis, setTargetBasis] = useState<TargetValueBasis | "">("");
  const [result, setResult] = useState<TargetAchievementResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<PlanningInputField, string>>>({});
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const currentSnapshot = JSON.stringify({ input, targetAmount, targetBasis });

  function clearFieldError(field: PlanningInputField) {
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (targetBasis === "") return;
    setError(null);

    const submittedAt = new Date();
    let request: TargetAchievementRequest;
    try {
      request = {
        initial_wealth: toInitialWealthSelector(input, submittedAt),
        assumptions: toProjectionAssumptions(input, submittedAt),
        target_amount: toTargetAmount(targetAmount),
        target_value_basis: targetBasis,
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
      const response = await solveTargetAchievement(request);
      if (!response) throw new Error("Target response is unavailable");
      setResult(response);
      setSubmittedSnapshot(currentSnapshot);
    } catch {
      setError(portfolioSourceUnavailableMessage(input) ?? "Não foi possível analisar o patrimônio-alvo. Revise os dados informados e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <CapabilityPanel title="Meta de patrimônio">
      <form className="space-y-6" onSubmit={handleSubmit}>
        <PlanningInputs value={input} onChange={setInput} goals={goals} idPrefix="target" fieldErrors={fieldErrors} onFieldChange={clearFieldError} />
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 text-sm font-medium text-zinc-300">
            Patrimônio-alvo
            <input required value={targetAmount} onChange={(event) => { setTargetAmount(event.target.value); clearFieldError("targetAmount"); }} placeholder="Ex.: R$ 10.000,00" inputMode="decimal" aria-describedby={fieldErrors.targetAmount ? "target-target-error" : undefined} className="min-h-10 rounded-xl border border-white/[0.12] bg-zinc-900 px-3 text-sm text-zinc-100 outline-none transition focus:border-sky-400/60 focus:ring-2 focus:ring-sky-400/10" />
            {fieldErrors.targetAmount ? <span id="target-target-error" className="text-xs font-normal text-rose-200">{fieldErrors.targetAmount}</span> : null}
          </label>
          <label className="flex flex-col gap-1.5 text-sm font-medium text-zinc-300">
            Base do patrimônio-alvo
            <select required value={targetBasis} onChange={(event) => setTargetBasis(event.target.value as TargetValueBasis | "")} className="min-h-10 rounded-xl border border-white/[0.12] bg-zinc-900 px-3 text-sm text-zinc-100 outline-none transition focus:border-sky-400/60 focus:ring-2 focus:ring-sky-400/10">
              <option value="">Selecione</option>
              <option value="NOMINAL">Nominal</option>
              <option value="REAL">Real</option>
            </select>
          </label>
        </div>
        <button type="submit" disabled={loading} className="inline-flex min-h-10 min-w-36 items-center justify-center gap-2 rounded-xl border border-violet-400/30 bg-violet-500/15 px-4 text-sm font-semibold text-violet-100 transition-colors hover:border-violet-300/45 hover:bg-violet-500/25 disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <Flag aria-hidden="true" size={16} />}
          {loading ? "Analisando..." : "Analisar meta"}
        </button>
      </form>
      {error ? <CapabilityError message={error} onDismiss={() => setError(null)} /> : null}
      <CapabilityResultState hasResult={result !== null} loading={loading} dirty={result !== null && submittedSnapshot !== currentSnapshot} loadingLabel="Analisando meta" empty={<CapabilityEmpty>Informe um patrimônio-alvo para ver quando ele pode ser alcançado.</CapabilityEmpty>}>
        {result ? <TargetResult result={result} /> : null}
      </CapabilityResultState>
    </CapabilityPanel>
  );
}
