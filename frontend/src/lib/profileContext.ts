import { APIRequestError, requestFromAPI } from "@/lib/api";
import type { DecimalString, ISODateString, ISODatetimeString } from "@/lib/planning";
import {
  formatBRDate,
  formatBRLDecimalString,
  formatFinancialInputError,
  parseBRLMoneyInput,
} from "@/lib/planningLocale";

export const LEGACY_PROFILE_STORAGE_KEY = "fin_profile_extended";

export interface LocalProfileFields {
  display_name: string;
  occupation: string;
  company: string;
  tax_regime: string;
}

export const EMPTY_LOCAL_PROFILE: LocalProfileFields = {
  display_name: "",
  occupation: "",
  company: "",
  tax_regime: "",
};

export interface ProfileDeclaredContextResponse {
  name: string;
  email: string;
  declared_monthly_gross_income: DecimalString | null;
  semantic_type: "DECLARED";
  source: "USER_PROFILE";
  currency: "BRL" | null;
  income_period: "MONTHLY" | null;
  income_basis: "GROSS" | null;
  income_as_of_date: ISODateString | null;
  declared_at: ISODatetimeString | null;
  updated_at: ISODatetimeString | null;
}

export interface ProfileDeclaredContextPatch {
  declared_monthly_gross_income: DecimalString | null;
  income_as_of_date: ISODateString | null;
}

export type IncomeEvidenceState = "DETECTED_CANDIDATE" | "STALE";
export type IncomeDecisionState = "CONFIRMED_AS_INCOME" | "REJECTED";
export type RecurringIncomeRiskFlag = "TRANSFER_AMBIGUITY";

export interface MonthlyOccurrence {
  reference_month: string;
  occurrence_count: number;
}

export interface IncomeCandidate {
  candidate_id: string;
  evidence_state: IncomeEvidenceState;
  decision_state: IncomeDecisionState | null;
  signature_version: number;
  source: "GOVERNED_TRANSACTIONS";
  evidence_fingerprint: string | null;
  currency: string | null;
  direction: "CREDIT" | null;
  window_start: ISODateString | null;
  window_end: ISODateString | null;
  current_month_is_partial: boolean | null;
  includes_current_month: boolean | null;
  observed_months: string[];
  monthly_occurrences: MonthlyOccurrence[];
  occurrence_count: number | null;
  distinct_month_count: number | null;
  first_occurrence_date: ISODateString | null;
  latest_occurrence_date: ISODateString | null;
  latest_amount: DecimalString | null;
  typical_received_amount: DecimalString | null;
  minimum_received_amount: DecimalString | null;
  maximum_received_amount: DecimalString | null;
  median_absolute_deviation: DecimalString | null;
  risk_flags: RecurringIncomeRiskFlag[];
  decided_at: ISODatetimeString | null;
  decision_updated_at: ISODatetimeString | null;
}

export interface IncomeCandidateCollection {
  as_of_date: ISODateString;
  candidates: IncomeCandidate[];
}

export interface IncomeDecisionRequest {
  evidence_fingerprint: string;
}

export type ProfileAPITransport = <T>(
  endpoint: string,
  options?: RequestInit,
) => Promise<T>;

type LoadResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: unknown };

export interface ProfileExperienceLoadResult {
  profile: LoadResult<ProfileDeclaredContextResponse>;
  candidates: LoadResult<IncomeCandidateCollection>;
}

export type DeclaredIncomeValidation =
  | { ok: true; payload: ProfileDeclaredContextPatch }
  | { ok: false; message: string };

export interface CandidateActionErrorState {
  kind: "CONFLICT" | "UNAVAILABLE" | "OWNERSHIP" | "GENERIC";
  message: string;
  refresh: boolean;
}

export interface CandidatePresentation {
  label: string;
  detail: string;
  tone: "INFO" | "SUCCESS" | "NEUTRAL" | "WARNING";
  showCurrentEvidence: boolean;
  allowDecision: boolean;
  allowReset: boolean;
}

type StorageBoundary = Pick<Storage, "getItem" | "setItem">;

function stringField(value: unknown): string {
  return typeof value === "string" ? value : "";
}

/** Keeps the historical browser record purpose-limited and excludes financial/PII fields. */
export function sanitizeLocalProfile(value: unknown): LocalProfileFields {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { ...EMPTY_LOCAL_PROFILE };
  }

  const record = value as Record<string, unknown>;
  return {
    display_name: stringField(record.display_name),
    occupation: stringField(record.occupation),
    company: stringField(record.company),
    tax_regime: stringField(record.tax_regime),
  };
}

export function readAndSanitizeLocalProfile(storage: StorageBoundary): LocalProfileFields {
  const raw = storage.getItem(LEGACY_PROFILE_STORAGE_KEY);
  if (!raw) {
    return { ...EMPTY_LOCAL_PROFILE };
  }

  try {
    const profile = sanitizeLocalProfile(JSON.parse(raw));
    storage.setItem(LEGACY_PROFILE_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  } catch {
    const profile = { ...EMPTY_LOCAL_PROFILE };
    storage.setItem(LEGACY_PROFILE_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  }
}

export function writeLocalProfile(
  storage: StorageBoundary,
  profile: LocalProfileFields,
): void {
  storage.setItem(
    LEGACY_PROFILE_STORAGE_KEY,
    JSON.stringify(sanitizeLocalProfile(profile)),
  );
}

export function getProfileContext(
  transport: ProfileAPITransport = requestFromAPI,
): Promise<ProfileDeclaredContextResponse> {
  return transport<ProfileDeclaredContextResponse>("/profile/context");
}

export function patchProfileContext(
  payload: ProfileDeclaredContextPatch,
  transport: ProfileAPITransport = requestFromAPI,
): Promise<ProfileDeclaredContextResponse> {
  return transport<ProfileDeclaredContextResponse>("/profile/context", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getIncomeCandidates(
  transport: ProfileAPITransport = requestFromAPI,
): Promise<IncomeCandidateCollection> {
  return transport<IncomeCandidateCollection>(
    "/financial-context/income-candidates",
  );
}

function candidateDecisionPath(candidateId: string, action: "confirm" | "reject"): string {
  return `/financial-context/income-candidates/${encodeURIComponent(candidateId)}/${action}`;
}

export function confirmIncomeCandidate(
  candidateId: string,
  evidenceFingerprint: string,
  transport: ProfileAPITransport = requestFromAPI,
): Promise<IncomeCandidate> {
  return transport<IncomeCandidate>(candidateDecisionPath(candidateId, "confirm"), {
    method: "POST",
    body: JSON.stringify({ evidence_fingerprint: evidenceFingerprint } satisfies IncomeDecisionRequest),
  });
}

export function rejectIncomeCandidate(
  candidateId: string,
  evidenceFingerprint: string,
  transport: ProfileAPITransport = requestFromAPI,
): Promise<IncomeCandidate> {
  return transport<IncomeCandidate>(candidateDecisionPath(candidateId, "reject"), {
    method: "POST",
    body: JSON.stringify({ evidence_fingerprint: evidenceFingerprint } satisfies IncomeDecisionRequest),
  });
}

export function resetIncomeCandidateDecision(
  candidateId: string,
  transport: ProfileAPITransport = requestFromAPI,
): Promise<void> {
  return transport<void>(
    `/financial-context/income-candidates/${encodeURIComponent(candidateId)}/decision`,
    { method: "DELETE" },
  );
}

async function settle<T>(operation: Promise<T>): Promise<LoadResult<T>> {
  try {
    return { ok: true, value: await operation };
  } catch (error) {
    return { ok: false, error };
  }
}

/** Initial load is intentionally GET-only; browser state can never trigger a PATCH. */
export async function loadProfileExperience(
  transport: ProfileAPITransport = requestFromAPI,
): Promise<ProfileExperienceLoadResult> {
  const [profile, candidates] = await Promise.all([
    settle(getProfileContext(transport)),
    settle(getIncomeCandidates(transport)),
  ]);
  return { profile, candidates };
}

function isValidISODate(value: string): value is ISODateString {
  try {
    formatBRDate(value as ISODateString);
    return true;
  } catch {
    return false;
  }
}

export function buildDeclaredIncomePatch(
  incomeInput: string,
  incomeAsOfDate: string,
): DeclaredIncomeValidation {
  const parsed = parseBRLMoneyInput(incomeInput);
  if (!parsed.ok) {
    return {
      ok: false,
      message: formatFinancialInputError(parsed.code, "money"),
    };
  }
  if (parsed.value.startsWith("-") || parsed.value === "0.00") {
    return { ok: false, message: "Informe um valor maior que zero." };
  }
  if (incomeAsOfDate !== "" && !isValidISODate(incomeAsOfDate)) {
    return { ok: false, message: "Informe uma data de referência válida." };
  }

  return {
    ok: true,
    payload: {
      declared_monthly_gross_income: parsed.value,
      income_as_of_date: incomeAsOfDate === "" ? null : incomeAsOfDate,
    },
  };
}

export function clearDeclaredIncomePatch(): ProfileDeclaredContextPatch {
  return {
    declared_monthly_gross_income: null,
    income_as_of_date: null,
  };
}

export function formatDeclaredIncomeInput(value: DecimalString | null): string {
  return value === null ? "" : formatBRLDecimalString(value);
}

const OFFSET_LESS_ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/;
const OFFSET_ISO_TIMESTAMP =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/i;

/** Smart Context persists naive datetime.utcnow values; normalize them as UTC for the browser. */
export function normalizeBackendUTCTimestamp(value: string | null | undefined): string | null {
  if (!value) return null;
  const normalized = OFFSET_LESS_ISO_TIMESTAMP.test(value) ? `${value}Z` : value;
  if (!OFFSET_ISO_TIMESTAMP.test(normalized)) return null;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : normalized;
}

export function formatBackendUTCTimestamp(
  value: string | null | undefined,
  timeZone?: string,
): string | null {
  const normalized = normalizeBackendUTCTimestamp(value);
  if (!normalized) return null;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    ...(timeZone ? { timeZone } : {}),
  }).format(new Date(normalized));
}

export function getCandidatePresentation(candidate: IncomeCandidate): CandidatePresentation {
  if (candidate.evidence_state === "STALE") {
    if (candidate.decision_state === "CONFIRMED_AS_INCOME") {
      return {
        label: "Confirmada anteriormente · evidência atual insuficiente",
        detail: "Sua confirmação foi preservada, mas esta fonte não possui recorrência atual suficiente.",
        tone: "WARNING",
        showCurrentEvidence: false,
        allowDecision: false,
        allowReset: true,
      };
    }
    if (candidate.decision_state === "REJECTED") {
      return {
        label: "Rejeitada anteriormente · evidência atual insuficiente",
        detail: "Sua rejeição foi preservada, mas esta fonte não possui recorrência atual suficiente.",
        tone: "NEUTRAL",
        showCurrentEvidence: false,
        allowDecision: false,
        allowReset: true,
      };
    }
    return {
      label: "Evidência atual insuficiente",
      detail: "Esta fonte não possui recorrência atual suficiente.",
      tone: "WARNING",
      showCurrentEvidence: false,
      allowDecision: false,
      allowReset: false,
    };
  }
  if (candidate.decision_state === "CONFIRMED_AS_INCOME") {
    return {
      label: "Confirmado como renda recorrente",
      detail: "Classificação confirmada por você. Isso não transforma a fonte em salário garantido.",
      tone: "SUCCESS",
      showCurrentEvidence: true,
      allowDecision: false,
      allowReset: true,
    };
  }
  if (candidate.decision_state === "REJECTED") {
    return {
      label: "Rejeitado por você",
      detail: "Esta fonte não será tratada como uma referência positiva de renda recorrente.",
      tone: "NEUTRAL",
      showCurrentEvidence: true,
      allowDecision: false,
      allowReset: true,
    };
  }
  return {
    label: "Aguardando sua revisão",
    detail: "Identificamos uma movimentação recorrente. Revise a evidência antes de classificar.",
    tone: "INFO",
    showCurrentEvidence: true,
    allowDecision: true,
    allowReset: false,
  };
}

export function profileLoadErrorMessage(error: unknown): string {
  if (error instanceof APIRequestError && error.status === 422) {
    return "Não foi possível carregar o contexto financeiro.";
  }
  return "Não foi possível carregar o perfil agora. Tente novamente.";
}

export function candidateLoadErrorMessage(error: unknown): string {
  if (error instanceof APIRequestError && error.status === 422) {
    return "Não foi possível carregar o contexto financeiro.";
  }
  return "Não foi possível carregar as fontes recorrentes agora.";
}

export function profileSaveErrorMessage(error: unknown): string {
  if (error instanceof APIRequestError && error.status === 422) {
    return "Não foi possível salvar o contexto financeiro. Revise os dados ou tente novamente.";
  }
  return "Não foi possível salvar o contexto financeiro agora.";
}

export function candidateActionError(error: unknown): CandidateActionErrorState {
  if (error instanceof APIRequestError && error.status === 409) {
    return {
      kind: "CONFLICT",
      message: "As movimentações usadas nesta análise mudaram.",
      refresh: true,
    };
  }
  if (error instanceof APIRequestError && error.status === 404) {
    return {
      kind: "UNAVAILABLE",
      message: "Esta fonte não está mais disponível para revisão.",
      refresh: true,
    };
  }
  if (error instanceof APIRequestError && error.status === 422) {
    return {
      kind: "OWNERSHIP",
      message: "Não foi possível atualizar o contexto financeiro.",
      refresh: false,
    };
  }
  return {
    kind: "GENERIC",
    message: "Não foi possível registrar sua decisão agora.",
    refresh: false,
  };
}
