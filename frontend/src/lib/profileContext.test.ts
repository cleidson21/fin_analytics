import { describe, expect, it, vi } from "vitest";

vi.hoisted(() => {
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1";
});

import { APIRequestError } from "@/lib/api";
import {
  EMPTY_LOCAL_PROFILE,
  LEGACY_PROFILE_STORAGE_KEY,
  buildDeclaredIncomePatch,
  candidateActionError,
  candidateLoadErrorMessage,
  clearDeclaredIncomePatch,
  confirmIncomeCandidate,
  formatBackendUTCTimestamp,
  formatDeclaredIncomeInput,
  getCandidatePresentation,
  loadProfileExperience,
  normalizeBackendUTCTimestamp,
  patchProfileContext,
  profileLoadErrorMessage,
  profileSaveErrorMessage,
  readAndSanitizeLocalProfile,
  rejectIncomeCandidate,
  resetIncomeCandidateDecision,
  sanitizeLocalProfile,
  writeLocalProfile,
  type IncomeCandidate,
  type IncomeCandidateCollection,
  type ProfileAPITransport,
  type ProfileDeclaredContextResponse,
} from "@/lib/profileContext";

const PROFILE_RESPONSE: ProfileDeclaredContextResponse = {
  name: "Pessoa autenticada",
  email: "pessoa@example.com",
  declared_monthly_gross_income: "5500.00",
  semantic_type: "DECLARED",
  source: "USER_PROFILE",
  currency: "BRL",
  income_period: "MONTHLY",
  income_basis: "GROSS",
  income_as_of_date: "2026-10-01",
  declared_at: "2026-10-02T10:00:00",
  updated_at: "2026-10-02T10:00:00",
};

function candidate(
  decisionState: IncomeCandidate["decision_state"] = null,
  evidenceState: IncomeCandidate["evidence_state"] = "DETECTED_CANDIDATE",
): IncomeCandidate {
  const current = evidenceState === "DETECTED_CANDIDATE";
  return {
    candidate_id: "ric_v1_opaque",
    evidence_state: evidenceState,
    decision_state: decisionState,
    signature_version: 1,
    source: "GOVERNED_TRANSACTIONS",
    evidence_fingerprint: current ? `sha256:${"a".repeat(64)}` : null,
    currency: current ? "BRL" : null,
    direction: current ? "CREDIT" : null,
    window_start: current ? "2026-05-01" : null,
    window_end: current ? "2026-10-05" : null,
    current_month_is_partial: current ? true : null,
    includes_current_month: current ? true : null,
    observed_months: current ? ["2026-08", "2026-09", "2026-10"] : [],
    monthly_occurrences: current
      ? [
          { reference_month: "2026-08", occurrence_count: 1 },
          { reference_month: "2026-09", occurrence_count: 1 },
          { reference_month: "2026-10", occurrence_count: 1 },
        ]
      : [],
    occurrence_count: current ? 3 : null,
    distinct_month_count: current ? 3 : null,
    first_occurrence_date: current ? "2026-08-05" : null,
    latest_occurrence_date: current ? "2026-10-05" : null,
    latest_amount: current ? "4200.10" : null,
    typical_received_amount: current ? "4200.10" : null,
    minimum_received_amount: current ? "4000.00" : null,
    maximum_received_amount: current ? "4300.00" : null,
    median_absolute_deviation: current ? "100.00" : null,
    risk_flags: current ? ["TRANSFER_AMBIGUITY"] : [],
    decided_at: decisionState ? "2026-09-01T12:00:00" : null,
    decision_updated_at: decisionState ? "2026-09-01T12:00:00" : null,
  };
}

function memoryStorage(initial: string | null = null) {
  const values = new Map<string, string>();
  if (initial !== null) values.set(LEGACY_PROFILE_STORAGE_KEY, initial);
  return {
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    },
  };
}

describe("Profile local browser boundary", () => {
  it("keeps only the four approved local presentation/professional fields", () => {
    expect(
      sanitizeLocalProfile({
        display_name: "Nome local",
        occupation: "Analista",
        company: "Empresa",
        tax_regime: "CLT",
        gross_monthly_income: "9999.99",
        cpf: "sensitive",
        phone: "sensitive",
        birthdate: "2000-01-01",
        employment_start: "2020-01-01",
      }),
    ).toEqual({
      display_name: "Nome local",
      occupation: "Analista",
      company: "Empresa",
      tax_regime: "CLT",
    });
  });

  it("sanitizes an old local record without creating an eligible income migration", () => {
    const storage = memoryStorage(
      JSON.stringify({
        display_name: "Nome local",
        occupation: "Analista",
        gross_monthly_income: "9999.99",
        cpf: "sensitive",
      }),
    );

    const result = readAndSanitizeLocalProfile(storage);

    expect(result).toEqual({ ...EMPTY_LOCAL_PROFILE, display_name: "Nome local", occupation: "Analista" });
    expect(JSON.parse(storage.getItem(LEGACY_PROFILE_STORAGE_KEY) ?? "{}")).toEqual(result);
  });

  it("recovers malformed local JSON as an empty purpose-limited record", () => {
    const storage = memoryStorage("{not-json");
    expect(readAndSanitizeLocalProfile(storage)).toEqual(EMPTY_LOCAL_PROFILE);
  });

  it("writes no financial or sensitive field to local storage", () => {
    const storage = memoryStorage();
    writeLocalProfile(storage, {
      display_name: "Nome",
      occupation: "Pessoa desenvolvedora",
      company: "Empresa",
      tax_regime: "PJ",
    });
    const persisted = storage.getItem(LEGACY_PROFILE_STORAGE_KEY) ?? "";
    expect(persisted).not.toContain("income");
    expect(persisted).not.toContain("cpf");
    expect(JSON.parse(persisted)).toEqual({
      display_name: "Nome",
      occupation: "Pessoa desenvolvedora",
      company: "Empresa",
      tax_regime: "PJ",
    });
  });
});

describe("Declared Profile context contract", () => {
  it.each([
    ["5.500,00", "5500.00"],
    ["R$ 0,01", "0.01"],
    ["1234567890123456,78", "1234567890123456.78"],
  ])("maps a valid BRL input %s to exact API text %s", (input, expected) => {
    expect(buildDeclaredIncomePatch(input, "2026-10-01")).toEqual({
      ok: true,
      payload: {
        declared_monthly_gross_income: expected,
        income_as_of_date: "2026-10-01",
      },
    });
  });

  it.each(["0", "0,00", "-1,00"])("rejects non-positive declared income %s", (input) => {
    expect(buildDeclaredIncomePatch(input, "")).toEqual({
      ok: false,
      message: "Informe um valor maior que zero.",
    });
  });

  it.each(["1,001", "abc", "1e3", "1.00,00"])("rejects malformed declared income %s", (input) => {
    expect(buildDeclaredIncomePatch(input, "").ok).toBe(false);
  });

  it("rejects an invalid civil as-of date", () => {
    expect(buildDeclaredIncomePatch("5500,00", "2026-02-30")).toEqual({
      ok: false,
      message: "Informe uma data de referência válida.",
    });
  });

  it("preserves an absent as-of date instead of fabricating today", () => {
    expect(buildDeclaredIncomePatch("5500,00", "")).toEqual({
      ok: true,
      payload: {
        declared_monthly_gross_income: "5500.00",
        income_as_of_date: null,
      },
    });
  });

  it("uses explicit nulls for clear and never zero", () => {
    expect(clearDeclaredIncomePatch()).toEqual({
      declared_monthly_gross_income: null,
      income_as_of_date: null,
    });
  });

  it("formats server Decimal text without JavaScript number authority", () => {
    expect(formatDeclaredIncomeInput("9007199254740993.01")).toBe("R$ 9.007.199.254.740.993,01");
    expect(formatDeclaredIncomeInput(null)).toBe("");
  });

  it("normalizes offset-less backend UTC timestamps without changing explicit offsets", () => {
    expect(normalizeBackendUTCTimestamp("2026-10-06T22:30:00")).toBe(
      "2026-10-06T22:30:00Z",
    );
    expect(normalizeBackendUTCTimestamp("2026-10-06T22:30:00Z")).toBe(
      "2026-10-06T22:30:00Z",
    );
    expect(normalizeBackendUTCTimestamp("2026-10-06T19:30:00-03:00")).toBe(
      "2026-10-06T19:30:00-03:00",
    );
  });

  it("formats naive UTC deterministically and keeps civil dates out of timestamp parsing", () => {
    expect(formatBackendUTCTimestamp("2026-10-06T22:30:00", "UTC")).toBe(
      formatBackendUTCTimestamp("2026-10-06T22:30:00Z", "UTC"),
    );
    expect(formatBackendUTCTimestamp("2026-10-06T19:30:00-03:00", "UTC")).toBe(
      formatBackendUTCTimestamp("2026-10-06T22:30:00Z", "UTC"),
    );
    expect(formatBackendUTCTimestamp("2026-10-06", "UTC")).toBeNull();
    expect(formatBackendUTCTimestamp("invalid", "UTC")).toBeNull();
    expect(formatBackendUTCTimestamp(null, "UTC")).toBeNull();
  });

  it("PATCH submits only the two approved declared-context fields", async () => {
    const calls: Array<{ endpoint: string; options?: RequestInit }> = [];
    const transport: ProfileAPITransport = async <T>(endpoint: string, options?: RequestInit) => {
      calls.push({ endpoint, options });
      return PROFILE_RESPONSE as T;
    };
    await patchProfileContext(
      { declared_monthly_gross_income: "5500.00", income_as_of_date: null },
      transport,
    );

    expect(calls).toHaveLength(1);
    expect(calls[0].endpoint).toBe("/profile/context");
    expect(calls[0].options?.method).toBe("PATCH");
    expect(JSON.parse(String(calls[0].options?.body))).toEqual({
      declared_monthly_gross_income: "5500.00",
      income_as_of_date: null,
    });
  });
});

describe("Profile experience loading", () => {
  it("loads Profile and candidates with GET-only requests and no automatic upload", async () => {
    const calls: Array<{ endpoint: string; options?: RequestInit }> = [];
    const collection: IncomeCandidateCollection = {
      as_of_date: "2026-10-05",
      candidates: [],
    };
    const transport: ProfileAPITransport = async <T>(endpoint: string, options?: RequestInit) => {
      calls.push({ endpoint, options });
      return (endpoint === "/profile/context" ? PROFILE_RESPONSE : collection) as T;
    };

    const result = await loadProfileExperience(transport);

    expect(result.profile.ok).toBe(true);
    expect(result.candidates.ok).toBe(true);
    expect(calls.map((call) => call.endpoint).sort()).toEqual([
      "/financial-context/income-candidates",
      "/profile/context",
    ]);
    expect(calls.every((call) => call.options === undefined)).toBe(true);
  });

  it("does not upload an unrelated legacy object during initial load", async () => {
    const storage = memoryStorage(
      JSON.stringify({
        display_name: "Nome",
        occupation: "Analista",
        company: "Empresa",
        tax_regime: "CLT",
        gross_monthly_income: "9999.99",
        phone: "sensitive",
      }),
    );
    readAndSanitizeLocalProfile(storage);
    const methods: Array<string | undefined> = [];
    const transport: ProfileAPITransport = async <T>(endpoint: string, options?: RequestInit) => {
      methods.push(options?.method);
      return (endpoint === "/profile/context"
        ? PROFILE_RESPONSE
        : { as_of_date: "2026-10-05", candidates: [] }) as T;
    };

    await loadProfileExperience(transport);
    expect(methods).toEqual([undefined, undefined]);
  });
});

describe("Recurring-income decision client", () => {
  it.each([
    ["confirm", confirmIncomeCandidate],
    ["reject", rejectIncomeCandidate],
  ] as const)("%s submits only the reviewed evidence fingerprint", async (action, operation) => {
    const calls: Array<{ endpoint: string; options?: RequestInit }> = [];
    const transport: ProfileAPITransport = async <T>(endpoint: string, options?: RequestInit) => {
      calls.push({ endpoint, options });
      return candidate() as T;
    };
    const fingerprint = `sha256:${"b".repeat(64)}`;

    await operation("candidate/with space", fingerprint, transport);

    expect(calls[0].endpoint).toBe(
      `/financial-context/income-candidates/candidate%2Fwith%20space/${action}`,
    );
    expect(calls[0].options?.method).toBe("POST");
    expect(JSON.parse(String(calls[0].options?.body))).toEqual({
      evidence_fingerprint: fingerprint,
    });
  });

  it("reset uses the exact DELETE decision route and no request body", async () => {
    const calls: Array<{ endpoint: string; options?: RequestInit }> = [];
    const transport: ProfileAPITransport = async <T>(endpoint: string, options?: RequestInit) => {
      calls.push({ endpoint, options });
      return undefined as T;
    };

    await resetIncomeCandidateDecision("ric_v1_opaque", transport);

    expect(calls).toEqual([
      {
        endpoint: "/financial-context/income-candidates/ric_v1_opaque/decision",
        options: { method: "DELETE" },
      },
    ]);
  });

  it("keeps detected, confirmed, rejected, and both stale decisions distinct", () => {
    const detected = getCandidatePresentation(candidate());
    const confirmed = getCandidatePresentation(candidate("CONFIRMED_AS_INCOME"));
    const rejected = getCandidatePresentation(candidate("REJECTED"));
    const staleConfirmed = getCandidatePresentation(
      candidate("CONFIRMED_AS_INCOME", "STALE"),
    );
    const staleRejected = getCandidatePresentation(candidate("REJECTED", "STALE"));

    expect(detected.allowDecision).toBe(true);
    expect(detected.label.toLowerCase()).not.toContain("salário");
    expect(confirmed.label).toBe("Confirmado como renda recorrente");
    expect(rejected.label).toBe("Rejeitado por você");
    expect(staleConfirmed.label).toContain("Confirmada anteriormente");
    expect(staleRejected.label).toContain("Rejeitada anteriormente");
    expect(staleConfirmed.label).not.toBe(staleRejected.label);
    expect(staleConfirmed.tone).not.toBe(staleRejected.tone);
    expect(staleConfirmed.showCurrentEvidence).toBe(false);
    expect(staleRejected.showCurrentEvidence).toBe(false);
    expect(staleConfirmed.allowReset).toBe(true);
    expect(staleRejected.allowReset).toBe(true);
  });

  it("never introduces confidence or detected-salary copy", () => {
    const visibleCopy = [
      getCandidatePresentation(candidate()),
      getCandidatePresentation(candidate("CONFIRMED_AS_INCOME")),
      getCandidatePresentation(candidate("REJECTED")),
      getCandidatePresentation(candidate("CONFIRMED_AS_INCOME", "STALE")),
    ]
      .flatMap((state) => [state.label, state.detail])
      .join(" ")
      .toLowerCase();
    expect(visibleCopy).not.toContain("confiança");
    expect(visibleCopy).not.toContain("salário detectado");
    expect(visibleCopy).not.toContain("seu salário");
  });
});

describe("Safe error presentation", () => {
  it("requires refresh after 409 and 404 without exposing backend details", () => {
    expect(candidateActionError(new APIRequestError(409, "/private"))).toEqual({
      kind: "CONFLICT",
      message: "As movimentações usadas nesta análise mudaram.",
      refresh: true,
    });
    expect(candidateActionError(new APIRequestError(404, "/private"))).toEqual({
      kind: "UNAVAILABLE",
      message: "Esta fonte não está mais disponível para revisão.",
      refresh: true,
    });
  });

  it("maps ownership-safe 422 errors to generic context language", () => {
    const error = new APIRequestError(422, "/private");
    expect(profileLoadErrorMessage(error)).toBe("Não foi possível carregar o contexto financeiro.");
    expect(candidateLoadErrorMessage(error)).toBe("Não foi possível carregar o contexto financeiro.");
    expect(profileSaveErrorMessage(error)).not.toContain("usuário");
    expect(candidateActionError(error).message).not.toContain("ownership");
  });
});
