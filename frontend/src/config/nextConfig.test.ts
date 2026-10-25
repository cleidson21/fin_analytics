import { describe, expect, it } from "vitest";

import nextConfig from "../../next.config";

describe("legacy route redirects", () => {
  it("redirects legacy Goals to its canonical Inteligência Patrimonial route", async () => {
    const redirects = await nextConfig.redirects?.();
    expect(redirects).toContainEqual({
      source: "/goals",
      destination: "/wealth-intelligence/goals",
      permanent: false,
    });
  });
});
