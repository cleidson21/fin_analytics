import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchFromAPIMock = vi.hoisted(() => vi.fn());
const requestFromAPIMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({
  fetchFromAPI: fetchFromAPIMock,
  requestFromAPI: requestFromAPIMock,
}));

import { getPlanningGoalContext, projectGoal } from "./planning";

beforeEach(() => {
  fetchFromAPIMock.mockReset();
  requestFromAPIMock.mockReset();
});

describe("Planning authenticated client", () => {
  it("loads Goal context through the shared authenticated GET client", async () => {
    const response = {
      goal_id: "abcdefab-1234-5678-90ab-abcdefabcdef",
      name: "Reserva",
      goal_type: "EMERGENCY_RESERVE",
      status: "ACTIVE",
      target_amount: "50000.00",
      current_amount: "0.00",
      planned_monthly_contribution: null,
      target_date: null,
    };
    requestFromAPIMock.mockResolvedValue(response);

    await expect(getPlanningGoalContext(response.goal_id)).resolves.toBe(response);
    expect(requestFromAPIMock).toHaveBeenCalledWith(
      `/planning/goals/${response.goal_id}/context`,
    );
    expect(fetchFromAPIMock).not.toHaveBeenCalled();
  });

  it("keeps the existing Goal projection as an explicit POST", async () => {
    const request = {
      initial_wealth: { source: "GOAL_CURRENT_AMOUNT" as const },
      assumptions: {
        as_of_date: "2026-10-26",
        scenario_monthly_contribution: "750.00",
        expected_return_rate: "0.08",
        return_type: "NOMINAL" as const,
        output_mode: "NOMINAL" as const,
        inflation_rate: null,
        horizon_months: 24,
        target_date: null,
        rate_basis: "EFFECTIVE_ANNUAL" as const,
        contribution_timing: "END_OF_MONTH" as const,
      },
      target_value_basis: null,
    };

    await projectGoal("abcdefab-1234-5678-90ab-abcdefabcdef", request);

    expect(fetchFromAPIMock).toHaveBeenCalledWith(
      "/planning/goals/abcdefab-1234-5678-90ab-abcdefabcdef/projection",
      { method: "POST", body: JSON.stringify(request) },
    );
  });
});
