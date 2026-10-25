import { requestFromAPI } from "@/lib/api";

export type WealthHomeAvailability =
  | "AVAILABLE"
  | "UNAVAILABLE"
  | "INSUFFICIENT_DATA";

export type WealthHomeFreshness =
  | "CURRENT"
  | "PARTIAL_PERIOD"
  | "CLOSED_PERIOD"
  | "UNKNOWN";

export type WealthHomeCompleteness = "COMPLETE" | "PARTIAL" | "UNKNOWN";

export interface WealthHomeSourceReadModel {
  authority: "FINANCIAL_HEALTH" | "GOALS" | "INVESTMENT_PORTFOLIO";
  reader: string;
  version: string;
  scope: string;
  read_at: string;
  updated_at: string | null;
  freshness: WealthHomeFreshness;
  completeness: WealthHomeCompleteness;
}

export interface WealthHomeHealthReadModel {
  status: WealthHomeAvailability;
  reference_month: string;
  currency: "BRL";
  net_cashflow: string | null;
  reason: string | null;
  source: WealthHomeSourceReadModel;
}

export interface WealthHomeGoalStatusCountReadModel {
  status: "ACTIVE" | "ACHIEVED" | "PAUSED" | "CANCELLED";
  count: number;
}

export interface WealthHomeGoalsReadModel {
  status: WealthHomeAvailability;
  total_count: number;
  by_status: readonly WealthHomeGoalStatusCountReadModel[];
  reason: string | null;
  source: WealthHomeSourceReadModel;
}

export interface WealthHomeInvestmentsReadModel {
  status: WealthHomeAvailability;
  requested_reference_month: string;
  snapshot_reference_month: string | null;
  currency: "BRL";
  investment_wealth: string | null;
  source_type: "MYPROFIT_EVOLUCAO" | null;
  portfolio_scope: string | null;
  run_id: string | null;
  reason: string | null;
  source: WealthHomeSourceReadModel;
}

export interface WealthHomeReadModel {
  contract_version: "wealth-home-v2";
  status: WealthHomeAvailability;
  reference_month: string;
  scope: "AUTHENTICATED_SINGLE_USER";
  generated_at: string;
  health: WealthHomeHealthReadModel;
  goals: WealthHomeGoalsReadModel;
  investments: WealthHomeInvestmentsReadModel;
}

export function getCurrentReferenceMonth(now = new Date()): string {
  const year = String(now.getFullYear()).padStart(4, "0");
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export type ReferenceMonthIssue = "INVALID" | "FUTURE" | null;

export interface ResolvedReferenceMonth {
  month: string;
  issue: ReferenceMonthIssue;
}

export function resolveReferenceMonth(
  candidate: string | null,
  now = new Date(),
): ResolvedReferenceMonth {
  const currentMonth = getCurrentReferenceMonth(now);
  if (candidate === null) return { month: currentMonth, issue: null };

  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(candidate);
  if (!match || Number(match[1]) < 1) {
    return { month: currentMonth, issue: "INVALID" };
  }
  if (candidate > currentMonth) {
    return { month: currentMonth, issue: "FUTURE" };
  }
  return { month: candidate, issue: null };
}

const pendingReads = new Map<string, Promise<WealthHomeReadModel>>();

export function loadWealthHome(referenceMonth: string): Promise<WealthHomeReadModel> {
  const pending = pendingReads.get(referenceMonth);
  if (pending) return pending;

  const request = requestFromAPI<WealthHomeReadModel>(
    `/wealth-home?reference_month=${encodeURIComponent(referenceMonth)}`,
  );
  pendingReads.set(referenceMonth, request);
  const clearPending = () => {
    if (pendingReads.get(referenceMonth) === request) {
      pendingReads.delete(referenceMonth);
    }
  };
  void request.then(clearPending, clearPending);
  return request;
}
