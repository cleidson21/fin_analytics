// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const analyzeFireMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/fire", () => ({ analyzeFire: analyzeFireMock }));
vi.mock("@/components/layout/PageLayout", () => ({
  PageLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("./components/FireInputs", () => ({
  FireInputs: ({ onMode }: { onMode: (mode: "PROJECTED_DATE") => void }) => (
    <button type="button" onClick={() => onMode("PROJECTED_DATE")}>Selecionar projeção de data</button>
  ),
}));
vi.mock("./components/fireForm", () => {
  class FireInputError extends Error {
    field = "field";
  }
  return {
    createFireForm: () => ({ mode: "SUMMARY" }),
    buildFireRequest: () => ({
      analysis_type: "PROJECTED_DATE",
      as_of_date: "2026-10-23",
      target_wealth: "1000000.00",
    }),
    FireInputError,
    normalizeFireMode: (_current: unknown, mode: string) => ({ mode }),
  };
});
vi.mock("./components/FireResults", () => ({
  createFireResultState: () => ({ pending: false, result: null, error: null }),
  beginFireSubmission: () => ({ pending: true, result: null, error: null }),
  completeFireSubmission: (_current: unknown, result: unknown) => ({ pending: false, result, error: null }),
  failFireSubmission: (_current: unknown, error: string) => ({ pending: false, result: null, error }),
  FireResultRegion: ({ state }: { state: { result: unknown } }) => (
    <div>{state.result ? "Resultado FIRE certificado" : "Nenhum resultado FIRE"}</div>
  ),
}));

import FirePage from "./page";

afterEach(() => cleanup());

beforeEach(() => {
  analyzeFireMock.mockReset();
  analyzeFireMock.mockResolvedValue({ status: "AVAILABLE" });
});

describe("FirePage execution boundary", () => {
  it("does not execute FIRE when the page opens or its mode changes", () => {
    render(<FirePage />);

    expect(analyzeFireMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar projeção de data" }));
    expect(analyzeFireMock).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Projetar data" })).toBeTruthy();
  });

  it("executes exactly once after explicit confirmation", async () => {
    render(<FirePage />);
    fireEvent.click(screen.getByRole("button", { name: "Selecionar projeção de data" }));
    fireEvent.click(screen.getByRole("button", { name: "Projetar data" }));

    await waitFor(() => expect(analyzeFireMock).toHaveBeenCalledTimes(1));
    expect(analyzeFireMock).toHaveBeenCalledWith({
      analysis_type: "PROJECTED_DATE",
      as_of_date: "2026-10-23",
      target_wealth: "1000000.00",
    });
    expect(await screen.findByText("Resultado FIRE certificado")).toBeTruthy();
  });

  it("exposes navigation without carrying the Wealth Home month into FIRE", () => {
    render(<FirePage />);

    expect(screen.getByRole("link", { name: "Visão Geral" }).getAttribute("href")).toBe(
      "/wealth-intelligence",
    );
    expect(screen.getByRole("link", { name: "Planejamento" }).getAttribute("href")).toBe(
      "/wealth-intelligence/planning?intent=simulate",
    );
  });
});
