// @vitest-environment jsdom

import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchFromAPIMock = vi.hoisted(() => vi.fn());
const navigationMock = vi.hoisted(() => ({
  pathname: "/wealth-intelligence/health",
  query: "",
  push: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("@/lib/api", () => ({ fetchFromAPI: fetchFromAPIMock }));
vi.mock("next/navigation", () => ({
  usePathname: () => navigationMock.pathname,
  useRouter: () => ({ push: navigationMock.push, replace: navigationMock.replace }),
  useSearchParams: () => new URLSearchParams(navigationMock.query),
}));
vi.mock("@/lib/wealthHome", () => ({
  getCurrentReferenceMonth: () => "2026-10",
  resolveReferenceMonth: (candidate: string | null) => {
    if (candidate === null) return { month: "2026-10", issue: null };
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(candidate)) {
      return { month: "2026-10", issue: "INVALID" };
    }
    if (candidate > "2026-10") return { month: "2026-10", issue: "FUTURE" };
    return { month: candidate, issue: null };
  },
}));
vi.mock("@/components/layout/PageLayout", () => ({
  PageLayout: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("./components/HealthSummaryCards", () => ({
  HealthSummaryCards: ({ cashflow, trends }: { cashflow: { reference_month: string }; trends: { requested_reference_month: string } }) => (
    <div data-testid="health-summary">{cashflow.reference_month}|{trends.requested_reference_month}</div>
  ),
}));
vi.mock("./components/HealthHistorySection", () => ({
  HealthHistorySection: ({ history }: { history: unknown[] }) => <div>Histórico: {history.length}</div>,
}));
vi.mock("./components/CategoryExpenseSection", () => ({
  CategoryExpenseSection: ({ summary }: { summary: { categories: unknown[] } }) => <div>Categorias: {summary.categories.length}</div>,
}));
vi.mock("./components/SpendingAnomalySection", () => ({
  SpendingAnomalySection: ({ summary }: { summary: { anomalies: unknown[] } }) => <div>Sinais: {summary.anomalies.length}</div>,
}));
vi.mock("./components/CategoryTrendSection", () => ({
  CategoryTrendSection: ({ trends }: { trends: { status: string } }) => <div>Tendências: {trends.status}</div>,
}));

import { FinancialHealthExperience, loadFinancialHealth } from "./page";

function responseFor(endpoint: string) {
  const month = new URLSearchParams(endpoint.split("?")[1]).get("reference_month") ?? "missing";
  if (endpoint.includes("/cashflow")) {
    return {
      reference_month: month,
      total_income: "1000.00",
      total_expense: "600.00",
      net_cashflow: "400.00",
      savings_amount: "400.00",
      savings_rate: "0.4",
      average_monthly_income: null,
      average_monthly_expense: null,
      average_monthly_net_cashflow: null,
    };
  }
  if (endpoint.includes("/history")) return [];
  if (endpoint.includes("/categories")) {
    return { reference_month: month, total_expense: "0.00", categories: [], top_category: null };
  }
  if (endpoint.includes("/anomalies")) {
    return { target_reference_month: month, global_status: "INSUFFICIENT_BASELINE", evaluations: [], anomalies: [] };
  }
  return {
    requested_reference_month: month,
    trend_target_month: month,
    comparison_month: "2026-08",
    status: "INSUFFICIENT_DATA",
    global: { status: "INSUFFICIENT_DATA", metrics: [] },
    categories: { status: "INSUFFICIENT_DATA", items: [] },
  };
}

afterEach(() => cleanup());

beforeEach(() => {
  navigationMock.query = "";
  navigationMock.push.mockReset();
  navigationMock.replace.mockReset();
  fetchFromAPIMock.mockReset();
  fetchFromAPIMock.mockImplementation(async (endpoint: string) => responseFor(endpoint));
});

describe("Financial Health URL period", () => {
  it("uses a direct URL month for every certified Health read", async () => {
    navigationMock.query = "month=2026-09&view=compact";
    render(<FinancialHealthExperience />);

    expect((await screen.findByTestId("health-summary")).textContent).toBe("2026-09|2026-09");
    expect((screen.getByLabelText("Mês de referência") as HTMLInputElement).value).toBe("2026-09");
    expect(fetchFromAPIMock.mock.calls.map(([endpoint]) => endpoint)).toEqual([
      "/financial-health/cashflow?reference_month=2026-09",
      "/financial-health/history?reference_month=2026-09",
      "/financial-health/categories?reference_month=2026-09",
      "/financial-health/anomalies?reference_month=2026-09",
      "/financial-health/trends?reference_month=2026-09",
    ]);
    expect(navigationMock.replace).not.toHaveBeenCalled();
  });

  it.each(["", "month=inválido", "month=2026-11"])(
    "normalizes an absent, invalid, or future month (%s)",
    async (query) => {
      navigationMock.query = query;
      render(<FinancialHealthExperience />);

      expect((await screen.findByTestId("health-summary")).textContent).toBe("2026-10|2026-10");
      expect(navigationMock.replace).toHaveBeenCalledWith(
        "/wealth-intelligence/health?month=2026-10",
        { scroll: false },
      );
      expect(fetchFromAPIMock).toHaveBeenCalledTimes(5);
    },
  );

  it("pushes a period change while preserving other query parameters", async () => {
    navigationMock.query = "month=2026-09&view=compact";
    render(<FinancialHealthExperience />);
    await screen.findByTestId("health-summary");

    fireEvent.change(screen.getByLabelText("Mês de referência"), {
      target: { value: "2026-08" },
    });
    expect(navigationMock.push).toHaveBeenCalledWith(
      "/wealth-intelligence/health?month=2026-08&view=compact",
      { scroll: false },
    );
  });

  it("reacts to back/forward URL changes and ignores a late stale response", async () => {
    const releases = new Map<string, () => void>();
    const gates = new Map<string, Promise<void>>();
    for (const month of ["2026-08", "2026-09"]) {
      gates.set(month, new Promise<void>((resolve) => releases.set(month, resolve)));
    }
    fetchFromAPIMock.mockImplementation((endpoint: string) => {
      const month = new URLSearchParams(endpoint.split("?")[1]).get("reference_month")!;
      return gates.get(month)!.then(() => responseFor(endpoint));
    });

    navigationMock.query = "month=2026-08";
    const view = render(<FinancialHealthExperience />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(5));

    navigationMock.query = "month=2026-09";
    view.rerender(<FinancialHealthExperience />);
    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledTimes(10));

    await act(async () => releases.get("2026-09")!());
    expect((await screen.findByTestId("health-summary")).textContent).toBe("2026-09|2026-09");

    await act(async () => releases.get("2026-08")!());
    expect(screen.getByTestId("health-summary").textContent).toBe("2026-09|2026-09");
  });

  it("deduplicates simultaneous batches and exposes loading, empty and error states", async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    fetchFromAPIMock.mockImplementation((endpoint: string) => gate.then(() => responseFor(endpoint)));

    const first = loadFinancialHealth("2026-07");
    const second = loadFinancialHealth("2026-07");
    expect(second).toBe(first);
    expect(fetchFromAPIMock).toHaveBeenCalledTimes(5);
    release();
    await first;

    navigationMock.query = "month=2026-06";
    fetchFromAPIMock.mockImplementation(async (endpoint: string) => responseFor(endpoint));
    render(<FinancialHealthExperience />);
    expect(screen.getByLabelText("Carregando Saúde Financeira")).toBeTruthy();
    expect(await screen.findByText("Histórico: 0")).toBeTruthy();
    expect(screen.getByText("Categorias: 0")).toBeTruthy();
    expect(screen.getByText("Tendências: INSUFFICIENT_DATA")).toBeTruthy();

    cleanup();
    navigationMock.query = "month=2026-05";
    fetchFromAPIMock.mockRejectedValue(new Error("offline"));
    render(<FinancialHealthExperience />);
    expect((await screen.findByRole("alert")).textContent).toContain("Dados indisponíveis");
  });
});
