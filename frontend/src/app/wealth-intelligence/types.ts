export type WealthHomePreviewState = "success" | "loading" | "empty" | "error";

export type WealthHomeMetricTone = "emerald" | "sky" | "violet" | "amber";

export interface WealthHomeMetric {
  id: string;
  label: string;
  value: string;
  context: string;
  source: string;
  tone: WealthHomeMetricTone;
}

export interface InvestmentWealthPoint {
  period: string;
  value: string;
  visualHeight: string;
}

export interface PortfolioAllocationItem {
  label: string;
  value: string;
  share: string;
  visualWidth: string;
  color: string;
}

export interface AdvisorContextItem {
  label: string;
  value: string;
  provenance: string;
}

export interface WealthHomeFixture {
  fixtureId: string;
  referencePeriod: string;
  scopeLabel: string;
  metrics: readonly WealthHomeMetric[];
  investmentWealthHistory: readonly InvestmentWealthPoint[];
  allocation: readonly PortfolioAllocationItem[];
  advisor: {
    question: string;
    context: readonly AdvisorContextItem[];
    sources: readonly string[];
    response: string;
    limitations: readonly string[];
  };
}
