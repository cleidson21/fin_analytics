// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { GoalBudgetPreviewRequest } from "./planning";
import fixture from "@/app/wealth-intelligence/planning/components/goalBudgetFixture.json";

vi.stubEnv("NEXT_PUBLIC_API_URL", "https://example.test/api/v1");
const { previewGoalBudget } = await import("./planning");
const { APIRequestError, AuthError } = await import("./api");

const request: GoalBudgetPreviewRequest = {
  goal_ids: fixture.results.map((item) => item.goal_id), monthly_budget: "100",
  assumptions: { as_of_date: "2026-10-28", expected_return_rate: "0", return_type: "NOMINAL", output_mode: "NOMINAL", horizon_months: 2, rate_basis: "EFFECTIVE_ANNUAL", contribution_timing: "END_OF_MONTH" },
  target_value_basis: "NOMINAL", scenarios: [
    { scenario_id: "A", allocations: fixture.scenarios[0].allocations },
    { scenario_id: "B", allocations: fixture.scenarios[1].allocations },
  ],
};

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("fin_token", "synthetic-token");
  vi.restoreAllMocks();
});
afterEach(() => vi.unstubAllGlobals());

describe("Goal budget authenticated HTTP client", () => {
  it("sends only the exact body and bearer header and preserves certified strings", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixture), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const signal = new AbortController().signal;
    const response = await previewGoalBudget(request, signal);
    expect(response).toEqual(fixture);
    expect(fetchMock).toHaveBeenCalledWith("https://example.test/api/v1/planning/goals/budget-preview", {
      method: "POST", body: JSON.stringify(request), signal,
      headers: { "Content-Type": "application/json", Authorization: "Bearer synthetic-token" }, cache: "no-store",
    });
  });

  it.each([404, 422, 500])("preserves HTTP %s for the UI without swallowing it", async (status) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status })));
    await expect(previewGoalBudget(request)).rejects.toMatchObject({ status, name: "APIRequestError" });
    expect(new APIRequestError(status, "test").status).toBe(status);
  });

  it("propagates network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Network unavailable")));
    await expect(previewGoalBudget(request)).rejects.toThrow("Network unavailable");
  });

  it("handles a current-session 401 through the existing authentication boundary", async () => {
    const location = { href: "" };
    vi.stubGlobal("window", { location });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 401 })));
    await expect(previewGoalBudget(request)).rejects.toBeInstanceOf(AuthError);
    expect(localStorage.getItem("fin_token")).toBeNull();
    expect(location.href).toBe("/login");
  });

  it("does not let an old 401 remove a replacement session", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => {
      localStorage.setItem("fin_token", "replacement-token");
      return new Response("{}", { status: 401 });
    }));
    await expect(previewGoalBudget(request, new AbortController().signal)).rejects.toMatchObject({ name: "AbortError" });
    expect(localStorage.getItem("fin_token")).toBe("replacement-token");
  });

  it("ignores an aborted response even if a transport resolves it late", async () => {
    const controller = new AbortController();
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => {
      controller.abort();
      return new Response("{}", { status: 401 });
    }));
    await expect(previewGoalBudget(request, controller.signal)).rejects.toMatchObject({ name: "AbortError" });
    expect(localStorage.getItem("fin_token")).toBe("synthetic-token");
  });
});
