// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TransientAnalysisCandidate } from "./transientAnalysis";

const authMock = vi.hoisted(() => ({
  user: { id: "user-1" } as { id: string } | null,
  token: "token-1" as string | null,
  isLoading: false,
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => authMock,
}));

import { TransientAnalysisProvider, useTransientAnalysis } from "./TransientAnalysisContext";

const projection: TransientAnalysisCandidate = {
  domain: "PLANNING",
  kind: "PROJECTION",
  result: {
    initial_wealth_fact: {
      source: "USER_PROVIDED_SCENARIO",
      amount: "1000.00",
      scope: "USER_PROVIDED_SCENARIO",
      as_of: { reference_month: null, observed_at: "2026-10-23T10:00:00-03:00" },
      provenance: {
        source_type: "USER_PROVIDED_SCENARIO",
        goal_id: null,
        account_id: null,
        reference_month: null,
        run_id: null,
        created_at: null,
        updated_at: null,
      },
    },
    assumptions: {
      as_of_date: "2026-10-23",
      scenario_monthly_contribution: "100.00",
      expected_return_rate: "0.05",
      return_type: "REAL",
      output_mode: "REAL",
      inflation_rate: null,
      horizon_months: 12,
      target_date: null,
      rate_basis: "EFFECTIVE_ANNUAL",
      contribution_timing: "END_OF_MONTH",
    },
    effective_projection_annual_rate: "0.05",
    monthly_equivalent_rate: "0.004074123783648302",
    periods: [],
    initial_wealth: "1000.00",
    final_wealth: "2250.00",
    total_contributions: "1200.00",
    total_projected_growth: "50.00",
    as_of_date: "2026-10-23",
    horizon_months: 12,
  },
};

const replacement: TransientAnalysisCandidate = {
  ...projection,
  result: { ...projection.result, final_wealth: "3000.00" },
};

function Harness() {
  const { selection, selectAnalysis, clearSelection } = useTransientAnalysis();
  const selectionText = selection?.domain === "PLANNING" && selection.kind === "PROJECTION"
    ? `${selection.domain}:${selection.kind}:${selection.result.final_wealth}`
    : selection
      ? `${selection.domain}:${selection.kind}`
      : "EMPTY";
  return (
    <div>
      <output>{selectionText}</output>
      <button type="button" onClick={() => selectAnalysis(projection)}>Selecionar</button>
      <button type="button" onClick={() => selectAnalysis(replacement)}>Substituir</button>
      <button type="button" onClick={clearSelection}>Limpar</button>
    </div>
  );
}

function renderProvider() {
  return render(<TransientAnalysisProvider><Harness /></TransientAnalysisProvider>);
}

afterEach(() => cleanup());

beforeEach(() => {
  authMock.user = { id: "user-1" };
  authMock.token = "token-1";
  authMock.isLoading = false;
});

describe("TransientAnalysisProvider", () => {
  it("keeps one validated selection only in the mounted memory scope", () => {
    const view = renderProvider();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));
    expect(screen.getByText("PLANNING:PROJECTION:2250.00")).toBeTruthy();

    view.unmount();
    renderProvider();
    expect(screen.getByText("EMPTY")).toBeTruthy();
  });

  it("clears immediately on logout, token replacement, or identity change", async () => {
    const view = renderProvider();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));

    authMock.token = null;
    authMock.user = null;
    view.rerender(<TransientAnalysisProvider><Harness /></TransientAnalysisProvider>);
    expect(screen.getByText("EMPTY")).toBeTruthy();

    authMock.user = { id: "user-2" };
    authMock.token = "token-2";
    view.rerender(<TransientAnalysisProvider><Harness /></TransientAnalysisProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));
    expect(screen.getByText("PLANNING:PROJECTION:2250.00")).toBeTruthy();

    authMock.token = "replacement-token";
    view.rerender(<TransientAnalysisProvider><Harness /></TransientAnalysisProvider>);
    expect(screen.getByText("EMPTY")).toBeTruthy();
    await waitFor(() => expect(screen.getByText("EMPTY")).toBeTruthy());
  });

  it("fails closed without a fully resolved authenticated identity", () => {
    authMock.user = null;
    authMock.token = null;
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    renderProvider();

    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));

    expect(screen.getByText("EMPTY")).toBeTruthy();
    expect(storageSpy).not.toHaveBeenCalled();
    storageSpy.mockRestore();
  });

  it("supports explicit clearing", () => {
    renderProvider();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));
    fireEvent.click(screen.getByRole("button", { name: "Limpar" }));
    expect(screen.getByText("EMPTY")).toBeTruthy();
  });

  it("replaces the single active selection explicitly", () => {
    renderProvider();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar" }));
    fireEvent.click(screen.getByRole("button", { name: "Substituir" }));
    expect(screen.getByText("PLANNING:PROJECTION:3000.00")).toBeTruthy();
    expect(screen.queryByText("PLANNING:PROJECTION:2250.00")).toBeNull();
  });
});
