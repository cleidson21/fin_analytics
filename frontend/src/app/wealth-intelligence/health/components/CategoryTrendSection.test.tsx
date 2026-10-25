// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { FinancialTrendResponse } from "../types";
import { CategoryTrendSection } from "./CategoryTrendSection";

const trends: FinancialTrendResponse = {
  requested_reference_month: "2026-10",
  trend_target_month: "2026-09",
  comparison_month: "2026-08",
  status: "OK",
  global: { status: "OK", metrics: [] },
  categories: {
    status: "OK",
    items: [
      {
        category: "Mercado",
        current_expense: "300.00",
        previous_expense: "500.00",
        absolute_delta: "-200.00",
        percentage_delta: "-0.40",
        direction: "DECREASED",
      },
    ],
  },
};

afterEach(() => cleanup());

describe("CategoryTrendSection", () => {
  it("keeps certified category deltas neutral and exposes the factual direction", () => {
    render(<CategoryTrendSection trends={trends} />);

    expect(screen.getByText("Reduziu")).toBeTruthy();
    const absoluteDelta = screen.getByText("-R$ 200,00");
    const relativeDelta = screen.getByText("-40,00%");
    expect(absoluteDelta.className).toContain("text-foreground/90");
    expect(relativeDelta.className).toContain("text-foreground/90");
  });
});
