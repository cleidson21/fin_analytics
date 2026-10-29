"use client";

import { type FormEvent, useEffect, useId, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { GOAL_STATUS_LABELS, type Goal } from "@/app/goals/types";
import { useAuth } from "@/contexts/AuthContext";
import { APIRequestError, AuthError } from "@/lib/api";
import { previewGoalBudget, type GoalBudgetPreviewResponse } from "@/lib/planning";
import { CapabilityEmpty, CapabilityPanel, CapabilityResultState } from "./CapabilityPanel";
import { createGoalBudgetForm, GoalBudgetInputError, toGoalBudgetRequest, type GoalBudgetFormState } from "./goalBudgetForm";
import { GoalBudgetResults } from "./GoalBudgetResults";

interface Props {
  goals: Goal[];
  loadingGoals: boolean;
  goalsError: string | null;
  onRefreshGoals: () => void;
  sessionExpired?: boolean;
}

const fieldClass = "min-h-11 w-full min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60";

function errorMessage(error: unknown): string {
  if (error instanceof AuthError) return "Sua sessão expirou. Entre novamente para comparar os cenários.";
  if (error instanceof APIRequestError) {
    if (error.status === 404) return "Uma ou mais metas não estão disponíveis para este usuário. Atualize a lista e revise a seleção.";
    if (error.status === 422) return "Revise os valores e as premissas. Os totais dos aportes em A e B devem ser exatamente iguais; valores monetários devem ser não negativos e o retorno deve ser maior que -100%.";
    return "Não foi possível concluir a comparação. Tente novamente.";
  }
  return "Não foi possível conectar ao serviço. Verifique sua conexão e tente novamente.";
}

export function GoalBudgetCapability(props: Props) {
  const { user, token, isLoading } = useAuth();
  if (props.sessionExpired) return <CapabilityEmpty>Sua sessão expirou. Entre novamente para distribuir o orçamento.</CapabilityEmpty>;
  if (isLoading) return <CapabilityEmpty>Carregando sessão…</CapabilityEmpty>;
  if (!user || !token) return <CapabilityEmpty>Entre na sua conta para distribuir o orçamento entre suas metas.</CapabilityEmpty>;
  return <GoalBudgetSession key={`${user.id}:${token}`} {...props} ownerId={user.id} />;
}

function GoalBudgetSession({ goals, loadingGoals, goalsError, onRefreshGoals, ownerId }: Props & { ownerId: string }) {
  const prefix = useId();
  const [form, setForm] = useState<GoalBudgetFormState>(createGoalBudgetForm);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [authFailed, setAuthFailed] = useState(false);
  const [mustRefresh, setMustRefresh] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [result, setResult] = useState<{ response: GoalBudgetPreviewResponse; snapshot: string; goalsVersion: string } | null>(null);
  const sequence = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const hasRun = useRef(false);
  const errorRef = useRef<HTMLParagraphElement>(null);
  const choices = [...new Map(goals.filter((goal) => goal.user_id === ownerId).map((goal) => [goal.id, goal])).values()];
  const goalsVersion = JSON.stringify(choices.map((goal) => [goal.id, goal.updated_at, goal.name, goal.status]));
  const snapshot = JSON.stringify(form);
  const missingSelection = form.allocations.some((allocation) => !choices.some((goal) => goal.id === allocation.goalId));
  const visibleResult = !loadingGoals && !goalsError && result?.snapshot === snapshot && result.goalsVersion === goalsVersion ? result.response : null;

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      sequence.current += 1;
      controller.current?.abort();
    };
  }, []);

  useEffect(() => {
    sequence.current += 1;
    controller.current?.abort();
    setLoading(false);
    setResult(null);
    setDirty(hasRun.current);
    if (!loadingGoals && !goalsError) setMustRefresh(false);
  }, [goalsVersion, loadingGoals, goalsError]);

  function edit(next: GoalBudgetFormState) {
    sequence.current += 1;
    controller.current?.abort();
    setForm(next);
    if (result || loading) setDirty(true);
    setLoading(false);
    setResult(null);
    setError(null);
    setFieldErrors({});
  }

  function toggleGoal(goalId: string) {
    const selected = form.allocations.some((allocation) => allocation.goalId === goalId);
    if (!selected && form.allocations.length >= 20) return;
    edit({ ...form, allocations: selected ? form.allocations.filter((allocation) => allocation.goalId !== goalId) : [...form.allocations, { goalId, A: "", B: "" }] });
  }

  function showError(message: string, field?: string) {
    setError(message);
    setFieldErrors(field ? { [field]: message } : {});
    // The error summary also provides a keyboard focus destination after submission.
    requestAnimationFrame(() => errorRef.current?.focus());
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading || authFailed || loadingGoals || goalsError || mustRefresh) return;
    if (missingSelection) {
      showError("A seleção contém metas que não estão mais disponíveis. Atualize a lista e revise a seleção.", "goals");
      return;
    }
    let request;
    try {
      request = toGoalBudgetRequest(form);
    } catch (caught) {
      if (caught instanceof GoalBudgetInputError) showError(caught.message, caught.field);
      return;
    }
    const currentSequence = ++sequence.current;
    hasRun.current = true;
    controller.current?.abort();
    const requestController = new AbortController();
    controller.current = requestController;
    setLoading(true);
    setDirty(false);
    setResult(null);
    setError(null);
    setFieldErrors({});
    try {
      const response = await previewGoalBudget(request, requestController.signal);
      if (!mounted.current || currentSequence !== sequence.current) return;
      if (JSON.stringify(response.results.map((item) => item.goal_id)) !== JSON.stringify(request.goal_ids)) throw new Error("Unexpected Goal selection");
      setResult({ response, snapshot, goalsVersion });
    } catch (caught) {
      if (!mounted.current || currentSequence !== sequence.current) return;
      if (caught instanceof AuthError) {
        setForm(createGoalBudgetForm());
        setResult(null);
        setAuthFailed(true);
      }
      if (caught instanceof APIRequestError && caught.status === 404) setMustRefresh(true);
      showError(errorMessage(caught));
    } finally {
      if (mounted.current && currentSequence === sequence.current) setLoading(false);
    }
  }

  function field(key: "monthlyBudget" | "horizonMonths" | "expectedReturnRate" | "asOfDate", label: string, placeholder?: string) {
    const message = fieldErrors[key];
    return <label className="flex min-w-0 flex-col gap-1.5 text-sm font-medium">
      {label}
      <input value={form[key]} onChange={(event) => edit({ ...form, [key]: event.target.value })} inputMode={key === "horizonMonths" ? "numeric" : key === "asOfDate" ? "text" : "decimal"} placeholder={placeholder} aria-invalid={!!message} aria-describedby={message ? `${prefix}-${key}-error` : undefined} className={fieldClass} />
      {message ? <span id={`${prefix}-${key}-error`} className="text-xs text-destructive">{message}</span> : null}
    </label>;
  }

  return <CapabilityPanel title="Distribuir orçamento">
    <p id={`${prefix}-premises`} className="text-xs leading-5 text-muted-foreground">Simulação com premissas escolhidas por você. Valores nominais, sem descontar inflação. Distribua o mesmo total mensal em A e B; o orçamento pode ser excedido.</p>
    <form onSubmit={submit} noValidate aria-describedby={`${prefix}-premises`} className="space-y-5">
      <fieldset disabled={authFailed} className="min-w-0 space-y-5">
        <fieldset aria-describedby={fieldErrors.goals ? `${prefix}-goals-error` : undefined} aria-invalid={!!fieldErrors.goals} className="space-y-2">
          <legend className="mb-2 text-sm font-medium">Metas ({form.allocations.length}/20)</legend>
          {loadingGoals ? <p role="status" className="text-sm text-muted-foreground">Carregando metas…</p> : goalsError ? <p role="alert" className="text-sm text-destructive">Não foi possível carregar as metas.</p> : choices.length === 0 ? <CapabilityEmpty>Nenhuma meta disponível. Cadastre uma meta para distribuir o orçamento.</CapabilityEmpty> : (
            <div className="grid gap-2 sm:grid-cols-2">
              {choices.map((goal) => {
                const checked = form.allocations.some((allocation) => allocation.goalId === goal.id);
                return <label key={goal.id} className={`flex min-h-11 min-w-0 cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm ${checked ? "border-primary/50 bg-primary/5" : "border-border"}`}>
                  <input type="checkbox" checked={checked} disabled={loadingGoals || (!checked && form.allocations.length >= 20)} onChange={() => toggleGoal(goal.id)} className="size-4 shrink-0 accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
                  <span className="min-w-0 break-words">{goal.name} <span className="text-xs text-muted-foreground">· {GOAL_STATUS_LABELS[goal.status]}</span></span>
                </label>;
              })}
            </div>
          )}
          {fieldErrors.goals ? <p id={`${prefix}-goals-error`} className="text-xs text-destructive">{fieldErrors.goals}</p> : null}
          {missingSelection ? <p role="alert" className="text-sm text-destructive">Uma meta selecionada não está disponível. Remova a seleção antes de comparar.</p> : null}
          {missingSelection ? <button type="button" onClick={() => edit({ ...form, allocations: [] })} className="min-h-11 rounded-lg border border-border px-3 text-sm focus-visible:ring-2 focus-visible:ring-ring">Limpar seleção</button> : null}
          <button type="button" disabled={loadingGoals} onClick={onRefreshGoals} className="min-h-11 rounded-lg px-2 text-xs text-muted-foreground underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Atualizar metas</button>
        </fieldset>
        <div className="grid gap-3 sm:grid-cols-3">
          {field("monthlyBudget", "Orçamento mensal", "Ex.: 1.500,00")}
          {field("horizonMonths", "Horizonte em meses", "Ex.: 120")}
          {field("expectedReturnRate", "Retorno hipotético anual (%)", "Ex.: 5")}
        </div>
        {form.allocations.length > 0 ? <div className="space-y-3">
          {form.allocations.map((allocation) => <fieldset key={allocation.goalId} className="min-w-0 rounded-xl border border-border p-3">
            <legend className="max-w-full break-words px-1 text-sm font-medium">{choices.find((goal) => goal.id === allocation.goalId)?.name ?? "Meta indisponível"}</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {(["A", "B"] as const).map((scenario) => {
                const key = `${allocation.goalId}-${scenario}`;
                return <label key={scenario} className="flex min-w-0 flex-col gap-1.5 text-sm">
                  Aporte mensal · cenário {scenario}
                  <input aria-label={`Aporte ${scenario} · ${choices.find((goal) => goal.id === allocation.goalId)?.name ?? "Meta indisponível"}`} value={allocation[scenario]} inputMode="decimal" placeholder="Ex.: 500,00" onChange={(event) => edit({ ...form, allocations: form.allocations.map((entry) => entry.goalId === allocation.goalId ? { ...entry, [scenario]: event.target.value } : entry) })} aria-invalid={!!fieldErrors[key]} aria-describedby={fieldErrors[key] ? `${prefix}-${key}-error` : undefined} className={fieldClass} />
                  {fieldErrors[key] ? <span id={`${prefix}-${key}-error`} className="text-xs text-destructive">{fieldErrors[key]}</span> : null}
                </label>;
              })}
            </div>
          </fieldset>)}
        </div> : null}
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer rounded focus-visible:ring-2 focus-visible:ring-ring">Data-base e convenções</summary>
          <div className="mt-3 max-w-sm space-y-3">{field("asOfDate", "Data-base (opcional)", "dd/mm/aaaa")}<p>Data-base de hoje ao executar, salvo alteração. Retorno efetivo anual; aportes no fim do mês. Horizonte independente da data-alvo cadastrada.</p></div>
        </details>
      </fieldset>
      {error ? <p ref={errorRef} tabIndex={-1} role="alert" className="rounded-xl border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive outline-none focus:ring-2 focus:ring-ring">{error}</p> : null}
      <div className="flex justify-end border-t border-border pt-4">
        <button type="submit" disabled={loading || loadingGoals || !!goalsError || authFailed || mustRefresh || missingSelection} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? <LoaderCircle aria-hidden="true" className="size-4 animate-spin motion-reduce:animate-none" /> : null}{loading ? "Comparando…" : "Comparar cenários"}
        </button>
      </div>
    </form>
    <CapabilityResultState hasResult={visibleResult !== null} loading={loading} dirty={false} loadingLabel="Comparando distribuições de orçamento" empty={<CapabilityEmpty>{dirty ? "Premissas ou metas alteradas. Compare novamente." : "Selecione as metas e preencha os aportes dos dois cenários para comparar."}</CapabilityEmpty>}>
      {visibleResult ? <GoalBudgetResults result={visibleResult} /> : null}
    </CapabilityResultState>
  </CapabilityPanel>;
}
