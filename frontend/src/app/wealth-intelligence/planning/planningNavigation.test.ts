import { describe, expect, it } from "vitest";

import { buildPlanningHref, resolvePlanningRoute } from "./planningNavigation";

describe("Planning route state", () => {
  it("uses the simulation intention when the URL has no view state", () => {
    expect(resolvePlanningRoute(new URLSearchParams())).toEqual({
      intention: "simulate",
      objectiveMode: "target",
      goalId: null,
      needsNormalization: true,
    });
  });

  it("restores an objective task from a direct URL", () => {
    expect(resolvePlanningRoute(new URLSearchParams("intent=objective&task=goals"))).toEqual({
      intention: "objective",
      objectiveMode: "goals",
      goalId: null,
      needsNormalization: false,
    });
  });

  it("rejects invalid states without carrying an unrelated task", () => {
    expect(resolvePlanningRoute(new URLSearchParams("intent=invalid&task=goals"))).toEqual({
      intention: "simulate",
      objectiveMode: "goals",
      goalId: null,
      needsNormalization: true,
    });
  });

  it("preserves unrelated parameters and removes task outside Objective", () => {
    const params = new URLSearchParams("intent=objective&task=required&from=home");

    expect(buildPlanningHref("/wealth-intelligence/planning", params, "compare")).toBe(
      "/wealth-intelligence/planning?intent=compare&from=home",
    );
    expect(buildPlanningHref("/wealth-intelligence/planning", params, "objective", "goals")).toBe(
      "/wealth-intelligence/planning?intent=objective&task=goals&from=home",
    );
  });

  it("accepts only a UUID Goal identifier on the Goal objective route", () => {
    const goalId = "ABCDEFAB-1234-5678-90AB-ABCDEFABCDEF";

    expect(resolvePlanningRoute(new URLSearchParams(
      `intent=objective&task=goals&goal=${goalId}`,
    ))).toEqual({
      intention: "objective",
      objectiveMode: "goals",
      goalId: goalId.toLowerCase(),
      needsNormalization: false,
    });
    expect(resolvePlanningRoute(new URLSearchParams(
      "intent=objective&task=goals&goal=not-a-uuid",
    ))).toEqual({
      intention: "objective",
      objectiveMode: "goals",
      goalId: null,
      needsNormalization: true,
    });
  });

  it("removes Goal identity outside the Goal objective without adding financial data", () => {
    const params = new URLSearchParams(
      "intent=objective&task=goals&goal=abcdefab-1234-5678-90ab-abcdefabcdef",
    );

    expect(buildPlanningHref("/wealth-intelligence/planning", params, "simulate")).toBe(
      "/wealth-intelligence/planning?intent=simulate",
    );
    expect(buildPlanningHref(
      "/wealth-intelligence/planning",
      new URLSearchParams("intent=objective&task=goals"),
      "objective",
      "goals",
      "abcdefab-1234-5678-90ab-abcdefabcdef",
    )).toBe(
      "/wealth-intelligence/planning?intent=objective&task=goals&goal=abcdefab-1234-5678-90ab-abcdefabcdef",
    );
  });
});
