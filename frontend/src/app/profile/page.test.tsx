// @vitest-environment jsdom

import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.hoisted(() => {
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1";
});

const apiMocks = vi.hoisted(() => ({
  loadProfileExperience: vi.fn(),
  patchProfileContext: vi.fn(),
  getIncomeCandidates: vi.fn(),
  confirmIncomeCandidate: vi.fn(),
  rejectIncomeCandidate: vi.fn(),
  resetIncomeCandidateDecision: vi.fn(),
}));

const authState = vi.hoisted(() => ({
  user: {
    id: "authenticated-user",
    name: "Pessoa autenticada",
    email: "pessoa@example.com",
    role: "USER",
    is_active: true,
    is_verified: true,
  },
  token: "test-token",
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => authState,
}));

vi.mock("@/components/layout/PageLayout", () => ({
  PageLayout: ({ title, children }: { title: string; children: React.ReactNode }) => (
    <main>
      <h1>{title}</h1>
      {children}
    </main>
  ),
}));

vi.mock("@/lib/profileContext", async () => {
  const actual = await vi.importActual<typeof import("@/lib/profileContext")>(
    "@/lib/profileContext",
  );
  return {
    ...actual,
    ...apiMocks,
  };
});

import ProfilePage from "@/app/profile/page";
import { APIRequestError } from "@/lib/api";
import type {
  IncomeCandidate,
  IncomeCandidateCollection,
  ProfileDeclaredContextResponse,
} from "@/lib/profileContext";

const FINGERPRINT = `sha256:${"a".repeat(64)}`;

const EMPTY_PROFILE: ProfileDeclaredContextResponse = {
  name: "Pessoa autenticada",
  email: "pessoa@example.com",
  declared_monthly_gross_income: null,
  semantic_type: "DECLARED",
  source: "USER_PROFILE",
  currency: null,
  income_period: null,
  income_basis: null,
  income_as_of_date: null,
  declared_at: null,
  updated_at: "2026-10-06T22:30:00",
};

const DECLARED_PROFILE: ProfileDeclaredContextResponse = {
  ...EMPTY_PROFILE,
  declared_monthly_gross_income: "5500.00",
  currency: "BRL",
  income_period: "MONTHLY",
  income_basis: "GROSS",
  income_as_of_date: "2026-10-01",
  declared_at: "2026-10-06T22:30:00",
};

function candidate(
  id: string,
  decisionState: IncomeCandidate["decision_state"] = null,
  evidenceState: IncomeCandidate["evidence_state"] = "DETECTED_CANDIDATE",
  riskFlags: IncomeCandidate["risk_flags"] = [],
): IncomeCandidate {
  const current = evidenceState === "DETECTED_CANDIDATE";
  return {
    candidate_id: id,
    evidence_state: evidenceState,
    decision_state: decisionState,
    signature_version: 1,
    source: "GOVERNED_TRANSACTIONS",
    evidence_fingerprint: current ? FINGERPRINT : null,
    currency: current ? "BRL" : null,
    direction: current ? "CREDIT" : null,
    window_start: current ? "2026-05-01" : null,
    window_end: current ? "2026-10-06" : null,
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
    latest_amount: current ? "4200.10" : "9876.54",
    typical_received_amount: current ? "4200.10" : "9876.54",
    minimum_received_amount: current ? "4000.00" : "9876.54",
    maximum_received_amount: current ? "4300.00" : "9876.54",
    median_absolute_deviation: current ? "100.00" : "9876.54",
    risk_flags: riskFlags,
    decided_at: decisionState ? "2026-09-01T15:00:00" : null,
    decision_updated_at: decisionState ? "2026-09-01T15:00:00" : null,
  };
}

function collection(candidates: IncomeCandidate[]): IncomeCandidateCollection {
  return { as_of_date: "2026-10-06", candidates };
}

function loadResult(
  profile: ProfileDeclaredContextResponse,
  candidates: IncomeCandidateCollection,
) {
  return {
    profile: { ok: true as const, value: profile },
    candidates: { ok: true as const, value: candidates },
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function renderProfile() {
  render(<ProfilePage />);
  await screen.findByText("Contexto financeiro declarado");
  await waitFor(() => expect(apiMocks.loadProfileExperience).toHaveBeenCalledTimes(1));
}

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  const detected = candidate("candidate-a");
  const initialCollection = collection([detected]);
  apiMocks.loadProfileExperience.mockResolvedValue(
    loadResult(EMPTY_PROFILE, initialCollection),
  );
  apiMocks.getIncomeCandidates.mockResolvedValue(initialCollection);
  apiMocks.patchProfileContext.mockResolvedValue(DECLARED_PROFILE);
  apiMocks.confirmIncomeCandidate.mockResolvedValue(detected);
  apiMocks.rejectIncomeCandidate.mockResolvedValue(detected);
  apiMocks.resetIncomeCandidateDecision.mockResolvedValue(undefined);
});

describe("Profile page declared context and browser boundary", () => {
  it("performs no mutation on mount and never uploads the local Profile object", async () => {
    window.localStorage.setItem(
      "fin_profile_extended",
      JSON.stringify({
        display_name: "Nome local",
        occupation: "Pessoa desenvolvedora",
        company: "Empresa local",
        tax_regime: "PJ",
        gross_monthly_income: "9999.99",
        cpf: "000.000.000-00",
      }),
    );

    await renderProfile();

    expect((screen.getByLabelText("Ocupação / cargo") as HTMLInputElement).value).toBe(
      "Pessoa desenvolvedora",
    );
    expect(apiMocks.patchProfileContext).not.toHaveBeenCalled();
    expect(apiMocks.confirmIncomeCandidate).not.toHaveBeenCalled();
    expect(apiMocks.rejectIncomeCandidate).not.toHaveBeenCalled();
    expect(apiMocks.resetIncomeCandidateDecision).not.toHaveBeenCalled();
    expect(JSON.parse(window.localStorage.getItem("fin_profile_extended") ?? "{}")).toEqual({
      display_name: "Nome local",
      occupation: "Pessoa desenvolvedora",
      company: "Empresa local",
      tax_regime: "PJ",
    });
  });

  it("saves an exact declared value only after the explicit action", async () => {
    await renderProfile();

    fireEvent.change(screen.getByLabelText("Valor mensal bruto"), {
      target: { value: "R$ 5.500,00" },
    });
    fireEvent.change(screen.getByLabelText("Data de referência do valor informado"), {
      target: { value: "2026-10-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar declaração" }));

    await waitFor(() =>
      expect(apiMocks.patchProfileContext).toHaveBeenCalledWith({
        declared_monthly_gross_income: "5500.00",
        income_as_of_date: "2026-10-01",
      }),
    );
    expect(await screen.findByText("Contexto declarado salvo pelo servidor.")).toBeTruthy();
  });

  it("clears only after explicit two-step confirmation", async () => {
    apiMocks.loadProfileExperience.mockResolvedValueOnce(
      loadResult(DECLARED_PROFILE, collection([])),
    );
    apiMocks.patchProfileContext.mockResolvedValueOnce(EMPTY_PROFILE);
    await renderProfile();

    fireEvent.click(screen.getByRole("button", { name: "Limpar valor" }));
    expect(apiMocks.patchProfileContext).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar limpeza" }));

    await waitFor(() =>
      expect(apiMocks.patchProfileContext).toHaveBeenCalledWith({
        declared_monthly_gross_income: null,
        income_as_of_date: null,
      }),
    );
    expect(await screen.findByText("Renda mensal bruta declarada removida.")).toBeTruthy();
  });
});

describe("Profile page recurring-income decisions", () => {
  it.each([
    ["Confirmar como renda recorrente", apiMocks.confirmIncomeCandidate],
    ["Não é minha renda recorrente", apiMocks.rejectIncomeCandidate],
  ])("executes %s with the opaque fingerprint", async (buttonName, operation) => {
    await renderProfile();
    expect(document.body.textContent).not.toContain(FINGERPRINT);

    fireEvent.click(screen.getByRole("button", { name: buttonName }));

    await waitFor(() =>
      expect(operation).toHaveBeenCalledWith("candidate-a", FINGERPRINT),
    );
    expect(document.body.textContent).not.toContain(FINGERPRINT);
  });

  it("resets a decision and keeps the success message when refresh returns an empty list", async () => {
    apiMocks.loadProfileExperience.mockResolvedValueOnce(
      loadResult(EMPTY_PROFILE, collection([candidate("candidate-a", "CONFIRMED_AS_INCOME")])),
    );
    apiMocks.getIncomeCandidates.mockResolvedValueOnce(collection([]));
    await renderProfile();

    fireEvent.click(screen.getByRole("button", { name: "Remover decisão" }));

    expect(await screen.findByText("Decisão removida. A lista foi atualizada.")).toBeTruthy();
    expect(screen.getByText("Nenhuma fonte está disponível para revisão.")).toBeTruthy();
  });

  it("uses a global synchronous lock to reject concurrent candidate mutations and retries", async () => {
    const first = candidate("candidate-a");
    const second = candidate("candidate-b");
    const pending = deferred<IncomeCandidate>();
    apiMocks.loadProfileExperience.mockResolvedValueOnce({
      profile: { ok: false as const, error: new Error("profile unavailable") },
      candidates: { ok: true as const, value: collection([first, second]) },
    });
    apiMocks.getIncomeCandidates.mockResolvedValueOnce(collection([first, second]));
    apiMocks.confirmIncomeCandidate.mockReturnValueOnce(pending.promise);
    await renderProfile();

    const confirmButtons = screen.getAllByRole("button", {
      name: "Confirmar como renda recorrente",
    });
    const retryProfile = screen.getByRole("button", { name: "Tentar novamente" });
    fireEvent.click(confirmButtons[0]);
    await waitFor(() => expect(apiMocks.confirmIncomeCandidate).toHaveBeenCalledTimes(1));

    expect((confirmButtons[1] as HTMLButtonElement).disabled).toBe(true);
    expect((retryProfile as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(confirmButtons[1]);
    fireEvent.click(retryProfile);
    expect(apiMocks.confirmIncomeCandidate).toHaveBeenCalledTimes(1);
    expect(apiMocks.loadProfileExperience).toHaveBeenCalledTimes(1);

    await act(async () => pending.resolve(first));
    await waitFor(() =>
      expect(
        (screen.getAllByRole("button", {
          name: "Confirmar como renda recorrente",
        })[1] as HTMLButtonElement).disabled,
      ).toBe(false),
    );
  });

  it("blocks a candidate mutation while a retry is already in flight", async () => {
    const first = candidate("candidate-a");
    const retry = deferred<ReturnType<typeof loadResult>>();
    apiMocks.loadProfileExperience
      .mockResolvedValueOnce({
        profile: { ok: false as const, error: new Error("profile unavailable") },
        candidates: { ok: true as const, value: collection([first]) },
      })
      .mockReturnValueOnce(retry.promise);
    await renderProfile();

    const retryProfile = screen.getByRole("button", { name: "Tentar novamente" });
    const confirm = screen.getByRole("button", { name: "Confirmar como renda recorrente" });
    fireEvent.click(retryProfile);
    await waitFor(() => expect(apiMocks.loadProfileExperience).toHaveBeenCalledTimes(2));

    expect((confirm as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(confirm);
    expect(apiMocks.confirmIncomeCandidate).not.toHaveBeenCalled();

    await act(async () => retry.resolve(loadResult(EMPTY_PROFILE, collection([first]))));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Confirmar como renda recorrente" }) as HTMLButtonElement,
      ).toHaveProperty("disabled", false),
    );
  });

  it("keeps a 404 message visible when canonical refresh removes the candidate", async () => {
    apiMocks.loadProfileExperience.mockResolvedValueOnce({
      profile: { ok: false as const, error: new Error("profile unavailable") },
      candidates: {
        ok: true as const,
        value: collection([candidate("candidate-a")]),
      },
    });
    apiMocks.confirmIncomeCandidate.mockRejectedValueOnce(
      new APIRequestError(404, "/private"),
    );
    apiMocks.getIncomeCandidates.mockResolvedValueOnce(collection([]));
    await renderProfile();

    fireEvent.click(screen.getByRole("button", { name: "Confirmar como renda recorrente" }));

    expect(
      await screen.findByText("Esta fonte não está mais disponível para revisão. A lista foi atualizada."),
    ).toBeTruthy();
    expect(screen.getByText("Nenhuma fonte está disponível para revisão.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Tentar novamente" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("reports a refreshed 409 accurately and releases the mutation lock", async () => {
    apiMocks.confirmIncomeCandidate.mockRejectedValueOnce(
      new APIRequestError(409, "/private"),
    );
    await renderProfile();
    const button = screen.getByRole("button", { name: "Confirmar como renda recorrente" });

    fireEvent.click(button);

    expect(
      await screen.findByText(
        "As movimentações usadas nesta análise mudaram. Os dados foram atualizados para uma nova revisão.",
      ),
    ).toBeTruthy();
    await waitFor(() => expect((button as HTMLButtonElement).disabled).toBe(false));
  });

  it("does not claim a successful refresh when the 409 reload fails and releases the lock", async () => {
    apiMocks.confirmIncomeCandidate.mockRejectedValueOnce(
      new APIRequestError(409, "/private"),
    );
    apiMocks.getIncomeCandidates.mockRejectedValueOnce(new Error("refresh failed"));
    await renderProfile();
    const button = screen.getByRole("button", { name: "Confirmar como renda recorrente" });

    fireEvent.click(button);

    const feedback = await screen.findByText(
      "As movimentações usadas nesta análise mudaram. Não foi possível atualizar a lista agora. Use Recarregar evidências.",
    );
    expect(feedback.textContent).toContain("As movimentações usadas nesta análise mudaram.");
    expect(feedback.textContent).toContain("Não foi possível atualizar a lista agora.");
    expect(feedback.textContent).not.toContain("foram atualizados");
    await waitFor(() => expect((button as HTMLButtonElement).disabled).toBe(false));
  });

  it("releases the mutation lock after an unexpected action failure", async () => {
    apiMocks.confirmIncomeCandidate.mockRejectedValueOnce(new Error("unexpected"));
    await renderProfile();
    const button = screen.getByRole("button", { name: "Confirmar como renda recorrente" });

    fireEvent.click(button);

    expect(await screen.findByText("Não foi possível registrar sua decisão agora.")).toBeTruthy();
    await waitFor(() => expect((button as HTMLButtonElement).disabled).toBe(false));
  });

  it("renders stale confirmed and stale rejected decisions distinctly without old money", async () => {
    apiMocks.loadProfileExperience.mockResolvedValueOnce(
      loadResult(
        EMPTY_PROFILE,
        collection([
          candidate("stale-confirmed", "CONFIRMED_AS_INCOME", "STALE"),
          candidate("stale-rejected", "REJECTED", "STALE"),
        ]),
      ),
    );
    await renderProfile();

    expect(screen.getByText(/Confirmada anteriormente/)).toBeTruthy();
    expect(screen.getByText(/Rejeitada anteriormente/)).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Remover decisão" })).toHaveLength(2);
    expect(document.body.textContent).not.toContain("9.876,54");
  });

  it("uses possibility language for transfer ambiguity and never labels detection as salary", async () => {
    apiMocks.loadProfileExperience.mockResolvedValueOnce(
      loadResult(
        EMPTY_PROFILE,
        collection([candidate("ambiguous", null, "DETECTED_CANDIDATE", ["TRANSFER_AMBIGUITY"])]),
      ),
    );
    await renderProfile();

    const status = screen.getByText("Aguardando sua revisão").closest("article");
    expect(status).not.toBeNull();
    expect(within(status as HTMLElement).getByText(/pode representar uma transferência/i)).toBeTruthy();
    expect((status as HTMLElement).textContent?.toLowerCase()).not.toContain("salário");
  });
});
