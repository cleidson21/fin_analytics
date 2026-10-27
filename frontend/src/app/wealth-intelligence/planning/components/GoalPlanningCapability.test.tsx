// @vitest-environment jsdom

import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Goal } from "@/app/goals/types";
import type { PlanningGoalContext } from "@/lib/planning";

const getPlanningGoalContextMock = vi.hoisted(() => vi.fn());
const projectGoalMock = vi.hoisted(() => vi.fn());
const authState = vi.hoisted(() => ({
  user: { id: "user-1" } as { id: string } | null,
  token: "token-1" as string | null,
  isLoading: false,
}));
const apiErrors = vi.hoisted(() => {
  class TestAuthError extends Error {
    constructor() {
      super("Authentication required");
      this.name = "AuthError";
    }
  }
  class TestAPIRequestError extends Error {
    constructor(
      public readonly status: number,
      public readonly endpoint: string,
    ) {
      super(`API request failed with status ${status}`);
      this.name = "APIRequestError";
    }
  }
  return { TestAuthError, TestAPIRequestError };
});

vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => authState }));
vi.mock("@/lib/api", () => ({
  AuthError: apiErrors.TestAuthError,
  APIRequestError: apiErrors.TestAPIRequestError,
}));
vi.mock("@/lib/planning", () => ({
  getPlanningGoalContext: getPlanningGoalContextMock,
  projectGoal: projectGoalMock,
}));
vi.mock("@/app/wealth-intelligence/components/ShowOnWealthHomeButton", () => ({
  ShowOnWealthHomeButton: () => <button>Mostrar na Visão Geral</button>,
}));
vi.mock("./PlanningResults", () => ({
  GoalPlanningResult: () => <div>Resultado certificado</div>,
}));

import { GoalPlanningCapability } from "./GoalPlanningCapability";

const GOAL_1 = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa";
const GOAL_2 = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb";

const goals: Goal[] = [
  {
    id: GOAL_1,
    user_id: "user-1",
    name: "Reserva de emergência",
    goal_type: "EMERGENCY_RESERVE",
    target_amount: 50000,
    current_amount: 12500,
    monthly_contribution: 750,
    target_date: "2028-12-31",
    status: "ACTIVE",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-10-01T00:00:00Z",
  },
  {
    id: GOAL_2,
    user_id: "user-1",
    name: "Viagem",
    goal_type: "TRAVEL",
    target_amount: 20000,
    current_amount: 3000,
    monthly_contribution: 400,
    target_date: "2027-07-01",
    status: "PAUSED",
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-10-02T00:00:00Z",
  },
];

const context1: PlanningGoalContext = {
  goal_id: GOAL_1,
  name: "Reserva de emergência",
  goal_type: "EMERGENCY_RESERVE",
  status: "ACTIVE",
  target_amount: "50000.00",
  current_amount: "12500.00",
  planned_monthly_contribution: "750.00",
  target_date: "2028-12-31",
};

const context2: PlanningGoalContext = {
  goal_id: GOAL_2,
  name: "Viagem",
  goal_type: "TRAVEL",
  status: "PAUSED",
  target_amount: "20000.00",
  current_amount: "3000.00",
  planned_monthly_contribution: "400.00",
  target_date: "2027-07-01",
};

function contextFor(goalId: string) {
  return goalId === GOAL_1 ? context1 : context2;
}

async function waitForContext(name: string) {
  const summary = await screen.findByLabelText("Contexto autenticado da meta");
  await waitFor(() => expect(within(summary).getByText(name)).toBeTruthy());
  return summary;
}

afterEach(() => cleanup());

beforeEach(() => {
  authState.user = { id: "user-1" };
  authState.token = "token-1";
  authState.isLoading = false;
  getPlanningGoalContextMock.mockReset();
  getPlanningGoalContextMock.mockImplementation(async (goalId: string) => contextFor(goalId));
  projectGoalMock.mockReset();
  projectGoalMock.mockResolvedValue({ status: "PROJECTED_ON_TIME" });
});

describe("GoalPlanningCapability", () => {
  it("loads a deep-linked Goal, shows localized facts, and applies only approved presets", async () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={GOAL_1} />,
    );

    const summary = await waitForContext("Reserva de emergência");
    expect(getPlanningGoalContextMock).toHaveBeenCalledWith(GOAL_1);
    expect(within(summary).getByText(/Reserva de Emergência · Ativa/)).toBeTruthy();
    expect(within(summary).getByText("R$ 50.000,00")).toBeTruthy();
    expect(within(summary).getByText("R$ 12.500,00")).toBeTruthy();
    expect(within(summary).getByText("R$ 750,00/mês")).toBeTruthy();
    expect(within(summary).getByText("31/12/2028")).toBeTruthy();
    expect((screen.getByLabelText("Origem do patrimônio inicial") as HTMLSelectElement).value).toBe(
      "GOAL_CURRENT_AMOUNT",
    );
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe(
      "R$ 750,00",
    );
    expect((screen.getByLabelText("Retorno esperado ao ano") as HTMLInputElement).value).toBe("");
    expect((screen.getByLabelText("Horizonte (meses)") as HTMLInputElement).value).toBe("");
    expect(screen.queryByLabelText("Patrimônio inicial")).toBeNull();
    expect(screen.queryByText("Hoje")).toBeNull();
    expect(screen.getByRole("button", { name: /Opções avançadasValores nominais/i })).toBeTruthy();
    expect(projectGoalMock).not.toHaveBeenCalled();
    expect(storageSpy).not.toHaveBeenCalled();
    storageSpy.mockRestore();
  });

  it("switches Goals directly when the form is intact", async () => {
    render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={GOAL_1} />,
    );
    await waitForContext("Reserva de emergência");

    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_2 },
    });

    await waitForContext("Viagem");
    expect((screen.getByRole("combobox", { name: "Meta" }) as HTMLSelectElement).value).toBe(GOAL_2);
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe("R$ 400,00");
    expect(screen.queryByText("Aplicar dados desta meta")).toBeNull();
    expect(projectGoalMock).not.toHaveBeenCalled();
  });

  it("keeps edited assumptions and the active Goal until a pending switch is confirmed", async () => {
    render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={GOAL_1} />,
    );
    await waitForContext("Reserva de emergência");
    const contribution = screen.getByLabelText("Aporte mensal") as HTMLInputElement;
    fireEvent.change(contribution, { target: { value: "R$ 900,00" } });

    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_2 },
    });
    expect(await screen.findByText("Aplicar dados de Viagem?")).toBeTruthy();
    expect(contribution.value).toBe("R$ 900,00");
    expect((screen.getByRole("combobox", { name: "Meta" }) as HTMLSelectElement).value).toBe(GOAL_1);
    expect((screen.getByRole("button", { name: "Analisar meta" }) as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByText("Aplicar dados de Viagem?")).toBeNull();
    expect(contribution.value).toBe("R$ 900,00");
    expect((screen.getByRole("combobox", { name: "Meta" }) as HTMLSelectElement).value).toBe(GOAL_1);

    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_2 },
    });
    await screen.findByText("Aplicar dados de Viagem?");
    fireEvent.click(screen.getByRole("button", { name: "Aplicar dados desta meta" }));

    await waitForContext("Viagem");
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe("R$ 400,00");
    expect((screen.getByRole("combobox", { name: "Meta" }) as HTMLSelectElement).value).toBe(GOAL_2);
    expect(projectGoalMock).not.toHaveBeenCalled();
  });

  it("ignores an obsolete Goal response after a faster later selection", async () => {
    let resolveFirst!: (value: PlanningGoalContext) => void;
    let resolveSecond!: (value: PlanningGoalContext) => void;
    getPlanningGoalContextMock.mockImplementation((goalId: string) => new Promise((resolve) => {
      if (goalId === GOAL_1) resolveFirst = resolve;
      else resolveSecond = resolve;
    }));
    render(<GoalPlanningCapability goals={goals} loadingGoals={false} />);

    const selector = screen.getByRole("combobox", { name: "Meta" });
    fireEvent.change(selector, { target: { value: GOAL_1 } });
    await waitFor(() => expect(getPlanningGoalContextMock).toHaveBeenCalledWith(GOAL_1));
    fireEvent.change(selector, { target: { value: GOAL_2 } });
    await waitFor(() => expect(getPlanningGoalContextMock).toHaveBeenCalledWith(GOAL_2));

    await act(async () => resolveSecond(context2));
    await waitForContext("Viagem");
    await act(async () => resolveFirst(context1));

    expect(within(screen.getByLabelText("Contexto autenticado da meta")).queryByText("Reserva de emergência")).toBeNull();
    expect((selector as HTMLSelectElement).value).toBe(GOAL_2);
  });

  it("surfaces a non-enumerating 404 without applying a Goal", async () => {
    getPlanningGoalContextMock.mockRejectedValue(
      new apiErrors.TestAPIRequestError(404, `/planning/goals/${GOAL_1}/context`),
    );
    render(<GoalPlanningCapability goals={goals} loadingGoals={false} />);

    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_1 },
    });

    expect(await screen.findByText(/não foi encontrada ou não está disponível/i)).toBeTruthy();
    expect(screen.queryByLabelText("Contexto autenticado da meta")).toBeNull();
    expect(projectGoalMock).not.toHaveBeenCalled();
  });

  it("clears Goal financial context after a 401", async () => {
    getPlanningGoalContextMock
      .mockResolvedValueOnce(context1)
      .mockRejectedValueOnce(new apiErrors.TestAuthError());
    render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={GOAL_1} />,
    );
    await waitForContext("Reserva de emergência");

    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_2 },
    });

    expect(await screen.findByText(/sessão expirou/i)).toBeTruthy();
    expect(screen.queryByLabelText("Contexto autenticado da meta")).toBeNull();
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe("");
    expect((screen.getByRole("combobox", { name: "Meta" }) as HTMLSelectElement).value).toBe("");
  });

  it("clears transient Goal context on logout or authenticated identity change", async () => {
    const { rerender } = render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={null} />,
    );
    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_1 },
    });
    await waitForContext("Reserva de emergência");

    authState.user = null;
    authState.token = null;
    rerender(<GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={null} />);
    await waitFor(() => expect(screen.queryByLabelText("Contexto autenticado da meta")).toBeNull());
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe("");

    authState.user = { id: "user-2" };
    authState.token = "token-2";
    const user2Goals = goals.map((goal) => ({ ...goal, user_id: "user-2" }));
    rerender(<GoalPlanningCapability goals={user2Goals} loadingGoals={false} initialGoalId={null} />);
    fireEvent.change(screen.getByRole("combobox", { name: "Meta" }), {
      target: { value: GOAL_2 },
    });
    await waitForContext("Viagem");

    authState.user = { id: "user-3" };
    authState.token = "token-3";
    rerender(<GoalPlanningCapability goals={user2Goals} loadingGoals={false} initialGoalId={null} />);
    await waitFor(() => expect(screen.queryByLabelText("Contexto autenticado da meta")).toBeNull());
    expect((screen.getByLabelText("Aporte mensal") as HTMLInputElement).value).toBe("");
  });

  it("submits only after explicit action and never sends Goal facts as manual wealth", async () => {
    render(
      <GoalPlanningCapability goals={goals} loadingGoals={false} initialGoalId={GOAL_1} />,
    );
    await waitForContext("Reserva de emergência");
    expect(projectGoalMock).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Retorno esperado ao ano"), {
      target: { value: "8" },
    });
    fireEvent.change(screen.getByLabelText("Horizonte (meses)"), {
      target: { value: "24", valueAsNumber: 24 },
    });
    fireEvent.click(screen.getByRole("button", { name: "Analisar meta" }));

    await waitFor(() => expect(projectGoalMock).toHaveBeenCalledTimes(1));
    const [submittedGoalId, request] = projectGoalMock.mock.calls[0];
    expect(submittedGoalId).toBe(GOAL_1);
    expect(request).toMatchObject({
      initial_wealth: { source: "GOAL_CURRENT_AMOUNT" },
      assumptions: {
        scenario_monthly_contribution: "750.00",
        expected_return_rate: "0.08",
        horizon_months: 24,
        target_date: null,
      },
      target_value_basis: null,
    });
    const serialized = JSON.stringify(request);
    expect(serialized).not.toContain(context1.current_amount as string);
    expect(serialized).not.toContain(context1.target_amount);
  });
});
