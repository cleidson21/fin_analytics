"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Briefcase,
  Building2,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Eye,
  FileText,
  History,
  LoaderCircle,
  Mail,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
  User,
  X,
} from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";
import { useAuth } from "@/contexts/AuthContext";
import type { ISODateString } from "@/lib/planning";
import { formatBRDate, formatBRLDecimalString, formatReferenceMonth } from "@/lib/planningLocale";
import {
  buildDeclaredIncomePatch,
  candidateActionError,
  candidateLoadErrorMessage,
  clearDeclaredIncomePatch,
  confirmIncomeCandidate,
  formatBackendUTCTimestamp,
  formatDeclaredIncomeInput,
  getCandidatePresentation,
  getIncomeCandidates,
  loadProfileExperience,
  patchProfileContext,
  profileLoadErrorMessage,
  profileSaveErrorMessage,
  readAndSanitizeLocalProfile,
  rejectIncomeCandidate,
  resetIncomeCandidateDecision,
  writeLocalProfile,
  type IncomeCandidate,
  type IncomeCandidateCollection,
  type LocalProfileFields,
  type ProfileDeclaredContextResponse,
} from "@/lib/profileContext";

const TAX_REGIMES = [
  { value: "", label: "Selecione..." },
  { value: "CLT", label: "CLT — Empregado" },
  { value: "MEI", label: "MEI — Microempreendedor Individual" },
  { value: "PJ", label: "PJ — Pessoa Jurídica" },
  { value: "AUTONOMO", label: "Autônomo / Freelancer" },
  { value: "SERVIDOR", label: "Servidor público" },
  { value: "APOSENTADO", label: "Aposentado / Pensionista" },
];

type CandidateAction = "confirm" | "reject" | "reset";

interface CandidateFeedback {
  message: string;
  tone: "SUCCESS" | "WARNING" | "ERROR";
}

function SectionCard({
  title,
  subtitle,
  icon: Icon,
  iconColor,
  children,
}: {
  title: string;
  subtitle: string;
  icon: React.ElementType;
  iconColor: string;
  children: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02]">
      <div className="flex items-start gap-3 border-b border-white/[0.06] px-5 py-4 sm:px-6">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${iconColor}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>
          <p className="mt-0.5 text-xs leading-5 text-zinc-500">{subtitle}</p>
        </div>
      </div>
      <div className="p-5 sm:p-6">{children}</div>
    </section>
  );
}

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-zinc-500"
    >
      {children}
    </label>
  );
}

function TextInput({
  id,
  icon: Icon,
  value,
  onChange,
  placeholder,
  readOnly = false,
  inputMode,
  ariaDescribedBy,
}: {
  id: string;
  icon: React.ElementType;
  value: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
  ariaDescribedBy?: string;
}) {
  return (
    <div className="relative">
      <Icon
        className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-600"
        aria-hidden="true"
      />
      <input
        id={id}
        type="text"
        inputMode={inputMode}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        aria-describedby={ariaDescribedBy}
        className={`w-full rounded-xl border py-2.5 pl-10 pr-4 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-emerald-400/30 ${
          readOnly
            ? "cursor-not-allowed border-white/5 bg-white/[0.02] text-zinc-500"
            : "border-white/10 bg-white/[0.04] text-zinc-100 placeholder-zinc-600 focus:border-emerald-500/40 focus:bg-white/[0.06]"
        }`}
      />
    </div>
  );
}

function formatOptionalDate(value: ISODateString | null): string | null {
  if (!value) return null;
  try {
    return formatBRDate(value);
  } catch {
    return null;
  }
}

function formatOptionalMoney(value: string | null): string | null {
  if (!value) return null;
  try {
    return formatBRLDecimalString(value);
  } catch {
    return null;
  }
}

function IncomeCandidateCard({
  candidate,
  pending,
  actionsDisabled,
  onAction,
}: {
  candidate: IncomeCandidate;
  pending: boolean;
  actionsDisabled: boolean;
  onAction: (candidate: IncomeCandidate, action: CandidateAction) => void;
}) {
  const state = getCandidatePresentation(candidate);
  const isStale = !state.showCurrentEvidence;
  const stateClassName = {
    INFO: "bg-sky-500/10 text-sky-300 ring-sky-400/20",
    SUCCESS: "bg-emerald-500/10 text-emerald-300 ring-emerald-400/20",
    NEUTRAL: "bg-zinc-500/10 text-zinc-300 ring-white/10",
    WARNING: "bg-amber-500/10 text-amber-300 ring-amber-400/20",
  }[state.tone];
  const typicalAmount = isStale ? null : formatOptionalMoney(candidate.typical_received_amount);
  const latestAmount = isStale ? null : formatOptionalMoney(candidate.latest_amount);
  const rangeMinimum = isStale ? null : formatOptionalMoney(candidate.minimum_received_amount);
  const rangeMaximum = isStale ? null : formatOptionalMoney(candidate.maximum_received_amount);
  const firstDate = isStale ? null : formatOptionalDate(candidate.first_occurrence_date);
  const latestDate = isStale ? null : formatOptionalDate(candidate.latest_occurrence_date);
  const decisionDate = formatBackendUTCTimestamp(
    candidate.decision_updated_at ?? candidate.decided_at,
  );

  return (
    <article className="rounded-2xl border border-white/[0.07] bg-black/10 p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <span
            className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${stateClassName}`}
          >
            {state.label}
          </span>
          <p className="max-w-2xl text-sm leading-6 text-zinc-300">{state.detail}</p>
        </div>
        {decisionDate ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-zinc-500">
            <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
            Decisão em {decisionDate}
          </span>
        ) : null}
      </div>

      {candidate.risk_flags.includes("TRANSFER_AMBIGUITY") ? (
        <div className="mt-4 flex gap-2 rounded-xl border border-amber-400/20 bg-amber-500/[0.06] p-3 text-sm text-amber-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <p>Esta movimentação pode representar uma transferência. Revise antes de confirmar.</p>
        </div>
      ) : null}

      {!isStale ? (
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Meses observados</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {candidate.distinct_month_count ?? "Indisponível"}
            </dd>
          </div>
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Ocorrências no período</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {candidate.occurrence_count ?? "Indisponível"}
            </dd>
          </div>
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Valor típico observado</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {typicalAmount ?? "Indisponível"}
            </dd>
          </div>
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Última ocorrência</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {latestDate ?? "Indisponível"}
              {latestAmount ? ` · ${latestAmount}` : ""}
            </dd>
          </div>
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Primeira ocorrência</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {firstDate ?? "Indisponível"}
            </dd>
          </div>
          <div className="rounded-xl bg-white/[0.025] p-3">
            <dt className="text-xs text-zinc-500">Faixa observada</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-200">
              {rangeMinimum && rangeMaximum
                ? `${rangeMinimum} a ${rangeMaximum}`
                : "Indisponível"}
            </dd>
          </div>
        </dl>
      ) : (
        <div className="mt-4 rounded-xl bg-white/[0.025] p-3 text-sm text-zinc-400">
          Valores monetários anteriores não são apresentados como evidência atual.
        </div>
      )}

      {!isStale && candidate.observed_months.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2" aria-label="Meses com ocorrência observada">
          {candidate.observed_months.map((month) => (
            <span
              key={month}
              className="rounded-lg bg-white/[0.04] px-2 py-1 text-xs text-zinc-400 ring-1 ring-inset ring-white/[0.06]"
            >
              {formatReferenceMonth(month)}
            </span>
          ))}
          {candidate.current_month_is_partial ? (
            <span className="rounded-lg bg-amber-500/[0.06] px-2 py-1 text-xs text-amber-300 ring-1 ring-inset ring-amber-400/15">
              Mês atual parcial
            </span>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 flex flex-col gap-2 border-t border-white/[0.06] pt-4 sm:flex-row sm:flex-wrap">
        {state.allowDecision ? (
          <>
            <button
              type="button"
              disabled={actionsDisabled || !candidate.evidence_fingerprint}
              onClick={() => onAction(candidate, "confirm")}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Confirmar como renda recorrente
            </button>
            <button
              type="button"
              disabled={actionsDisabled || !candidate.evidence_fingerprint}
              onClick={() => onAction(candidate, "reject")}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-semibold text-zinc-300 transition-colors hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400/50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <X className="h-4 w-4" aria-hidden="true" />
              Não é minha renda recorrente
            </button>
          </>
        ) : null}
        {state.allowReset ? (
          <button
            type="button"
            disabled={actionsDisabled}
            onClick={() => onAction(candidate, "reset")}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-semibold text-zinc-300 transition-colors hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400/50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <History className="h-4 w-4" />}
            Remover decisão
          </button>
        ) : null}
      </div>
    </article>
  );
}

function LoadingBlock({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-sm text-zinc-400">
      <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default function ProfilePage() {
  const { user, isLoading: authLoading } = useAuth();
  const [localProfile, setLocalProfile] = useState<LocalProfileFields>({
    display_name: "",
    occupation: "",
    company: "",
    tax_regime: "",
  });
  const [localSaved, setLocalSaved] = useState(false);
  const [profileContext, setProfileContext] = useState<ProfileDeclaredContextResponse | null>(null);
  const [candidateCollection, setCandidateCollection] = useState<IncomeCandidateCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileLoadError, setProfileLoadError] = useState<string | null>(null);
  const [candidateLoadError, setCandidateLoadError] = useState<string | null>(null);
  const [incomeInput, setIncomeInput] = useState("");
  const [incomeAsOfDate, setIncomeAsOfDate] = useState("");
  const [incomeBaseline, setIncomeBaseline] = useState({ value: "", asOfDate: "" });
  const [incomeError, setIncomeError] = useState<string | null>(null);
  const [incomeSuccess, setIncomeSuccess] = useState<string | null>(null);
  const [savingIncome, setSavingIncome] = useState(false);
  const [confirmingClear, setConfirmingClear] = useState(false);
  const [pendingCandidateId, setPendingCandidateId] = useState<string | null>(null);
  const candidateInteractionLockRef = useRef(false);
  const [candidateRetryPending, setCandidateRetryPending] = useState(false);
  const [candidateFeedback, setCandidateFeedback] = useState<CandidateFeedback | null>(null);

  const applyProfileContext = useCallback((context: ProfileDeclaredContextResponse) => {
    const value = formatDeclaredIncomeInput(context.declared_monthly_gross_income);
    const asOfDate = context.income_as_of_date ?? "";
    setProfileContext(context);
    setIncomeInput(value);
    setIncomeAsOfDate(asOfDate);
    setIncomeBaseline({ value, asOfDate });
  }, []);

  const loadExperience = useCallback(async () => {
    setLoading(true);
    setProfileLoadError(null);
    setCandidateLoadError(null);
    const result = await loadProfileExperience();
    if (result.profile.ok) {
      applyProfileContext(result.profile.value);
    } else {
      setProfileLoadError(profileLoadErrorMessage(result.profile.error));
    }
    if (result.candidates.ok) {
      setCandidateCollection(result.candidates.value);
    } else {
      setCandidateLoadError(candidateLoadErrorMessage(result.candidates.error));
    }
    setLoading(false);
  }, [applyProfileContext]);

  useEffect(() => {
    const persisted = readAndSanitizeLocalProfile(window.localStorage);
    setLocalProfile({
      ...persisted,
      display_name: persisted.display_name || user?.name || "",
    });
  }, [user?.name]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      setProfileLoadError("Autenticação necessária para carregar o contexto financeiro.");
      setCandidateLoadError("Autenticação necessária para revisar fontes recorrentes.");
      return;
    }
    void loadExperience();
  }, [authLoading, loadExperience, user]);

  const identityName = profileContext?.name ?? user?.name ?? "Usuário";
  const identityEmail = profileContext?.email ?? user?.email ?? "";
  const displayName = localProfile.display_name || identityName;
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "U";
  const incomeDirty =
    incomeInput !== incomeBaseline.value || incomeAsOfDate !== incomeBaseline.asOfDate;
  const canSaveIncome = incomeDirty && incomeInput.trim() !== "" && !savingIncome;
  const provenanceDate = formatBackendUTCTimestamp(profileContext?.updated_at ?? null);
  const declaredDate = formatBackendUTCTimestamp(profileContext?.declared_at ?? null);
  const referenceDate = formatOptionalDate(profileContext?.income_as_of_date ?? null);
  const candidates = candidateCollection?.candidates ?? [];

  function updateLocalProfile(field: keyof LocalProfileFields, value: string) {
    setLocalSaved(false);
    setLocalProfile((current) => ({ ...current, [field]: value }));
  }

  function saveLocalProfile() {
    writeLocalProfile(window.localStorage, localProfile);
    setLocalSaved(true);
  }

  async function saveDeclaredIncome() {
    const validation = buildDeclaredIncomePatch(incomeInput, incomeAsOfDate);
    if (!validation.ok) {
      setIncomeError(validation.message);
      setIncomeSuccess(null);
      return;
    }
    setSavingIncome(true);
    setIncomeError(null);
    setIncomeSuccess(null);
    setConfirmingClear(false);
    try {
      const context = await patchProfileContext(validation.payload);
      applyProfileContext(context);
      setIncomeSuccess("Contexto declarado salvo pelo servidor.");
    } catch (error) {
      setIncomeError(profileSaveErrorMessage(error));
    } finally {
      setSavingIncome(false);
    }
  }

  async function clearDeclaredIncome() {
    setSavingIncome(true);
    setIncomeError(null);
    setIncomeSuccess(null);
    try {
      const context = await patchProfileContext(clearDeclaredIncomePatch());
      applyProfileContext(context);
      setIncomeSuccess("Renda mensal bruta declarada removida.");
    } catch (error) {
      setIncomeError(profileSaveErrorMessage(error));
    } finally {
      setSavingIncome(false);
      setConfirmingClear(false);
    }
  }

  async function refreshCandidates(): Promise<boolean> {
    try {
      const result = await getIncomeCandidates();
      setCandidateCollection(result);
      setCandidateLoadError(null);
      return true;
    } catch (error) {
      setCandidateLoadError(candidateLoadErrorMessage(error));
      return false;
    }
  }

  async function retryExperience() {
    if (candidateInteractionLockRef.current) return;
    candidateInteractionLockRef.current = true;
    setCandidateRetryPending(true);
    try {
      await loadExperience();
    } finally {
      setCandidateRetryPending(false);
      candidateInteractionLockRef.current = false;
    }
  }

  async function retryCandidates() {
    if (candidateInteractionLockRef.current) return;
    candidateInteractionLockRef.current = true;
    setCandidateRetryPending(true);
    try {
      await refreshCandidates();
    } finally {
      setCandidateRetryPending(false);
      candidateInteractionLockRef.current = false;
    }
  }

  async function handleCandidateAction(candidate: IncomeCandidate, action: CandidateAction) {
    if (candidateInteractionLockRef.current) return;
    candidateInteractionLockRef.current = true;
    setPendingCandidateId(candidate.candidate_id);
    setCandidateFeedback(null);
    try {
      if (action === "confirm" || action === "reject") {
        if (!candidate.evidence_fingerprint) {
          throw new Error("Candidate evidence is unavailable.");
        }
        if (action === "confirm") {
          await confirmIncomeCandidate(candidate.candidate_id, candidate.evidence_fingerprint);
        } else {
          await rejectIncomeCandidate(candidate.candidate_id, candidate.evidence_fingerprint);
        }
      } else {
        await resetIncomeCandidateDecision(candidate.candidate_id);
      }
      const refreshed = await refreshCandidates();
      const successMessage =
        action === "reset"
          ? "Decisão removida."
          : action === "confirm"
            ? "Fonte confirmada como renda recorrente."
            : "Fonte rejeitada como renda recorrente.";
      setCandidateFeedback({
        message: refreshed
          ? `${successMessage} A lista foi atualizada.`
          : `${successMessage} Não foi possível atualizar a lista agora. Use Recarregar evidências.`,
        tone: refreshed ? "SUCCESS" : "WARNING",
      });
    } catch (error) {
      const state = candidateActionError(error);
      if (!state.refresh) {
        setCandidateFeedback({ message: state.message, tone: "ERROR" });
      } else {
        const refreshed = await refreshCandidates();
        const refreshMessage = refreshed
          ? state.kind === "CONFLICT"
            ? "Os dados foram atualizados para uma nova revisão."
            : "A lista foi atualizada."
          : "Não foi possível atualizar a lista agora. Use Recarregar evidências.";
        setCandidateFeedback({
          message: `${state.message} ${refreshMessage}`,
          tone: refreshed ? "WARNING" : "ERROR",
        });
      }
    } finally {
      candidateInteractionLockRef.current = false;
      setPendingCandidateId(null);
    }
  }

  const declarationMetadata = useMemo(
    () => [
      "Informado por você",
      "Mensal · bruto · BRL",
      referenceDate ? `Referência ${referenceDate}` : null,
      provenanceDate ? `Atualizado em ${provenanceDate}` : null,
    ].filter((item): item is string => item !== null),
    [provenanceDate, referenceDate],
  );

  return (
    <PageLayout
      title="Perfil"
      subtitle="Identidade, contexto declarado e decisões sobre evidências recorrentes."
    >
      <div className="mx-auto max-w-4xl space-y-6 pb-12">
        <div className="flex flex-col gap-5 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 sm:flex-row sm:items-center sm:p-6">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 ring-1 ring-inset ring-emerald-400/20">
            <span className="text-2xl font-bold text-emerald-300">{initials}</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xl font-semibold text-zinc-100">{identityName}</p>
            <p className="mt-0.5 truncate text-sm text-zinc-500">{identityEmail}</p>
            <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-inset ring-emerald-400/20">
              <ShieldCheck className="h-3 w-3" aria-hidden="true" />
              Identidade autenticada
            </span>
          </div>
        </div>

        <SectionCard
          title="Contexto financeiro declarado"
          subtitle="O que você informou explicitamente ao FINANALYTICS. Não é renda observada nem capacidade de investir."
          icon={CircleDollarSign}
          iconColor="bg-emerald-500/15 text-emerald-400"
        >
          {loading && !profileContext && !profileLoadError ? (
            <LoadingBlock label="Carregando o contexto financeiro declarado..." />
          ) : null}

          {profileLoadError ? (
            <div role="alert" className="rounded-xl border border-red-400/20 bg-red-500/[0.06] p-4">
              <p className="text-sm text-red-200">{profileLoadError}</p>
              <button
                type="button"
                disabled={pendingCandidateId !== null || candidateRetryPending}
                onClick={() => void retryExperience()}
                className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-red-100 underline decoration-red-300/40 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300/40"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Tentar novamente
              </button>
            </div>
          ) : null}

          {profileContext ? (
            <div className="space-y-5">
              {profileContext.declared_monthly_gross_income === null ? (
                <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.015] p-4">
                  <p className="text-sm font-medium text-zinc-200">
                    Nenhuma renda mensal bruta foi informada.
                  </p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    Você pode adicionar uma declaração abaixo. Nenhum valor será inferido de transações.
                  </p>
                </div>
              ) : (
                <div className="rounded-xl border border-emerald-400/15 bg-emerald-500/[0.04] p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                    Renda mensal bruta declarada
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-zinc-100">
                    {formatOptionalMoney(profileContext.declared_monthly_gross_income)}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {declarationMetadata.map((item) => (
                      <span
                        key={item}
                        className="rounded-lg bg-black/10 px-2 py-1 text-xs text-zinc-400 ring-1 ring-inset ring-white/[0.06]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                  {declaredDate ? (
                    <p className="mt-2 text-xs text-zinc-500">Declaração registrada em {declaredDate}.</p>
                  ) : null}
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel htmlFor="declared-income">Valor mensal bruto</FieldLabel>
                  <TextInput
                    id="declared-income"
                    icon={CircleDollarSign}
                    value={incomeInput}
                    onChange={(value) => {
                      setIncomeInput(value);
                      setIncomeError(null);
                      setIncomeSuccess(null);
                      setConfirmingClear(false);
                    }}
                    placeholder="R$ 5.500,00"
                    inputMode="decimal"
                    ariaDescribedBy="declared-income-help declared-income-message"
                  />
                  <p id="declared-income-help" className="mt-1.5 text-xs leading-5 text-zinc-500">
                    Campo declarado, mensal, bruto e em BRL. Salvo somente após sua ação.
                  </p>
                </div>
                <div>
                  <FieldLabel htmlFor="income-as-of-date">Data de referência do valor informado</FieldLabel>
                  <div className="relative">
                    <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-600" />
                    <input
                      id="income-as-of-date"
                      type="date"
                      value={incomeAsOfDate}
                      onChange={(event) => {
                        setIncomeAsOfDate(event.target.value);
                        setIncomeError(null);
                        setIncomeSuccess(null);
                      }}
                      className="w-full rounded-xl border border-white/10 bg-white/[0.04] py-2.5 pl-10 pr-4 text-sm text-zinc-100 outline-none transition-colors focus:border-emerald-500/40 focus-visible:ring-2 focus-visible:ring-emerald-400/30"
                    />
                  </div>
                  <p className="mt-1.5 text-xs leading-5 text-zinc-500">
                    Opcional. A ausência de data não será substituída pela data atual.
                  </p>
                </div>
              </div>

              {incomeInput.trim() === "" && profileContext.declared_monthly_gross_income !== null ? (
                <p className="text-xs text-amber-300">
                  Para remover a declaração, use a ação explícita “Limpar valor”.
                </p>
              ) : null}
              {incomeError ? (
                <p id="declared-income-message" role="alert" className="text-sm text-red-300">
                  {incomeError}
                </p>
              ) : null}
              {incomeSuccess ? (
                <p id="declared-income-message" role="status" aria-live="polite" className="text-sm text-emerald-300">
                  {incomeSuccess}
                </p>
              ) : null}

              {confirmingClear ? (
                <div className="rounded-xl border border-amber-400/20 bg-amber-500/[0.05] p-4">
                  <p className="text-sm font-medium text-amber-100">Remover a renda declarada?</p>
                  <p className="mt-1 text-xs leading-5 text-amber-200/70">
                    Isso remove somente esta declaração. Transações e evidências observadas não serão alteradas.
                  </p>
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <button
                      type="button"
                      disabled={savingIncome}
                      onClick={() => void clearDeclaredIncome()}
                      className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-amber-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50"
                    >
                      {savingIncome ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      Confirmar limpeza
                    </button>
                    <button
                      type="button"
                      disabled={savingIncome}
                      onClick={() => setConfirmingClear(false)}
                      className="rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-zinc-300 hover:bg-white/[0.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400/50"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : null}

              <div className="flex flex-col gap-2 border-t border-white/[0.06] pt-4 sm:flex-row sm:justify-end">
                {profileContext.declared_monthly_gross_income !== null && !confirmingClear ? (
                  <button
                    type="button"
                    disabled={savingIncome}
                    onClick={() => setConfirmingClear(true)}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-semibold text-zinc-300 hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400/50 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    Limpar valor
                  </button>
                ) : null}
                <button
                  type="button"
                  disabled={!canSaveIncome}
                  onClick={() => void saveDeclaredIncome()}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 transition-colors hover:bg-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {savingIncome ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  {savingIncome ? "Salvando..." : "Salvar declaração"}
                </button>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Fontes de renda recorrente observadas"
          subtitle="Evidências encontradas em transações governadas. Uma detecção só vira renda recorrente após sua decisão."
          icon={Eye}
          iconColor="bg-sky-500/15 text-sky-400"
        >
          {loading && !candidateCollection && !candidateLoadError ? (
            <LoadingBlock label="Carregando evidências recorrentes..." />
          ) : null}
          {candidateLoadError ? (
            <div role="alert" className="rounded-xl border border-red-400/20 bg-red-500/[0.06] p-4">
              <p className="text-sm text-red-200">{candidateLoadError}</p>
              <button
                type="button"
                disabled={pendingCandidateId !== null || candidateRetryPending}
                onClick={() => void retryCandidates()}
                className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-red-100 underline decoration-red-300/40 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300/40"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Recarregar evidências
              </button>
            </div>
          ) : null}
          {candidateFeedback ? (
            <p
              role={candidateFeedback.tone === "ERROR" ? "alert" : "status"}
              aria-live="polite"
              className={`mb-4 rounded-xl p-3 text-sm ${
                candidateFeedback.tone === "SUCCESS"
                  ? "bg-emerald-500/[0.06] text-emerald-200"
                  : candidateFeedback.tone === "WARNING"
                    ? "bg-amber-500/[0.06] text-amber-200"
                    : "bg-red-500/[0.06] text-red-200"
              }`}
            >
              {candidateFeedback.message}
            </p>
          ) : null}
          {candidateCollection && candidates.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.015] p-4">
              <p className="text-sm font-medium text-zinc-200">Nenhuma fonte está disponível para revisão.</p>
              <p className="mt-1 text-xs leading-5 text-zinc-500">
                Isso não significa renda zero; apenas não há evidência recorrente elegível agora.
              </p>
            </div>
          ) : null}
          {candidateCollection && candidates.length > 0 ? (
            <div className="space-y-4">
              <div className="flex flex-col gap-2 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
                <span>Fonte: transações governadas · revisão humana obrigatória</span>
                <span>Referência da leitura: {formatBRDate(candidateCollection.as_of_date)}</span>
              </div>
              {candidates.map((candidate) => (
                <IncomeCandidateCard
                  key={candidate.candidate_id}
                  candidate={candidate}
                  pending={pendingCandidateId === candidate.candidate_id}
                  actionsDisabled={pendingCandidateId !== null || candidateRetryPending}
                  onAction={(item, action) => void handleCandidateAction(item, action)}
                />
              ))}
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Informações locais do perfil"
          subtitle="Preferências de apresentação e contexto profissional mantidas somente neste navegador. Não participam de cálculos."
          icon={Briefcase}
          iconColor="bg-violet-500/15 text-violet-400"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <FieldLabel htmlFor="local-display-name">Nome de exibição local</FieldLabel>
              <TextInput
                id="local-display-name"
                icon={User}
                value={localProfile.display_name}
                onChange={(value) => updateLocalProfile("display_name", value)}
                placeholder={identityName}
              />
            </div>
            <div>
              <FieldLabel htmlFor="local-occupation">Ocupação / cargo</FieldLabel>
              <TextInput
                id="local-occupation"
                icon={Briefcase}
                value={localProfile.occupation}
                onChange={(value) => updateLocalProfile("occupation", value)}
                placeholder="Contexto local opcional"
              />
            </div>
            <div>
              <FieldLabel htmlFor="local-company">Empresa / empregador</FieldLabel>
              <TextInput
                id="local-company"
                icon={Building2}
                value={localProfile.company}
                onChange={(value) => updateLocalProfile("company", value)}
                placeholder="Contexto local opcional"
              />
            </div>
            <div className="sm:col-span-2">
              <FieldLabel htmlFor="local-tax-regime">Regime tributário</FieldLabel>
              <div className="relative">
                <FileText className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-600" />
                <select
                  id="local-tax-regime"
                  value={localProfile.tax_regime}
                  onChange={(event) => updateLocalProfile("tax_regime", event.target.value)}
                  className="w-full appearance-none rounded-xl border border-white/10 bg-white/[0.04] py-2.5 pl-10 pr-8 text-sm text-zinc-100 outline-none transition-colors focus:border-emerald-500/40 focus-visible:ring-2 focus-visible:ring-emerald-400/30"
                >
                  {TAX_REGIMES.map((option) => (
                    <option key={option.value} value={option.value} className="bg-zinc-900">
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          <div className="mt-5 flex flex-col gap-3 border-t border-white/[0.06] pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-5 text-zinc-500">
              Estes quatro campos não são enviados para o contexto financeiro do servidor.
            </p>
            <button
              type="button"
              onClick={saveLocalProfile}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-zinc-200 hover:bg-white/[0.08] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400/50"
            >
              {localSaved ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Save className="h-4 w-4" />}
              {localSaved ? "Salvo neste navegador" : "Salvar informações locais"}
            </button>
          </div>
        </SectionCard>

        <div className="flex items-start gap-2 rounded-xl border border-white/[0.06] bg-white/[0.015] p-4 text-xs leading-5 text-zinc-500">
          <Mail className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <p>
            Nome e e-mail vêm da identidade autenticada. CPF, telefone, nascimento e vínculo detalhado não são coletados por esta experiência.
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
