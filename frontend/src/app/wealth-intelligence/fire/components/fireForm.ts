import {
  formatFinancialInputError,
  formatLocalISODate,
  parseBRDateInput,
  parseBRLMoneyInput,
  parseBRPercentInputToFraction,
} from "@/lib/planningLocale";
import type { DecimalString, ISODateString, ReturnType } from "@/lib/planning";
import type { FireAnalysisRequest, FireAnalysisType, FireInitialWealthSelector } from "@/lib/fire";

export type FireInputField = "wealth" | "spending" | "withdrawalRate" | "contribution" | "expectedReturn" | "inflation" | "horizon" | "desiredDate" | "asOfDate";
export type FireFormState = {
  mode: FireAnalysisType;
  source: FireInitialWealthSelector["source"];
  wealth: string;
  spending: string;
  withdrawalRate: string;
  contribution: string;
  expectedReturn: string;
  returnType: ReturnType;
  inflation: string;
  horizon: string;
  desiredDate: string;
  asOfDate: string;
};

export class FireInputError extends Error {
  constructor(public readonly field: FireInputField, message: string) { super(message); }
}

export function createFireForm(): FireFormState {
  return { mode: "SUMMARY", source: "INVESTMENT_PORTFOLIO_SNAPSHOT", wealth: "", spending: "", withdrawalRate: "", contribution: "", expectedReturn: "", returnType: "REAL", inflation: "", horizon: "", desiredDate: "", asOfDate: "" };
}

function money(value: string, field: FireInputField): DecimalString {
  const parsed = parseBRLMoneyInput(value);
  if (!parsed.ok) throw new FireInputError(field, formatFinancialInputError(parsed.code, "money"));
  return parsed.value;
}

function rate(value: string, field: FireInputField): DecimalString {
  const parsed = parseBRPercentInputToFraction(value);
  if (!parsed.ok) throw new FireInputError(field, formatFinancialInputError(parsed.code, "rate"));
  return parsed.value;
}

function date(value: string, field: FireInputField): ISODateString {
  const parsed = parseBRDateInput(value);
  if (!parsed.ok) throw new FireInputError(field, formatFinancialInputError(parsed.code, "date"));
  return parsed.value;
}

function positiveLessThanOne(value: DecimalString) {
  return !/^0(?:\.0+)?$/.test(value) && !/^-/.test(value) && !/^[1-9]\d*(?:\.\d+)?$/.test(value);
}

function horizon(value: string): number {
  if (!/^\d+$/.test(value)) throw new FireInputError("horizon", "Informe o horizonte em meses.");
  const digits = value.replace(/^0+(?=\d)/, "");
  if (digits.length > 4 || (digits.length === 4 && digits > "1200") || digits === "0") throw new FireInputError("horizon", "Use um horizonte entre 1 e 1200 meses.");
  let total = 0;
  for (const character of digits) total = total * 10 + character.charCodeAt(0) - 48;
  return total;
}

function asOfDate(value: string, submittedAt: Date): ISODateString {
  return value.trim() === "" ? formatLocalISODate(submittedAt) : date(value, "asOfDate");
}

function source(input: FireFormState, submittedAt: Date): FireInitialWealthSelector {
  if (input.source === "INVESTMENT_PORTFOLIO_SNAPSHOT") return { source: "INVESTMENT_PORTFOLIO_SNAPSHOT" };
  return { source: "USER_PROVIDED_SCENARIO", amount: money(input.wealth, "wealth"), observed_at: submittedAt.toISOString() };
}

export function normalizeFireMode(input: FireFormState, mode: FireAnalysisType): FireFormState {
  if (mode === "SUMMARY") return { ...input, mode, contribution: "", expectedReturn: "", inflation: "", horizon: "", desiredDate: "" };
  if (mode === "PROJECTED_DATE") return { ...input, mode, desiredDate: "" };
  return { ...input, mode, contribution: "", horizon: "" };
}

export function buildFireRequest(input: FireFormState, submittedAt: Date): FireAnalysisRequest {
  const withdrawalRate = rate(input.withdrawalRate, "withdrawalRate");
  if (!positiveLessThanOne(withdrawalRate)) throw new FireInputError("withdrawalRate", "Use uma taxa maior que 0% e menor que 100%.");
  const common = { as_of_date: asOfDate(input.asOfDate, submittedAt), initial_wealth: source(input, submittedAt), monthly_retirement_spending: money(input.spending, "spending"), assumed_annual_withdrawal_rate: withdrawalRate };
  if (input.mode === "SUMMARY") return { analysis_type: "SUMMARY", ...common };
  const expected_return_rate = rate(input.expectedReturn, "expectedReturn");
  const inflation_rate = input.returnType === "NOMINAL" ? rate(input.inflation, "inflation") : undefined;
  if (input.mode === "PROJECTED_DATE") return { analysis_type: "PROJECTED_DATE", ...common, scenario_monthly_contribution: money(input.contribution, "contribution"), expected_return_rate, return_type: input.returnType, ...(inflation_rate ? { inflation_rate } : {}), horizon_months: horizon(input.horizon) };
  return { analysis_type: "REQUIRED_CONTRIBUTION", ...common, expected_return_rate, return_type: input.returnType, ...(inflation_rate ? { inflation_rate } : {}), desired_fire_date: date(input.desiredDate, "desiredDate") };
}
