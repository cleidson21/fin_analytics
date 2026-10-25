import { describe, expect, it } from "vitest";

import { buildPlanningHref, resolvePlanningRoute } from "./planningNavigation";

describe("Planning route state", () => {
  it("uses the simulation intention when the URL has no view state", () => {
    expect(resolvePlanningRoute(new URLSearchParams())).toEqual({
      intention: "simulate",
      objectiveMode: "target",
      needsNormalization: true,
    });
  });

  it("restores an objective task from a direct URL", () => {
    expect(resolvePlanningRoute(new URLSearchParams("intent=objective&task=goals"))).toEqual({
      intention: "objective",
      objectiveMode: "goals",
      needsNormalization: false,
    });
  });

  it("rejects invalid states without carrying an unrelated task", () => {
    expect(resolvePlanningRoute(new URLSearchParams("intent=invalid&task=goals"))).toEqual({
      intention: "simulate",
      objectiveMode: "goals",
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
});
