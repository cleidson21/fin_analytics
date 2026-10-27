"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { LoaderCircle, Target } from "lucide-react";

import {
  GOAL_STATUS_LABELS,
  GOAL_TYPE_LABELS,
  type Goal,
} from "@/app/goals/types";
import { ShowOnWealthHomeButton } from "@/app/wealth-intelligence/components/ShowOnWealthHomeButton";
import { useAuth } from "@/contexts/AuthContext";
import { APIRequestError, AuthError } from "@/lib/api";
import {
  getPlanningGoalContext,
  projectGoal,
  type GoalPlanningRequest,
  type GoalPlanningResponse,
  type PlanningGoalContext,
  type TargetValueBasis,
} from "@/lib/planning";
import { formatBRDate, formatBRLDecimalString } from "@/lib/planningLocale";

import {
  CapabilityEmpty,
  CapabilityError,
  CapabilityPanel,
  CapabilityResultState,
} from "./CapabilityPanel";
import { applyGoalContextPreset } from "./goalContext";
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

function contextLoadMessage(error: unknown): string {
  if (error instanceof APIRequestError && error.status === 404) {
    return "A meta não foi encontrada ou não está disponível para este usuário.";
  }
  if (error instanceof AuthError) {
    return "Sua sessão expirou. Entre novamente para carregar a meta.";
  }
  return "Não foi possível carregar os dados desta meta.";
}

function GoalContextSummary({ context }: { context: PlanningGoalContext }) {
  return (
    <section
      aria-label="Contexto autenticado da meta"
      className="rounded-xl border border-border bg-muted/30 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-foreground">{context.name}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {GOAL_TYPE_LABELS[context.goal_type]} · {GOAL_STATUS_LABELS[context.status]}
          </p>
        </div>
        <span className="rounded-full border border-violet-300/20 bg-violet-300/[0.07] px-2.5 py-1 text-[10px] font-semibold text-violet-700 dark:text-violet-300">
          Contexto da meta
        </span>
      </div>
      <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2 xl:grid-cols-4">
        <div><dt className="text-muted-foreground">Valor-alvo</dt><dd className="mt-0.5 font-medium text-foreground">{formatBRLDecimalString(context.target_amount)}</dd></div>
        <div><dt className="text-muted-foreground">Valor atual</dt><dd className="mt-0.5 font-medium text-foreground">{context.current_amount === null ? "Não informado" : formatBRLDecimalString(context.current_amount)}</dd></div>
        <div><dt className="text-muted-foreground">Aporte planejado</dt><dd className="mt-0.5 font-medium text-foreground">{context.planned_monthly_contribution === null ? "Não informado" : `${formatBRLDecimalString(context.planned_monthly_contribution)}/mês`}</dd></div>
        <div><dt className="text-muted-foreground">Data-alvo</dt><dd className="mt-0.5 font-medium text-foreground">{context.target_date === null ? "Não informada" : formatBRDate(context.target_date)}</dd></div>
      </dl>
      {context.current_amount === null ? (
        <p className="mt-3 text-xs leading-5 text-warning-foreground">
          Esta meta não tem valor atual cadastrado. Informe explicitamente o patrimônio da simulação ou escolha outra origem.
        </p>
      ) : null}
      <p className="mt-3 border-t border-border pt-2 text-xs leading-5 text-muted-foreground">
        O aporte é apenas um preset editável desta simulação. A data-alvo não altera automaticamente o horizonte.
      </p>
    </section>
  );
}

export function GoalPlanningCapability({
  goals,
  loadingGoals,
  initialGoalId = null,
}: {
  goals: Goal[];
  loadingGoals: boolean;
  initialGoalId?: string | null;
}) {
  const { user, token, isLoading: authLoading } = useAuth();
  const identityKey = user !== null && token !== null ? `${user.id}:${token}` : null;
  const [stateIdentity, setStateIdentity] = useState(identityKey);
  const [goalId, setGoalId] = useState("");
  const [context, setContext] = useState<PlanningGoalContext | null>(null);
  const [pendingGoalId, setPendingGoalId] = useState<string | null>(null);
  const [pendingContext, setPendingContext] = useState<PlanningGoalContext | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [input, setInput] = useState<PlanningInputState>(createPlanningInput);
  const [locallyEdited, setLocallyEdited] = useState(false);
  const [targetBasis, setTargetBasis] = useState<TargetValueBasis | "">("");
  const [result, setResult] = useState<GoalPlanningResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<PlanningInputField, string>>>({});
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const contextRequestSequence = useRef(0);
  const submissionSequence = useRef(0);
  const editVersion = useRef(0);
  const locallyEditedRef = useRef(false);
  const initialRequestKey = useRef<string | null>(null);
  const currentSnapshot = JSON.stringify({ goalId, input, targetBasis });

  const clearPrivateState = useCallback(() => {
    contextRequestSequence.current += 1;
    submissionSequence.current += 1;
    editVersion.current += 1;
    locallyEditedRef.current = false;
    setGoalId("");
    setContext(null);
    setPendingGoalId(null);
    setPendingContext(null);
    setContextLoading(false);
    setContextError(null);
    setInput(createPlanningInput());
    setLocallyEdited(false);
    setTargetBasis("");
    setResult(null);
    setLoading(false);
    setError(null);
    setFieldErrors({});
    setSubmittedSnapshot(null);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      contextRequestSequence.current += 1;
      submissionSequence.current += 1;
    };
  }, []);

  useEffect(() => {
    initialRequestKey.current = null;
    clearPrivateState();
    setStateIdentity(identityKey);
  }, [clearPrivateState, identityKey]);

  const applyContext = useCallback((nextContext: PlanningGoalContext) => {
    contextRequestSequence.current += 1;
    submissionSequence.current += 1;
    editVersion.current += 1;
    locallyEditedRef.current = false;
    setInput((current) => applyGoalContextPreset(current, nextContext));
    setGoalId(nextContext.goal_id);
    setContext(nextContext);
    setPendingGoalId(null);
    setPendingContext(null);
    setContextLoading(false);
    setContextError(null);
    setLocallyEdited(false);
    setResult(null);
    setLoading(false);
    setError(null);
    setFieldErrors({});
    setSubmittedSnapshot(null);
  }, []);

  const loadContext = useCallback(async (
    nextGoalId: string,
    preferPending: boolean,
  ) => {
    if (identityKey === null || authLoading) return;

    const sequence = ++contextRequestSequence.current;
    const requestIdentity = identityKey;
    const requestEditVersion = editVersion.current;
    setContextLoading(true);
    setContextError(null);
    if (preferPending) {
      setPendingGoalId(nextGoalId);
      setPendingContext(null);
    }

    try {
      const nextContext = await getPlanningGoalContext(nextGoalId);
      if (
        !mountedRef.current ||
        sequence !== contextRequestSequence.current ||
        requestIdentity !== identityKey
      ) return;
      if (nextContext.goal_id.toLowerCase() !== nextGoalId.toLowerCase()) {
        throw new Error("Goal context identity mismatch");
      }

      const editedDuringRequest = requestEditVersion !== editVersion.current;
      if (preferPending || editedDuringRequest || locallyEditedRef.current) {
        setPendingGoalId(nextGoalId);
        setPendingContext(nextContext);
      } else {
        applyContext(nextContext);
      }
    } catch (caught) {
      if (!mountedRef.current || sequence !== contextRequestSequence.current) return;
      if (caught instanceof AuthError) clearPrivateState();
      setContextError(contextLoadMessage(caught));
      setPendingGoalId(null);
      setPendingContext(null);
    } finally {
      if (mountedRef.current && sequence === contextRequestSequence.current) {
        setContextLoading(false);
      }
    }
  }, [applyContext, authLoading, clearPrivateState, identityKey]);

  useEffect(() => {
    if (initialGoalId === null || identityKey === null || authLoading) return;
    const requestKey = `${identityKey}:${initialGoalId}`;
    if (initialRequestKey.current === requestKey) return;
    initialRequestKey.current = requestKey;
    void loadContext(initialGoalId, false);
  }, [authLoading, identityKey, initialGoalId, loadContext]);

  if (stateIdentity !== identityKey) {
    return (
      <CapabilityPanel title="Metas existentes">
        <CapabilityEmpty>Atualizando o contexto autenticadoâ€¦</CapabilityEmpty>
      </CapabilityPanel>
    );
  }

  function clearFieldError(field: PlanningInputField) {
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function markEdited() {
    editVersion.current += 1;
    locallyEditedRef.current = true;
    setLocallyEdited(true);
  }

  function changeInput(nextInput: PlanningInputState) {
    setInput(nextInput);
    markEdited();
  }

  function changeTargetBasis(next: TargetValueBasis | "") {
    setTargetBasis(next);
    markEdited();
  }

  function selectGoal(nextGoalId: string) {
    if (nextGoalId === "" || nextGoalId === goalId) return;
    void loadContext(nextGoalId, locallyEditedRef.current);
  }

  function cancelPendingGoal() {
    contextRequestSequence.current += 1;
    setPendingGoalId(null);
    setPendingContext(null);
    setContextLoading(false);
    setContextError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!goalId || pendingGoalId !== null || contextLoading || identityKey === null) return;
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

    const sequence = ++submissionSequence.current;
    const submittedIdentity = identityKey;
    const submittedGoalId = goalId;
    setLoading(true);
    try {
      const response = await projectGoal(submittedGoalId, request);
      if (!response) throw new Error("Goal planning response is unavailable");
      if (
        !mountedRef.current ||
        sequence !== submissionSequence.current ||
        submittedIdentity !== identityKey
      ) return;
      setResult(response);
      setSubmittedSnapshot(currentSnapshot);
    } catch (caught) {
      if (!mountedRef.current || sequence !== submissionSequence.current) return;
      if (caught instanceof AuthError) clearPrivateState();
      setError(
        portfolioSourceUnavailableMessage(input) ??
        "Não foi possível analisar esta meta. Verifique a meta e as premissas informadas.",
      );
    } finally {
      if (mountedRef.current && sequence === submissionSequence.current) {
        setLoading(false);
      }
    }
  }

  const pendingLabel = pendingContext?.name
    ?? goals.find((goal) => goal.id === pendingGoalId && goal.user_id === user?.id)?.name
    ?? "a nova meta";
  const visibleGoals = identityKey === null
    ? []
    : goals.filter((goal) => goal.user_id === user?.id);
  const selectedGoalVisible = visibleGoals.some((goal) => goal.id === goalId);

  return (
    <CapabilityPanel title="Metas existentes">
      <form className="space-y-5" onSubmit={handleSubmit}>
        <label className="flex max-w-xl flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Meta
          <select
            required
            aria-label="Meta"
            value={goalId}
            onChange={(event) => selectGoal(event.target.value)}
            disabled={loadingGoals || loading || authLoading || identityKey === null}
            className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-400/10 disabled:opacity-60"
          >
            <option value="">{loadingGoals ? "Carregando metas..." : "Selecione uma meta"}</option>
            {goalId !== "" && !selectedGoalVisible ? (
              <option value={goalId}>{context?.name ?? "Meta selecionada"}</option>
            ) : null}
            {visibleGoals.map((goal) => (
              <option key={goal.id} value={goal.id}>
                {goal.name} · {GOAL_TYPE_LABELS[goal.goal_type]} · {GOAL_STATUS_LABELS[goal.status]}
              </option>
            ))}
          </select>
        </label>

        {contextLoading ? (
          <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground">
            <LoaderCircle aria-hidden="true" className="size-4 animate-spin motion-reduce:animate-none" />
            Carregando contexto autenticado da meta…
          </p>
        ) : null}
        {contextError ? <CapabilityError message={contextError} onDismiss={() => setContextError(null)} /> : null}

        {pendingGoalId !== null && pendingContext !== null ? (
          <section role="alert" className="rounded-xl border border-amber-300/25 bg-amber-300/[0.07] p-3 text-sm">
            <p className="font-semibold text-warning-foreground">Aplicar dados de {pendingLabel}?</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              O formulário atual foi editado. Nada será substituído até você confirmar.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => applyContext(pendingContext)}
                className="rounded-lg bg-amber-300 px-3 py-2 text-xs font-semibold text-zinc-950 hover:bg-amber-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300/50"
              >
                Aplicar dados desta meta
              </button>
              <button
                type="button"
                onClick={cancelPendingGoal}
                className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Cancelar
              </button>
            </div>
          </section>
        ) : null}

        {context ? <GoalContextSummary context={context} /> : null}
        <PlanningInputs
          value={input}
          onChange={changeInput}
          goals={visibleGoals}
          idPrefix="goal-planning"
          goalSourceMode="path"
          fieldErrors={fieldErrors}
          onFieldChange={clearFieldError}
        />
        <label className="flex max-w-xl flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Base do alvo da meta (opcional)
          <select
            value={targetBasis}
            onChange={(event) => changeTargetBasis(event.target.value as TargetValueBasis | "")}
            className="min-h-10 rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-400/10"
          >
            <option value="">Não informar</option>
            <option value="NOMINAL">Nominal</option>
            <option value="REAL">Real</option>
          </select>
        </label>
        {locallyEdited ? (
          <p className="text-xs text-muted-foreground">
            Ajustes locais afetam somente esta simulação e não alteram a meta cadastrada.
          </p>
        ) : null}
        <div className="flex justify-end border-t border-border pt-4">
          <button
            type="submit"
            disabled={
              loading ||
              loadingGoals ||
              contextLoading ||
              pendingGoalId !== null ||
              goalId === "" ||
              identityKey === null
            }
            className="inline-flex min-h-10 min-w-36 items-center justify-center gap-2 rounded-xl bg-violet-300 px-4 text-sm font-semibold text-zinc-950 transition-colors hover:bg-violet-200 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <Target aria-hidden="true" size={16} />}
            {loading ? "Analisando..." : "Analisar meta"}
          </button>
        </div>
      </form>
      {error ? <CapabilityError message={error} onDismiss={() => setError(null)} /> : null}
      <CapabilityResultState
        hasResult={result !== null}
        loading={loading}
        dirty={result !== null && submittedSnapshot !== currentSnapshot}
        loadingLabel="Analisando meta existente"
        empty={<CapabilityEmpty>Escolha uma meta, revise as premissas e execute a análise.</CapabilityEmpty>}
        action={result && error === null ? <ShowOnWealthHomeButton analysis={{ domain: "PLANNING", kind: "GOAL", result }} /> : null}
      >
        {result ? <GoalPlanningResult result={result} /> : null}
      </CapabilityResultState>
    </CapabilityPanel>
  );
}
