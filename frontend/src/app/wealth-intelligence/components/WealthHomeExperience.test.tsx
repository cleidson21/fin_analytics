// @vitest-environment jsdom

import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { WealthHomeReadModel } from "@/lib/wealthHome";
import type { FireAnalysisResponse } from "@/lib/fire";
import type { TransientAnalysisSelection } from "../transientAnalysis";

const loadWealthHomeMock = vi.hoisted(() => vi.fn());
const navigationMock = vi.hoisted(() => ({
  pathname: "/wealth-intelligence",
  query: "",
  push: vi.fn(),
  replace: vi.fn(),
}));
const transientAnalysisMock = vi.hoisted(() => ({
  selection: null as TransientAnalysisSelection | null,
  selectAnalysis: vi.fn(),
  clearSelection: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigationMock.pathname,
  useRouter: () => ({ push: navigationMock.push, replace: navigationMock.replace }),
  useSearchParams: () => new URLSearchParams(navigationMock.query),
}));

vi.mock("../TransientAnalysisContext", () => ({
  useTransientAnalysis: () => transientAnalysisMock,
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
  loadWealthHome: loadWealthHomeMock,
}));

import { WealthHomeExperience } from "./WealthHomeExperience";

const SUCCESS_RESPONSE: WealthHomeReadModel = {
  contract_version: "wealth-home-v2",
  status: "AVAILABLE",
  reference_month: "2026-10",
  scope: "AUTHENTICATED_SINGLE_USER",
  generated_at: "2026-10-22T14:30:00Z",
  health: {
    status: "AVAILABLE",
    reference_month: "2026-10",
    currency: "BRL",
    net_cashflow: "3376.55",
    reason: null,
    source: {
      authority: "FINANCIAL_HEALTH",
      reader: "PlanningHealthReadAdapter",
      version: "10.2",
      scope: "CONSOLIDATED_LOCAL_TENANT",
      read_at: "2026-10-22T14:30:00Z",
      updated_at: null,
      freshness: "PARTIAL_PERIOD",
      completeness: "UNKNOWN",
    },
  },
  goals: {
    status: "AVAILABLE",
    total_count: 4,
    by_status: [
      { status: "ACTIVE", count: 2 },
      { status: "ACHIEVED", count: 1 },
      { status: "PAUSED", count: 1 },
      { status: "CANCELLED", count: 0 },
    ],
    reason: null,
    source: {
      authority: "GOALS",
      reader: "PlanningGoalReadQuery",
      version: "10.3.1",
      scope: "AUTHENTICATED_USER_OWNED_GOALS",
      read_at: "2026-10-22T14:30:00Z",
      updated_at: "2026-10-20T10:00:00Z",
      freshness: "CURRENT",
      completeness: "COMPLETE",
    },
  },
  investments: {
    status: "AVAILABLE",
    requested_reference_month: "2026-10",
    snapshot_reference_month: "2026-09",
    currency: "BRL",
    investment_wealth: "842450.00",
    source_type: "MYPROFIT_EVOLUCAO",
    portfolio_scope: "portfolio-synthetic-01",
    run_id: "run-synthetic-01",
    reason: null,
    source: {
      authority: "INVESTMENT_PORTFOLIO",
      reader: "PlanningPortfolioSourceResolver",
      version: "10.3.10B1",
      scope: "AUTHENTICATED_CANONICAL_MYPROFIT_PORTFOLIO",
      read_at: "2026-10-22T14:30:00Z",
      updated_at: "2026-09-30T10:00:00Z",
      freshness: "CLOSED_PERIOD",
      completeness: "UNKNOWN",
    },
  },
};

const FIRE_RESPONSE: FireAnalysisResponse = {
  analysis_type: "SUMMARY",
  as_of_date: "2026-10-20",
  basis: "REAL",
  summary: {
    monthly_retirement_spending: "5000.00",
    annual_required_spending: "60000.00",
    assumed_annual_withdrawal_rate: "0.04",
    fire_target: "1500000.00",
    eligible_investment_wealth: "800000.00",
    gap_to_fire: "700000.00",
    progress_ratio: "0.53333333",
    supported_annual_withdrawal: "32000.00",
    supported_monthly_withdrawal: "2666.67",
    summary_status: "BELOW_FIRE_TARGET",
  },
  projection: null,
  required_contribution: null,
  assumptions: {
    monthly_retirement_spending: "5000.00",
    assumed_annual_withdrawal_rate: "0.04",
    expected_return_rate: null,
    return_type: null,
    inflation_rate: null,
    scenario_monthly_contribution: null,
    horizon_months: null,
    desired_fire_date: null,
  },
  provenance: {
    initial_wealth_fact: {
      source: "INVESTMENT_PORTFOLIO_SNAPSHOT",
      amount: "800000.00",
      scope: "INVESTMENT_PORTFOLIO",
      as_of: { reference_month: "2026-09", observed_at: null },
      provenance: {
        source_type: "MYPROFIT_EVOLUCAO",
        goal_id: null,
        account_id: null,
        reference_month: "2026-09",
        run_id: "fire-run-01",
        created_at: null,
        updated_at: "2026-09-30T10:00:00Z",
      },
    },
  },
};

afterEach(() => cleanup());

beforeEach(() => {
  navigationMock.query = "";
  navigationMock.push.mockReset();
  navigationMock.replace.mockReset();
  loadWealthHomeMock.mockReset();
  loadWealthHomeMock.mockResolvedValue(SUCCESS_RESPONSE);
  transientAnalysisMock.selection = null;
  transientAnalysisMock.clearSelection.mockReset();
});

describe("WealthHomeExperience", () => {
  it("loads the authenticated contract and keeps each card origin explicit", async () => {
    render(<WealthHomeExperience />);

    expect(screen.getByLabelText("Carregando visão geral")).toBeTruthy();
    expect(screen.getByText("Lendo dados governados com escopo autenticado…")).toBeTruthy();
    expect(await screen.findByText("R$ 3.376,55")).toBeTruthy();
    expect(screen.queryByText(/Seu panorama financeiro/i)).toBeNull();
    expect(screen.queryByText(/Contrato: wealth-home/i)).toBeNull();
    expect(screen.getByText("R$ 842.450,00")).toBeTruthy();
    expect(screen.getByText("Patrimônio de investimentos")).toBeTruthy();
    expect(screen.getByText(/Último snapshot elegível: 09\/2026 · solicitado: 10\/2026/i)).toBeTruthy();
    expect(screen.getByText("MYPROFIT_EVOLUCAO")).toBeTruthy();
    expect(screen.queryByText(/PlanningPortfolioSourceResolver v10.3.10B1/i)).toBeNull();
    expect(screen.getByText("Metas autenticadas")).toBeTruthy();
    expect(screen.getByText("Fotografia atual · 2 ativas · 1 concluídas · 1 pausadas")).toBeTruthy();
    expect(screen.getAllByText("Governado")).toHaveLength(3);
    expect(screen.getAllByText("Demonstração").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/completude não certificada/i)).toBeTruthy();
    expect(screen.getByText("período em aberto")).toBeTruthy();
    expect(screen.getByText(/Evolução e alocação indisponíveis/i)).toBeTruthy();
    expect(screen.queryByText(/Histórico sintético/i)).toBeNull();
    expect(screen.queryByRole("dialog", { name: "Proveniência de Investments" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Detalhes de proveniência" }));
    expect(screen.getByRole("dialog", { name: "Proveniência de Investments" })).toBeTruthy();
    expect(screen.getByText(/PlanningPortfolioSourceResolver v10.3.10B1/i)).toBeTruthy();
    expect(screen.getByText(/Snapshot anterior ao mês solicitado/i)).toBeTruthy();
    expect(screen.getByText(/run-synthetic-01/i)).toBeTruthy();
    expect(screen.getByText(/AUTHENTICATED_CANONICAL_MYPROFIT_PORTFOLIO/i)).toBeTruthy();
    const technicalSummary = screen.getByText("Detalhes técnicos").closest("summary") as HTMLElement;
    expect(technicalSummary).toBeTruthy();
    const closeButton = screen.getByRole("button", { name: "Fechar detalhes de proveniência" });
    closeButton.focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(technicalSummary);
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(closeButton);
    fireEvent.click(closeButton);
    expect(screen.queryByRole("dialog", { name: "Proveniência de Investments" })).toBeNull();
    expect(screen.getByText("Nenhum cenário selecionado")).toBeTruthy();
    expect(screen.getByText("Nenhuma análise executada")).toBeTruthy();
    expect(screen.getAllByText("Sob demanda").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("R$ 657.550,00")).toBeNull();
    expect(loadWealthHomeMock).toHaveBeenCalledWith("2026-10");
  });

  it("preserves missing Health as missing while zero owned Goals remains a fact", async () => {
    loadWealthHomeMock.mockResolvedValue({
      ...SUCCESS_RESPONSE,
      status: "INSUFFICIENT_DATA",
      health: {
        ...SUCCESS_RESPONSE.health,
        status: "INSUFFICIENT_DATA",
        net_cashflow: null,
        reason: "NO_CERTIFIED_HEALTH_FACT",
      },
      goals: {
        ...SUCCESS_RESPONSE.goals,
        total_count: 0,
        by_status: SUCCESS_RESPONSE.goals.by_status.map((item) => ({ ...item, count: 0 })),
      },
    });

    render(<WealthHomeExperience />);

    expect(await screen.findByText("Sem dado certificado")).toBeTruthy();
    expect(screen.getByText("Fotografia atual: nenhuma meta autenticada cadastrada")).toBeTruthy();
    expect(screen.queryByText("R$ 0,00")).toBeNull();
  });

  it("renders an explicitly selected FIRE response separately from governed cards", async () => {
    transientAnalysisMock.selection = {
      domain: "FIRE",
      kind: "FIRE_ANALYSIS",
      result: FIRE_RESPONSE,
      selectedAt: "2026-10-23T10:00:00Z",
      validation: "VALIDATED_API_RESPONSE",
    };

    render(<WealthHomeExperience />);

    expect(await screen.findByText("Resultado transitório")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Independência financeira", level: 2 })).toBeTruthy();
    expect(screen.getAllByText("Resposta validada")).toHaveLength(1);
    expect(screen.getByText("R$ 1.500.000,00")).toBeTruthy();
    expect(screen.getByText(/não é patrimônio atual/i)).toBeTruthy();
    expect(screen.getByText("R$ 842.450,00")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Limpar seleção" }));
    expect(transientAnalysisMock.clearSelection).toHaveBeenCalledTimes(1);
  });

  it("shows API failure without falling back to synthetic Health or Goals", async () => {
    loadWealthHomeMock.mockRejectedValue(new Error("offline"));

    render(<WealthHomeExperience />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText(/nenhuma fixture foi usada como substituta/i)).toBeTruthy();
    expect(screen.queryByText("R$ 3.420,00")).toBeNull();
    expect(screen.queryByText("Metas autenticadas")).toBeNull();
  });

  it("shows governed investment absence without falling back to the fixture value", async () => {
    loadWealthHomeMock.mockResolvedValue({
      ...SUCCESS_RESPONSE,
      status: "INSUFFICIENT_DATA",
      investments: {
        ...SUCCESS_RESPONSE.investments,
        status: "INSUFFICIENT_DATA",
        snapshot_reference_month: null,
        investment_wealth: null,
        source_type: null,
        portfolio_scope: null,
        run_id: null,
        reason: "NO_ELIGIBLE_INVESTMENT_SNAPSHOT",
        source: {
          ...SUCCESS_RESPONSE.investments.source,
          updated_at: null,
          freshness: "UNKNOWN",
        },
      },
    });

    render(<WealthHomeExperience />);

    expect(await screen.findByText("Sem dado governado")).toBeTruthy();
    expect(screen.getByText(/Nenhum snapshot MyProfit elegível para 10\/2026/i)).toBeTruthy();
    expect(screen.queryByText("R$ 842.450,00")).toBeNull();
    expect(screen.getByText(/Evolução e alocação indisponíveis/i)).toBeTruthy();
  });

  it("keeps the synthetic experience behind an explicit demonstration mode", async () => {
    render(<WealthHomeExperience />);
    await screen.findByText("R$ 3.376,55");

    fireEvent.click(screen.getByRole("button", { name: "Demonstração" }));

    expect(screen.getByText("Modo demonstrativo")).toBeTruthy();
    expect(screen.getByText("Fixture: wealth-home-demo-v1")).toBeTruthy();
    expect(screen.getByText("R$ 3.420,00")).toBeTruthy();
    expect(screen.getByText(/Histórico sintético/i)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: /Abrir área operacional de investimentos/i }).getAttribute("href"),
    ).toBe("/wealth");

    fireEvent.click(screen.getByRole("button", { name: "Sem dados" }));
    expect(screen.getByText("Ainda não há dados para compor esta visão")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Erro" }));
    expect(screen.getByText(/erro demonstrativo/i)).toBeTruthy();
  });

  it("keeps Advisor disabled and navigation on approved routes", async () => {
    render(<WealthHomeExperience />);
    const advisorLabel = await screen.findByText("Advisor experimental");
    const advisorDetails = advisorLabel.closest("details") as HTMLDetailsElement;
    expect(advisorDetails.open).toBe(false);
    fireEvent.click(advisorLabel.closest("summary") as HTMLElement);
    expect(advisorDetails.open).toBe(true);

    expect(screen.getByText("Inferência desativada")).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: /Executar Advisor/i }) as HTMLButtonElement).disabled,
    ).toBe(true);
    const healthLinks = screen.getAllByRole("link").filter((link) =>
      link.getAttribute("href")?.startsWith("/wealth-intelligence/health"),
    );
    expect(healthLinks).toHaveLength(1);
    expect(healthLinks.every((link) => link.getAttribute("href") === "/wealth-intelligence/health?month=2026-10")).toBe(true);
    expect(
      screen.getByRole("link", { name: /Abrir detalhamento de Saúde Financeira/i }).getAttribute("href"),
    ).toBe("/wealth-intelligence/health?month=2026-10");
    expect(screen.getByRole("link", { name: /Abrir Metas/i }).getAttribute("href")).toBe(
      "/wealth-intelligence/goals",
    );
    expect(screen.getByRole("link", { name: /Abrir Planejamento/i }).getAttribute("href")).toBe(
      "/wealth-intelligence/planning?intent=simulate&from=wealth-home",
    );
    expect(screen.getByRole("link", { name: "Abrir FIRE" }).getAttribute("href")).toBe(
      "/wealth-intelligence/fire?from=wealth-home",
    );
    expect(screen.queryByRole("link", { name: /Abrir área operacional de investimentos/i })).toBeNull();
  });

  it("retries the authenticated read after an error", async () => {
    loadWealthHomeMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(SUCCESS_RESPONSE);
    render(<WealthHomeExperience />);
    await screen.findByRole("alert");

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    await waitFor(() => expect(loadWealthHomeMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("R$ 3.376,55")).toBeTruthy();
  });

  it("uses the URL month and pushes a changed month into browser history", async () => {
    navigationMock.query = "month=2026-09&view=compact";
    render(<WealthHomeExperience />);

    await waitFor(() => expect(loadWealthHomeMock).toHaveBeenCalledWith("2026-09"));
    const selector = screen.getByLabelText("Mês de referência da Wealth Home") as HTMLInputElement;
    expect(selector.value).toBe("2026-09");
    const healthLinks = screen.getAllByRole("link").filter((link) =>
      link.getAttribute("href")?.startsWith("/wealth-intelligence/health"),
    );
    expect(healthLinks).toHaveLength(1);
    expect(healthLinks.every((link) => link.getAttribute("href") === "/wealth-intelligence/health?month=2026-09&view=compact")).toBe(true);

    fireEvent.change(selector, { target: { value: "2026-08" } });
    expect(navigationMock.push).toHaveBeenCalledWith(
      "/wealth-intelligence?month=2026-08&view=compact",
      { scroll: false },
    );
  });

  it.each(["month=not-a-month", "month=2026-11"])(
    "normalizes an invalid or future URL month (%s) without querying it",
    async (query) => {
      navigationMock.query = query;
      render(<WealthHomeExperience />);

      await waitFor(() => expect(loadWealthHomeMock).toHaveBeenCalledWith("2026-10"));
      expect(navigationMock.replace).toHaveBeenCalledWith(
        "/wealth-intelligence?month=2026-10",
        { scroll: false },
      );
      expect(loadWealthHomeMock).toHaveBeenCalledTimes(1);
    },
  );

  it("ignores a stale response after the URL month changes", async () => {
    let resolveSeptember!: (value: WealthHomeReadModel) => void;
    let resolveOctober!: (value: WealthHomeReadModel) => void;
    const september = new Promise<WealthHomeReadModel>((resolve) => { resolveSeptember = resolve; });
    const october = new Promise<WealthHomeReadModel>((resolve) => { resolveOctober = resolve; });
    loadWealthHomeMock.mockImplementation((month: string) => month === "2026-09" ? september : october);
    navigationMock.query = "month=2026-09";
    const view = render(<WealthHomeExperience />);
    await waitFor(() => expect(loadWealthHomeMock).toHaveBeenCalledWith("2026-09"));

    navigationMock.query = "month=2026-10";
    view.rerender(<WealthHomeExperience />);
    await waitFor(() => expect(loadWealthHomeMock).toHaveBeenCalledWith("2026-10"));

    await act(async () => {
      resolveOctober({ ...SUCCESS_RESPONSE, health: { ...SUCCESS_RESPONSE.health, net_cashflow: "5000.00" } });
    });
    expect(await screen.findByText("R$ 5.000,00")).toBeTruthy();

    await act(async () => {
      resolveSeptember({ ...SUCCESS_RESPONSE, health: { ...SUCCESS_RESPONSE.health, net_cashflow: "1000.00" } });
    });
    expect(screen.queryByText("R$ 1.000,00")).toBeNull();
    expect(screen.getByText("R$ 5.000,00")).toBeTruthy();
  });
});
