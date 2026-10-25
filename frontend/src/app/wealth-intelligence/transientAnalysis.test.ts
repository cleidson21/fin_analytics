import { describe, expect, it } from "vitest";

import type { FireAnalysisResponse } from "@/lib/fire";
import type { GoalPlanningResponse, ScenarioComparisonResponse } from "@/lib/planning";

import { isSelectableAnalysis, type TransientAnalysisCandidate } from "./transientAnalysis";

describe("transient analysis validation", () => {
  it("rejects incomplete FIRE mode responses", () => {
    const result = {
      analysis_type: "PROJECTED_DATE",
      projection: null,
      required_contribution: null,
    } as FireAnalysisResponse;
    expect(isSelectableAnalysis({ domain: "FIRE", kind: "FIRE_ANALYSIS", result })).toBe(false);
  });

  it.each(["INSUFFICIENT_DATA", "NOT_APPLICABLE"] as const)(
    "rejects a Goal analysis with status %s",
    (status) => {
      const result = {
        status,
        initial_wealth_fact: null,
        target_achievement_result: null,
      } as GoalPlanningResponse;
      expect(isSelectableAnalysis({ domain: "PLANNING", kind: "GOAL", result })).toBe(false);
    },
  );

  it("rejects an incomplete comparison", () => {
    const result = { entries: [{}] } as ScenarioComparisonResponse;
    expect(isSelectableAnalysis({ domain: "PLANNING", kind: "COMPARISON", result })).toBe(false);
  });

  it("accepts a response kind without inventing a new financial result", () => {
    const candidate = {
      domain: "PLANNING",
      kind: "PROJECTION",
      result: {},
    } as TransientAnalysisCandidate;
    expect(isSelectableAnalysis(candidate)).toBe(true);
  });
});
