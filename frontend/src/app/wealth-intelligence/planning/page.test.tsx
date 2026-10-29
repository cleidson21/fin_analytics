// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchFromAPIMock = vi.hoisted(() => vi.fn());
const authState = vi.hoisted(() => ({
  user: { id: "user-1" } as { id: string } | null,
  token: "token-1" as string | null,
  isLoading: false,
}));
const navigationMock = vi.hoisted(() => ({
  pathname: "/wealth-intelligence/planning",
  query: "",
  push: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigationMock.pathname,
  useRouter: () => ({ push: navigationMock.push, replace: navigationMock.replace }),
  useSearchParams: () => new URLSearchParams(navigationMock.query),
}));

vi.mock("@/lib/api", () => ({ fetchFromAPI: fetchFromAPIMock, AuthError: class AuthError extends Error {} }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => authState }));
vi.mock("@/components/layout/PageLayout", () => ({
  PageLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("./components/ProjectionCapability", () => ({
  ProjectionCapability: () => <div>Capacidade de projeção</div>,
}));
vi.mock("./components/TargetCapability", () => ({
  TargetCapability: () => <div>Capacidade de prazo</div>,
}));
vi.mock("./components/RequiredContributionCapability", () => ({
  RequiredContributionCapability: () => <div>Capacidade de aporte</div>,
}));
vi.mock("./components/GoalPlanningCapability", async () => {
  const { useId } = await import("react");
  return { GoalPlanningCapability: ({ initialGoalId }: { initialGoalId?: string | null }) => {
    const instance = useId();
    return <div data-testid="goal-capability" data-instance={instance}>
      Capacidade de meta autenticada
      {initialGoalId ? <span>Meta inicial: {initialGoalId}</span> : null}
    </div>;
  } };
});
vi.mock("./components/ScenarioComparisonCapability", () => ({
  ScenarioComparisonCapability: () => <div>Capacidade de comparação</div>,
}));
vi.mock("./components/GoalBudgetCapability", () => ({
  GoalBudgetCapability: ({ sessionExpired }: { sessionExpired?: boolean }) => <div>{sessionExpired ? "Sessão expirada no fluxo de orçamento" : "Capacidade de orçamento"}</div>,
}));

import PlanningPage from "./page";
import { AuthError } from "@/lib/api";

afterEach(() => cleanup());

beforeEach(() => {
  authState.user = { id: "user-1" };
  authState.token = "token-1";
  authState.isLoading = false;
  navigationMock.query = "";
  navigationMock.push.mockReset();
  navigationMock.replace.mockReset();
  fetchFromAPIMock.mockReset();
  fetchFromAPIMock.mockResolvedValue([]);
});

describe("PlanningPage route integration", () => {
  it("preserves the individual Goal component during a same-session deep-link change", async () => {
    navigationMock.query = "intent=objective&task=goals&goal=00000000-0000-0000-0000-000000000001";
    const view = render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(1));
    const instance = screen.getByTestId("goal-capability").getAttribute("data-instance");
    navigationMock.query = "intent=objective&task=goals&goal=00000000-0000-0000-0000-000000000002";
    view.rerender(<PlanningPage />);
    expect(screen.getByTestId("goal-capability").getAttribute("data-instance")).toBe(instance);
    expect(screen.getByText("Meta inicial: 00000000-0000-0000-0000-000000000002")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Distribuir orçamento" }));
    navigationMock.query = "intent=objective&task=goals&goal=00000000-0000-0000-0000-000000000003";
    view.rerender(<PlanningPage />);
    expect(screen.queryByText("Capacidade de orçamento")).toBeNull();
    expect(screen.getByText("Meta inicial: 00000000-0000-0000-0000-000000000003")).toBeTruthy();
  });
  it("propagates a Goal-list 401 to the budget session gate", async () => {
    fetchFromAPIMock.mockRejectedValue(new AuthError());
    navigationMock.query = "intent=objective&task=goals";
    render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole("button", { name: "Distribuir orçamento" }));
    expect(await screen.findByText("Sessão expirada no fluxo de orçamento")).toBeTruthy();
  });
  it("opens budget distribution inside Goal Objective without a fourth intention or new navigation", async () => {
    navigationMock.query = "intent=objective&task=goals";
    render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
    fireEvent.click(screen.getByRole("button", { name: "Distribuir orçamento" }));
    expect(screen.getByText("Capacidade de orçamento")).toBeTruthy();
    expect(screen.queryByText("Capacidade de meta autenticada")).toBeNull();
    expect(screen.getAllByRole("tablist")).toHaveLength(2);
    expect(navigationMock.push).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Voltar à meta individual" }));
    expect(screen.getByText("Capacidade de meta autenticada")).toBeTruthy();
  });
  it("normalizes a direct route and does not run a planning calculation on open", async () => {
    render(<PlanningPage />);

    expect(screen.getByText("Capacidade de projeção")).toBeTruthy();
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
    expect(fetchFromAPIMock).toHaveBeenCalledTimes(1);
    expect(navigationMock.replace).toHaveBeenCalledWith(
      "/wealth-intelligence/planning?intent=simulate",
      { scroll: false },
    );
  });

  it("restores the authenticated Goal capability from a shared URL", async () => {
    navigationMock.query = "intent=objective&task=goals&from=wealth-home";

    render(<PlanningPage />);

    expect(screen.getByText("Capacidade de meta autenticada")).toBeTruthy();
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
    expect(navigationMock.replace).not.toHaveBeenCalled();
  });

  it("passes only a valid deep-linked Goal identifier to the authenticated capability", async () => {
    const goalId = "abcdefab-1234-5678-90ab-abcdefabcdef";
    navigationMock.query = `intent=objective&task=goals&goal=${goalId}`;

    render(<PlanningPage />);

    expect(screen.getByText(`Meta inicial: ${goalId}`)).toBeTruthy();
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
    expect(navigationMock.replace).not.toHaveBeenCalled();
  });

  it("removes an invalid Goal identifier before mounting any Goal context", async () => {
    navigationMock.query = "intent=objective&task=goals&goal=not-a-uuid";

    render(<PlanningPage />);

    expect(screen.queryByText(/Meta inicial:/)).toBeNull();
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
    expect(navigationMock.replace).toHaveBeenCalledWith(
      "/wealth-intelligence/planning?intent=objective&task=goals",
      { scroll: false },
    );
  });

  it("puts a directly selected mode in browser history without serializing financial inputs", async () => {
    navigationMock.query = "intent=simulate&from=wealth-home";
    render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));

    fireEvent.click(screen.getByRole("tab", { name: "Comparar" }));

    expect(navigationMock.push).toHaveBeenCalledWith(
      "/wealth-intelligence/planning?intent=compare&from=wealth-home",
      { scroll: false },
    );
    expect(navigationMock.push.mock.calls[0][0]).not.toContain("initial_wealth");
  });

  it("opens comparison directly without executing it", async () => {
    navigationMock.query = "intent=compare";

    render(<PlanningPage />);

    expect(screen.getByText("Capacidade de comparação")).toBeTruthy();
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(1));
  });

  it("clears and reloads the Goal list when the authenticated identity changes", async () => {
    navigationMock.query = "intent=objective&task=goals";
    const { rerender } = render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(1));

    authState.user = { id: "user-2" };
    authState.token = "token-2";
    rerender(<PlanningPage />);

    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(2));
    expect(fetchFromAPIMock).toHaveBeenNthCalledWith(1, "/goals", { signal: expect.any(AbortSignal) });
    expect(fetchFromAPIMock).toHaveBeenNthCalledWith(2, "/goals", { signal: expect.any(AbortSignal) });
  });

  it.each([
    ["intent=simulate", "Capacidade de projeção"],
    ["intent=objective&task=target", "Capacidade de prazo"],
    ["intent=objective&task=required", "Capacidade de aporte"],
    ["intent=objective&task=goals", "Capacidade de meta autenticada"],
    ["intent=compare", "Capacidade de comparação"],
  ])("mounts only the capability selected by %s", async (query, expectedCapability) => {
    navigationMock.query = query;

    render(<PlanningPage />);

    expect(screen.getByText(expectedCapability)).toBeTruthy();
    expect(screen.getAllByText(/Capacidade de/)).toHaveLength(1);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));
  });

  it("shows exactly three primary intentions and keeps Objective tasks nested", async () => {
    navigationMock.query = "intent=simulate&from=wealth-home";
    const firstRender = render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));

    expect(screen.getByRole("tab", { name: "Simular" })).toBeTruthy();
    expect(screen.getByRole("tab", { name: "Objetivo" })).toBeTruthy();
    expect(screen.getByRole("tab", { name: "Comparar" })).toBeTruthy();
    expect(screen.queryByRole("tab", { name: "Quando alcanço?" })).toBeNull();
    expect(screen.queryByText("O que você quer descobrir?")).toBeNull();
    expect(screen.queryByRole("link", { name: "Metas" })).toBeNull();

    fireEvent.click(screen.getByRole("tab", { name: "Objetivo" }));

    expect(navigationMock.push).toHaveBeenNthCalledWith(
      1,
      "/wealth-intelligence/planning?intent=objective&from=wealth-home&task=target",
      { scroll: false },
    );

    firstRender.unmount();
    navigationMock.query = "intent=objective&task=target&from=wealth-home";
    render(<PlanningPage />);

    const objectiveTabs = screen.getByRole("tablist", { name: "Tipo de objetivo" });
    expect(objectiveTabs.className).toContain("max-w-3xl");
    expect(objectiveTabs.className).toContain("rounded-xl");
    expect(screen.getByRole("tab", { name: "Quando alcanço?" }).className).toContain("justify-center");
  });

  it("maps the three Objective tasks to the existing route contracts", async () => {
    navigationMock.query = "intent=objective&task=target&from=wealth-home";
    render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));

    expect(screen.getByRole("tab", { name: "Quando alcanço?" }).getAttribute("aria-selected")).toBe("true");
    fireEvent.click(screen.getByRole("tab", { name: "Quanto aportar?" }));
    fireEvent.click(screen.getByRole("tab", { name: "Meta cadastrada" }));

    expect(navigationMock.push).toHaveBeenNthCalledWith(
      1,
      "/wealth-intelligence/planning?intent=objective&task=required&from=wealth-home",
      { scroll: false },
    );
    expect(navigationMock.push).toHaveBeenNthCalledWith(
      2,
      "/wealth-intelligence/planning?intent=objective&task=goals&from=wealth-home",
      { scroll: false },
    );
  });

  it("moves between primary intentions with the keyboard without executing a calculation", async () => {
    navigationMock.query = "intent=simulate";
    render(<PlanningPage />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals", { signal: expect.any(AbortSignal) }));

    const simulate = screen.getByRole("tab", { name: "Simular" });
    simulate.focus();
    fireEvent.keyDown(simulate, { key: "ArrowRight" });

    expect(document.activeElement).toBe(screen.getByRole("tab", { name: "Objetivo" }));
    expect(navigationMock.push).toHaveBeenCalledWith(
      "/wealth-intelligence/planning?intent=objective&task=target",
      { scroll: false },
    );
    expect(fetchFromAPIMock).toHaveBeenCalledTimes(1);
  });
});
