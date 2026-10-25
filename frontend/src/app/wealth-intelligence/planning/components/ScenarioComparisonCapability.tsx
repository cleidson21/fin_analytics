"use client";

import { type FormEvent, useId, useRef, useState } from "react";
import { BarChart3, ChevronDown, LoaderCircle, Plus, Trash2 } from "lucide-react";

import type { Goal } from "@/app/goals/types";
import { ShowOnWealthHomeButton } from "@/app/wealth-intelligence/components/ShowOnWealthHomeButton";
import {
  comparePlanningScenarios,
  type OutputMode,
  type ScenarioArchetype,
  type ScenarioComparisonResponse,
} from "@/lib/planning";
import { formatBRDate, parseBRDateInput } from "@/lib/planningLocale";

import { CapabilityEmpty, CapabilityError, CapabilityPanel, CapabilityResultState } from "./CapabilityPanel";
import { PlanningInputs } from "./PlanningInputs";
import { ScenarioComparisonResult } from "./PlanningResults";
import { createPlanningInput, portfolioSourceUnavailableMessage, type PlanningInputField, type PlanningInputState } from "./planningForm";
import {
  buildScenarioComparisonRequest,
  createScenarioComparisonSharedContext,
  referenceAfterScenarioRemoval,
  ScenarioComparisonBuildError,
  type ScenarioComparisonDraftInput,
  type ScenarioComparisonSharedContext,
} from "./scenarioComparisonForm";

type ScenarioDraft = ScenarioComparisonDraftInput;
type SharedFieldErrors = Partial<Record<PlanningInputField, string>>;

function createScenario(scenarioId: string): ScenarioDraft {
  return {
    scenarioId,
    label: "",
    archetype: "",
    input: createPlanningInput(),
  };
}

function scenarioName(scenario: ScenarioDraft, index: number) {
  return scenario.label.trim() || `Cenário ${index + 1}`;
}

function SharedDateSummary({ value }: { value: string }) {
  if (value === "") return <span>Hoje</span>;
  const parsed = parseBRDateInput(value);
  return <span>{parsed.ok ? `Data-base personalizada: ${formatBRDate(parsed.value)}` : "Data-base personalizada"}</span>;
}

export function ScenarioComparisonCapability({ goals }: { goals: Goal[] }) {
  const scenarioCounter = useRef(3);
  const advancedId = useId();
  const [scenarios, setScenarios] = useState<ScenarioDraft[]>(() => [
    createScenario("scenario-1"),
    createScenario("scenario-2"),
  ]);
  const [sharedContext, setSharedContext] = useState<ScenarioComparisonSharedContext>(createScenarioComparisonSharedContext);
  const [referenceScenarioId, setReferenceScenarioId] = useState("");
  const [sharedAdvancedOpen, setSharedAdvancedOpen] = useState(false);
  const [result, setResult] = useState<ScenarioComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarioFieldErrors, setScenarioFieldErrors] = useState<Record<string, Partial<Record<PlanningInputField, string>>>>({});
  const [sharedFieldErrors, setSharedFieldErrors] = useState<SharedFieldErrors>({});
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const currentSnapshot = JSON.stringify({ scenarios, sharedContext, referenceScenarioId });

  const containsRealReturn = scenarios.some((scenario) => scenario.input.returnType === "REAL");
  const hasNonDefaultSharedContext =
    sharedContext.outputMode !== "NOMINAL" ||
    sharedContext.asOfDate !== "" ||
    sharedContext.includeTarget;

  function updateScenario(scenarioId: string, next: Partial<ScenarioDraft>) {
    setScenarios((current) => current.map((scenario) => (
      scenario.scenarioId === scenarioId ? { ...scenario, ...next } : scenario
    )));
  }

  function updateScenarioInput(scenarioId: string, input: PlanningInputState) {
    updateScenario(scenarioId, { input });
    if (input.returnType === "REAL" && sharedContext.outputMode === "NOMINAL") {
      setSharedContext((current) => ({ ...current, outputMode: "REAL" }));
    }
  }

  function addScenario() {
    const nextId = `scenario-${scenarioCounter.current}`;
    scenarioCounter.current += 1;
    setScenarios((current) => [...current, createScenario(nextId)]);
  }

  function removeScenario(scenarioId: string) {
    if (scenarios.length <= 2) return;
    setScenarios((current) => current.filter((scenario) => scenario.scenarioId !== scenarioId));
    setReferenceScenarioId((current) => referenceAfterScenarioRemoval(current, scenarioId));
    setScenarioFieldErrors((current) => {
      const next = { ...current };
      delete next[scenarioId];
      return next;
    });
  }

  function updateSharedContext(next: Partial<ScenarioComparisonSharedContext>, field?: PlanningInputField) {
    setSharedContext((current) => ({ ...current, ...next }));
    if (field) clearSharedFieldError(field);
  }

  function clearScenarioFieldError(scenarioId: string, field: PlanningInputField) {
    setScenarioFieldErrors((current) => {
      const scenarioErrors = current[scenarioId];
      if (!scenarioErrors?.[field]) return current;
      const nextScenarioErrors = { ...scenarioErrors };
      delete nextScenarioErrors[field];
      return { ...current, [scenarioId]: nextScenarioErrors };
    });
  }

  function clearSharedFieldError(field: PlanningInputField) {
    setSharedFieldErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function updateSharedOutputMode(outputMode: OutputMode) {
    updateSharedContext({ outputMode }, "outputMode");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!referenceScenarioId) return;
    setError(null);

    let request;
    try {
      request = buildScenarioComparisonRequest(scenarios, sharedContext, referenceScenarioId, new Date());
    } catch (caught) {
      if (caught instanceof ScenarioComparisonBuildError) {
        if (caught.scope === "shared") {
          setSharedFieldErrors((current) => ({ ...current, [caught.field]: caught.message }));
        } else if (caught.scenarioId) {
          const scenarioId = caught.scenarioId;
          const field = caught.field;
          const message = caught.message;
          setScenarioFieldErrors((current) => ({
            ...current,
            [scenarioId]: { ...current[scenarioId], [field]: message },
          }));
        }
        return;
      }
      throw caught;
    }

    setLoading(true);
    try {
      const response = await comparePlanningScenarios(request);
      if (!response) throw new Error("Scenario comparison response is unavailable");
      setResult(response);
      setSubmittedSnapshot(currentSnapshot);
    } catch {
      setError(
        scenarios.some((scenario) => portfolioSourceUnavailableMessage(scenario.input))
          ? "Não foi possível utilizar a carteira de investimentos para esta data-base."
          : "Não foi possível comparar os cenários. Revise os dados informados e tente novamente.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <CapabilityPanel title="Comparar cenários">
      <form className="space-y-5" onSubmit={handleSubmit}>
        <section aria-labelledby="comparison-context-title" className="space-y-4 rounded-2xl border border-border bg-muted/25 p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 id="comparison-context-title" className="text-sm font-semibold text-foreground">Contexto da comparação</h3>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
              <SharedDateSummary value={sharedContext.asOfDate} />
              <span aria-hidden="true">·</span>
              <span>{sharedContext.outputMode === "REAL" ? "Valores reais" : "Valores nominais"}</span>
            </div>
          </div>
          <label className="flex max-w-xs flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Horizonte (meses)
            <input
              required
              type="number"
              value={sharedContext.horizonMonths ?? ""}
              onChange={(event) => updateSharedContext({ horizonMonths: event.currentTarget.valueAsNumber || undefined }, "horizonMonths")}
              aria-describedby={sharedFieldErrors.horizonMonths ? "comparison-horizon-error" : undefined}
              className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10"
            />
            {sharedFieldErrors.horizonMonths ? <span id="comparison-horizon-error" className="text-xs font-normal text-destructive">{sharedFieldErrors.horizonMonths}</span> : null}
          </label>
          <button
            type="button"
            aria-expanded={sharedAdvancedOpen}
            aria-controls={advancedId}
            onClick={() => setSharedAdvancedOpen((current) => !current)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-cyan-200 transition hover:bg-cyan-300/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/50"
          >
            Opções avançadas da comparação
            <ChevronDown aria-hidden="true" size={14} className={sharedAdvancedOpen ? "rotate-180 transition-transform" : "transition-transform"} />
          </button>
          {!sharedAdvancedOpen && hasNonDefaultSharedContext ? (
            <p className="text-xs text-cyan-100">{sharedContext.outputMode === "REAL" ? "Valores reais" : "Valores nominais"}{sharedContext.asOfDate ? " · data-base personalizada" : ""}{sharedContext.includeTarget ? " · patrimônio-alvo incluído" : ""}</p>
          ) : null}
          {sharedAdvancedOpen ? (
            <div id={advancedId} className="grid gap-4 rounded-xl border border-border bg-background p-4 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
                Base de saída
                <select value={sharedContext.outputMode} onChange={(event) => updateSharedOutputMode(event.target.value as OutputMode)} aria-describedby={sharedFieldErrors.outputMode ? "comparison-output-error" : undefined} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10">
                  <option value="NOMINAL" disabled={containsRealReturn}>Nominal</option>
                  <option value="REAL">Real</option>
                </select>
                {sharedFieldErrors.outputMode ? <span id="comparison-output-error" className="text-xs font-normal text-destructive">{sharedFieldErrors.outputMode}</span> : null}
              </label>
              <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
                Data-base personalizada
                <input value={sharedContext.asOfDate} onChange={(event) => updateSharedContext({ asOfDate: event.target.value }, "asOfDate")} placeholder="DD/MM/AAAA" inputMode="numeric" aria-describedby={sharedFieldErrors.asOfDate ? "comparison-as-of-error" : undefined} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10" />
                {sharedFieldErrors.asOfDate ? <span id="comparison-as-of-error" className="text-xs font-normal text-destructive">{sharedFieldErrors.asOfDate}</span> : null}
                <button type="button" onClick={() => updateSharedContext({ asOfDate: "" }, "asOfDate")} className="self-start text-xs font-medium text-cyan-200 hover:text-cyan-100">Usar hoje</button>
              </label>
              <div className="space-y-4 sm:col-span-2">
                <label className="flex items-center gap-2 text-sm font-medium text-foreground/90">
                  <input type="checkbox" checked={sharedContext.includeTarget} onChange={(event) => updateSharedContext({ includeTarget: event.target.checked, targetAmount: event.target.checked ? sharedContext.targetAmount : "" }, "targetAmount")} className="h-4 w-4 accent-cyan-300" />
                  Comparar também um patrimônio-alvo
                </label>
                {sharedContext.includeTarget ? (
                  <label className="flex max-w-sm flex-col gap-1.5 text-sm font-medium text-foreground/90">
                    Patrimônio-alvo compartilhado
                    <input required value={sharedContext.targetAmount} onChange={(event) => updateSharedContext({ targetAmount: event.target.value }, "targetAmount")} placeholder="Ex.: R$ 10.000,00" inputMode="decimal" aria-describedby={sharedFieldErrors.targetAmount ? "comparison-target-error" : undefined} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10" />
                    {sharedFieldErrors.targetAmount ? <span id="comparison-target-error" className="text-xs font-normal text-destructive">{sharedFieldErrors.targetAmount}</span> : null}
                    <span className="text-xs font-normal text-muted-foreground">Base do alvo: {sharedContext.outputMode === "REAL" ? "real" : "nominal"}.</span>
                  </label>
                ) : null}
              </div>
              <p className="text-xs leading-5 text-muted-foreground sm:col-span-2">Taxa efetiva anual · Aporte no fim do mês</p>
            </div>
          ) : null}
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          {scenarios.map((scenario, index) => (
            <article key={scenario.scenarioId} aria-labelledby={`${scenario.scenarioId}-title`} className="space-y-4 rounded-2xl border border-border bg-background p-4 sm:p-5">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div className="min-w-0 flex-1 space-y-3">
                  <h3 id={`${scenario.scenarioId}-title`} className="text-sm font-semibold text-foreground">{scenarioName(scenario, index)}</h3>
                  <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
                    Nome do cenário (opcional)
                    <input value={scenario.label} onChange={(event) => updateScenario(scenario.scenarioId, { label: event.target.value })} placeholder="Ex.: Aporte maior" className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10" />
                  </label>
                </div>
                {scenarios.length > 2 ? (
                  <button type="button" onClick={() => removeScenario(scenario.scenarioId)} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-rose-300/20 px-3 text-sm font-semibold text-destructive hover:bg-rose-300/10">
                    <Trash2 aria-hidden="true" size={16} /> Remover
                  </button>
                ) : null}
              </div>
              <PlanningInputs
                value={scenario.input}
                onChange={(input) => updateScenarioInput(scenario.scenarioId, input)}
                goals={goals}
                idPrefix={scenario.scenarioId}
                comparisonScenario
                comparisonOutputMode={sharedContext.outputMode}
                fieldErrors={scenarioFieldErrors[scenario.scenarioId]}
                onFieldChange={(field) => clearScenarioFieldError(scenario.scenarioId, field)}
                advancedSlot={(
                  <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
                    Arquétipo (opcional)
                    <select value={scenario.archetype} onChange={(event) => updateScenario(scenario.scenarioId, { archetype: event.target.value as ScenarioArchetype | "" })} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10">
                      <option value="">Sem arquétipo</option>
                      <option value="CONSERVATIVE">Conservador</option>
                      <option value="BASE">Base</option>
                      <option value="OPTIMISTIC">Otimista</option>
                    </select>
                  </label>
                )}
              />
            </article>
          ))}
        </div>

        <div className="flex flex-col gap-4 rounded-xl border border-border bg-muted/25 p-4 sm:flex-row sm:items-end sm:justify-between">
          <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Referência
            <select required value={referenceScenarioId} onChange={(event) => setReferenceScenarioId(event.target.value)} className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10">
              <option value="">Selecione a referência</option>
              {scenarios.map((scenario, index) => (
                <option key={scenario.scenarioId} value={scenario.scenarioId}>{scenarioName(scenario, index)}</option>
              ))}
            </select>
          </label>
          <button type="button" onClick={addScenario} className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-4 text-sm font-semibold text-cyan-100 hover:bg-cyan-300/15">
            <Plus aria-hidden="true" size={16} /> Adicionar cenário
          </button>
        </div>

        <div className="flex justify-end border-t border-border pt-4">
        <button type="submit" disabled={loading} className="inline-flex min-h-10 min-w-44 items-center justify-center gap-2 rounded-xl bg-violet-300 px-4 text-sm font-semibold text-zinc-950 transition-colors hover:bg-violet-200 disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <BarChart3 aria-hidden="true" size={16} />}
          {loading ? "Comparando..." : "Comparar cenários"}
        </button>
        </div>
      </form>
      {error ? <CapabilityError message={error} onDismiss={() => setError(null)} /> : null}
      <CapabilityResultState hasResult={result !== null} loading={loading} dirty={result !== null && submittedSnapshot !== currentSnapshot} loadingLabel="Comparando cenários" empty={<CapabilityEmpty>Crie ao menos dois cenários e escolha uma referência antes de comparar.</CapabilityEmpty>} action={result && error === null ? <ShowOnWealthHomeButton analysis={{ domain: "PLANNING", kind: "COMPARISON", result }} /> : null}>
        {result ? <ScenarioComparisonResult result={result} /> : null}
      </CapabilityResultState>
    </CapabilityPanel>
  );
}
