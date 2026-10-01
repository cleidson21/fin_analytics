import { describe, expect, it } from "vitest";
import { buildFireRequest, createFireForm, normalizeFireMode } from "./fireForm";

const submittedAt = new Date("2026-09-30T12:00:00.000Z");
function valid() { return { ...createFireForm(), source: "USER_PROVIDED_SCENARIO" as const, wealth: "R$ 1.000,50", spending: "5.000", withdrawalRate: "4" }; }

describe("FIRE request builder", () => {
  it("builds summary without projection fields", () => {
    expect(buildFireRequest(valid(), submittedAt)).toEqual({ analysis_type: "SUMMARY", as_of_date: "2026-09-30", initial_wealth: { source: "USER_PROVIDED_SCENARIO", amount: "1000.50", observed_at: submittedAt.toISOString() }, monthly_retirement_spending: "5000.00", assumed_annual_withdrawal_rate: "0.04" });
  });
  it("builds projected real without inflation or desired date", () => {
    const input = { ...valid(), mode: "PROJECTED_DATE" as const, source: "INVESTMENT_PORTFOLIO_SNAPSHOT" as const, contribution: "1.000", expectedReturn: "3,5", horizon: "120" };
    expect(buildFireRequest(input, submittedAt)).toEqual({ analysis_type: "PROJECTED_DATE", as_of_date: "2026-09-30", initial_wealth: { source: "INVESTMENT_PORTFOLIO_SNAPSHOT" }, monthly_retirement_spending: "5000.00", assumed_annual_withdrawal_rate: "0.04", scenario_monthly_contribution: "1000.00", expected_return_rate: "0.035", return_type: "REAL", horizon_months: 120 });
  });
  it("builds projected nominal with inflation", () => {
    const input = { ...valid(), mode: "PROJECTED_DATE" as const, contribution: "0", expectedReturn: "4", horizon: "12", returnType: "NOMINAL" as const, inflation: "0,5" };
    expect(buildFireRequest(input, submittedAt)).toMatchObject({ return_type: "NOMINAL", expected_return_rate: "0.04", inflation_rate: "0.005" });
  });
  it("builds required contribution without contribution or horizon", () => {
    const input = { ...valid(), mode: "REQUIRED_CONTRIBUTION" as const, expectedReturn: "4", desiredDate: "30/09/2036" };
    expect(buildFireRequest(input, submittedAt)).toEqual(expect.objectContaining({ analysis_type: "REQUIRED_CONTRIBUTION", desired_fire_date: "2036-09-30", return_type: "REAL" }));
  });
  it("normalizes incompatible mode fields", () => {
    const projected = { ...valid(), mode: "PROJECTED_DATE" as const, contribution: "100", horizon: "120", expectedReturn: "4", inflation: "3", desiredDate: "01/01/2030" };
    expect(normalizeFireMode(projected, "REQUIRED_CONTRIBUTION")).toMatchObject({ contribution: "", horizon: "", desiredDate: "01/01/2030" });
    expect(normalizeFireMode(projected, "SUMMARY")).toMatchObject({ contribution: "", horizon: "", expectedReturn: "", inflation: "", desiredDate: "" });
  });
  it("rejects dot money and invalid date", () => {
    expect(() => buildFireRequest({ ...valid(), spending: "1000.50" }, submittedAt)).toThrow();
    expect(() => buildFireRequest({ ...valid(), mode: "REQUIRED_CONTRIBUTION", expectedReturn: "4", desiredDate: "31/02/2036" }, submittedAt)).toThrow();
  });
});
