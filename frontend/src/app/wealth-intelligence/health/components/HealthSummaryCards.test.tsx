// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { CashflowSummary, FinancialTrendResponse } from "../types";
import { HealthSummaryCards } from "./HealthSummaryCards";

const cashflow: CashflowSummary = {
  reference_month: "2026-10",
  total_income: "10000.00",
  total_expense: "4000.00",
  net_cashflow: "6000.00",
  savings_amount: "6000.00",
  savings_rate: "0.60",
  average_monthly_income: null,
  average_monthly_expense: null,
  average_monthly_net_cashflow: null,
};

const trends: FinancialTrendResponse = {
  requested_reference_month: "2026-10",
  trend_target_month: "2026-09",
  comparison_month: "2026-08",
  status: "OK",
  global: {
    status: "OK",
    metrics: [
      {
        metric: "total_expense",
        current_value: "4000.00",
        previous_value: "5000.00",
        absolute_delta: "-1000.00",
        percentage_delta: "-0.20",
        direction: "DECREASED",
      },
    ],
  },
  categories: { status: "OK", items: [] },
};

afterEach(() => cleanup());

describe("HealthSummaryCards", () => {
  it("presents a certified direction without judging a negative expense delta as bad", () => {
    render(<HealthSummaryCards cashflow={cashflow} trends={trends} />);

    const delta = screen.getByText("-R$ 1.000,00");
    expect(delta.className).toContain("text-foreground/90");
    expect(delta.className).not.toContain("text-rose-300");
    expect(screen.getByText("-20,00%")).toBeTruthy();
  });
});
