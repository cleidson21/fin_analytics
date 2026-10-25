"use client";

import { type FormEvent, useState } from "react";
import { Calculator, LoaderCircle } from "lucide-react";

import type { Goal } from "@/app/goals/types";
import { ShowOnWealthHomeButton } from "@/app/wealth-intelligence/components/ShowOnWealthHomeButton";
import { projectPlanning, type ForwardProjectionResponse, type ProjectionRequest } from "@/lib/planning";

import { CapabilityEmpty, CapabilityError, CapabilityPanel, CapabilityResultState } from "./CapabilityPanel";
import { PlanningInputs } from "./PlanningInputs";
import { ProjectionResult } from "./PlanningResults";
import {
  createPlanningInput,
  PlanningInputError,
  portfolioSourceUnavailableMessage,
  toInitialWealthSelector,
  toProjectionAssumptions,
  type PlanningInputField,
  type PlanningInputState,
} from "./planningForm";

export function ProjectionCapability({ goals }: { goals: Goal[] }) {
  const [input, setInput] = useState<PlanningInputState>(createPlanningInput);
  const [result, setResult] = useState<ForwardProjectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<PlanningInputField, string>>>({});
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const currentSnapshot = JSON.stringify(input);

  function clearFieldError(field: PlanningInputField) {
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const submittedAt = new Date();
    let request: ProjectionRequest;
    try {
      request = {
        initial_wealth: toInitialWealthSelector(input, submittedAt),
        assumptions: toProjectionAssumptions(input, submittedAt),
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
      const response = await projectPlanning(request);
      if (!response) throw new Error("Planning response is unavailable");
      setResult(response);
      setSubmittedSnapshot(currentSnapshot);
    } catch {
      setError(portfolioSourceUnavailableMessage(input) ?? "Não foi possível executar a projeção. Revise os dados informados e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <CapabilityPanel title="Projeção">
      <form className="space-y-5" onSubmit={handleSubmit}>
        <PlanningInputs value={input} onChange={setInput} goals={goals} idPrefix="projection" fieldErrors={fieldErrors} onFieldChange={clearFieldError} />
        <div className="flex justify-end border-t border-border pt-4">
        <button type="submit" disabled={loading} className="inline-flex min-h-10 min-w-40 items-center justify-center gap-2 rounded-xl bg-violet-300 px-4 text-sm font-semibold text-zinc-950 transition-colors hover:bg-violet-200 disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <Calculator aria-hidden="true" size={16} />}
          {loading ? "Calculando..." : "Executar projeção"}
        </button>
        </div>
      </form>
      {error ? <CapabilityError message={error} onDismiss={() => setError(null)} /> : null}
      <CapabilityResultState hasResult={result !== null} loading={loading} dirty={result !== null && submittedSnapshot !== currentSnapshot} loadingLabel="Calculando projeção" empty={<CapabilityEmpty>Informe as premissas para visualizar a trajetória.</CapabilityEmpty>} action={result && error === null ? <ShowOnWealthHomeButton analysis={{ domain: "PLANNING", kind: "PROJECTION", result }} /> : null}>
        {result ? <ProjectionResult result={result} /> : null}
      </CapabilityResultState>
    </CapabilityPanel>
  );
}
