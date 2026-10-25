// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TransientAnalysisCandidate } from "../transientAnalysis";

const pushMock = vi.hoisted(() => vi.fn());
const selectAnalysisMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: pushMock }) }));
vi.mock("../TransientAnalysisContext", () => ({
  useTransientAnalysis: () => ({ selectAnalysis: selectAnalysisMock }),
}));

import { ShowOnWealthHomeButton } from "./ShowOnWealthHomeButton";

const validAnalysis = {
  domain: "PLANNING",
  kind: "PROJECTION",
  result: {},
} as TransientAnalysisCandidate;

afterEach(() => cleanup());

beforeEach(() => {
  pushMock.mockReset();
  selectAnalysisMock.mockReset();
  selectAnalysisMock.mockReturnValue(true);
});

describe("ShowOnWealthHomeButton", () => {
  it("selects the existing response and navigates without an API call", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<ShowOnWealthHomeButton analysis={validAnalysis} />);

    fireEvent.click(screen.getByRole("button", { name: /Mostrar na Visão Geral/i }));

    expect(selectAnalysisMock).toHaveBeenCalledWith(validAnalysis);
    expect(pushMock).toHaveBeenCalledWith("/wealth-intelligence");
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("does not navigate when authorization context rejects the selection", () => {
    selectAnalysisMock.mockReturnValue(false);
    render(<ShowOnWealthHomeButton analysis={validAnalysis} />);

    fireEvent.click(screen.getByRole("button", { name: /Mostrar na Visão Geral/i }));

    expect(pushMock).not.toHaveBeenCalled();
  });

  it("does not expose an action for an incomplete response", () => {
    const invalid = {
      domain: "FIRE",
      kind: "FIRE_ANALYSIS",
      result: { analysis_type: "PROJECTED_DATE", projection: null, required_contribution: null },
    } as TransientAnalysisCandidate;
    render(<ShowOnWealthHomeButton analysis={invalid} />);
    expect(screen.queryByRole("button", { name: /Mostrar na Visão Geral/i })).toBeNull();
  });
});
