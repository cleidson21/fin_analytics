// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.stubEnv("NEXT_PUBLIC_API_URL", "https://example.test/api/v1");
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/components/layout/PageLayout", () => ({ PageLayout: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }));
vi.mock("recharts", () => ({ Line: () => null, LineChart: () => null }));
const { DashboardPage } = await import("./DashboardPage");

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("fin_token", "synthetic-token");
  localStorage.setItem("pierre_last_sync", "previous successful synchronization");
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function responses(importResponse: Response, deniedReads = false) {
  const fetchMock = vi.fn(async (url: string, options: RequestInit) => {
    if (options.method === "POST") return importResponse;
    if (deniedReads) return new Response("{}", { status: 403 });
    const body = url.includes("summary-v2") ? {
      receitas: { current: 12, previous: 10, delta_pct: 20 }, despesas: { current: 5, previous: 5, delta_pct: 0 },
      saldo_liquido: { current: 7, previous: 5, delta_pct: 40 }, patrimonio: { current: 7, previous: 5, delta_pct: 40 },
    } : url.includes("pacing") ? {
      current_expenses: 5, previous_expenses: 5, delta_percentage: 0, daily_data: [],
    } : url.includes("governance/transactions") ? { items: [], total: 0 } : [];
    return new Response(JSON.stringify(body), { status: 200 });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

it("uses the existing Importar Dados button and updates synchronization only after committed success", async () => {
  const fetchMock = responses(new Response(JSON.stringify({ success: true, transactions: 2, skipped: 1 }), { status: 200 }));
  render(<DashboardPage />);
  await waitFor(() => expect(screen.getByText("Última sync: previous successful synchronization")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: "Importar Dados" }));
  await waitFor(() => expect(screen.getByText(/2 importadas, 1 ignoradas/)).toBeTruthy());
  expect(localStorage.getItem("pierre_last_sync")).not.toBe("previous successful synchronization");
  expect(fetchMock.mock.calls.some(([url, options]) => url.endsWith("/pierre/import") && options.method === "POST")).toBe(true);
});

it("shows authorization pending, hides financial results and preserves the session and last successful sync on 403", async () => {
  responses(new Response("{}", { status: 403 }), true);
  render(<DashboardPage />);
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Autorização financeira pendente"));
  fireEvent.click(screen.getByRole("button", { name: "Importar Dados" }));
  await waitFor(() => expect(screen.getAllByText(/Autorização financeira pendente/).length).toBeGreaterThan(0));
  expect(localStorage.getItem("fin_token")).toBe("synthetic-token");
  expect(localStorage.getItem("pierre_last_sync")).toBe("previous successful synchronization");
  expect(screen.queryByText("Patrimônio Total")).toBeNull();
});

it.each([
  new Response("{}", { status: 502 }),
  new Response(JSON.stringify({ success: false, error_message: "Synthetic failure" }), { status: 200 }),
  new Response(JSON.stringify({ success: true, status: "partial", errors: 1 }), { status: 200 }),
])("does not announce success or advance synchronization after failure or partial output", async (response) => {
  responses(response);
  render(<DashboardPage />);
  fireEvent.click(screen.getByRole("button", { name: "Importar Dados" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Importar Dados" })).not.toHaveProperty("disabled", true));
  expect(localStorage.getItem("pierre_last_sync")).toBe("previous successful synchronization");
  expect(screen.queryByText(/importadas,/)).toBeNull();
});
