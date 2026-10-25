import { beforeEach, describe, expect, it, vi } from "vitest";

const requestFromAPIMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({ requestFromAPI: requestFromAPIMock }));

import { getCurrentReferenceMonth, loadWealthHome, resolveReferenceMonth } from "./wealthHome";

const NOW = new Date(2026, 9, 22, 12, 0, 0);

beforeEach(() => requestFromAPIMock.mockReset());

describe("Wealth Home reference month", () => {
  it("uses local calendar fields rather than UTC conversion", () => {
    expect(getCurrentReferenceMonth(NOW)).toBe("2026-10");
  });

  it("accepts current and past YYYY-MM values", () => {
    expect(resolveReferenceMonth("2026-10", NOW)).toEqual({ month: "2026-10", issue: null });
    expect(resolveReferenceMonth("2025-12", NOW)).toEqual({ month: "2025-12", issue: null });
  });

  it.each(["2026-00", "2026-13", "26-10", "0000-01", "texto"])(
    "falls back safely for invalid month %s",
    (month) => {
      expect(resolveReferenceMonth(month, NOW)).toEqual({ month: "2026-10", issue: "INVALID" });
    },
  );

  it("rejects a future month and defaults a missing month", () => {
    expect(resolveReferenceMonth("2026-11", NOW)).toEqual({ month: "2026-10", issue: "FUTURE" });
    expect(resolveReferenceMonth(null, NOW)).toEqual({ month: "2026-10", issue: null });
  });

  it("deduplicates simultaneous reads for the same month", async () => {
    const response = { contract_version: "wealth-home-v2" };
    requestFromAPIMock.mockResolvedValue(response);

    const first = loadWealthHome("2026-10");
    const second = loadWealthHome("2026-10");

    expect(second).toBe(first);
    expect(requestFromAPIMock).toHaveBeenCalledTimes(1);
    await expect(first).resolves.toBe(response);
  });
});
