import { describe, expect, it } from "vitest";

import {
  SECTION_TABS,
  SIDEBAR_NAV,
  buildPeriodAwareTabHref,
  getTabsForPath,
  isNavigationTabActive,
  isSidebarNavigationActive,
} from "./navigation";

const wealthHrefs = SECTION_TABS.wealthIntelligence.map((tab) => tab.href);

describe("Inteligência Patrimonial navigation", () => {
  it("defines the localized hierarchy and canonical Goals route", () => {
    expect(SECTION_TABS.wealthIntelligence.map(({ name, href }) => ({ name, href }))).toEqual([
      { name: "Visão geral", href: "/wealth-intelligence" },
      { name: "Metas", href: "/wealth-intelligence/goals" },
      { name: "Saúde Financeira", href: "/wealth-intelligence/health" },
      { name: "Planejamento", href: "/wealth-intelligence/planning" },
      { name: "Independência Financeira", href: "/wealth-intelligence/fire" },
    ]);
  });

  it.each([
    ["/wealth-intelligence", "/wealth-intelligence"],
    ["/wealth-intelligence/goals", "/wealth-intelligence/goals"],
    ["/wealth-intelligence/health", "/wealth-intelligence/health"],
    ["/wealth-intelligence/planning", "/wealth-intelligence/planning"],
    ["/wealth-intelligence/fire", "/wealth-intelligence/fire"],
  ])("activates only the expected tab for %s", (pathname, expected) => {
    expect(getTabsForPath(pathname)).toBe(SECTION_TABS.wealthIntelligence);
    const active = wealthHrefs.filter((href) => isNavigationTabActive(pathname, href, wealthHrefs));
    expect(active).toEqual([expected]);
  });

  it.each([
    "/wealth-intelligence",
    "/wealth-intelligence/goals",
    "/wealth-intelligence/health",
    "/wealth-intelligence/planning",
    "/wealth-intelligence/fire",
    "/goals",
  ])("keeps only Inteligência Patrimonial active in the sidebar for %s", (pathname) => {
    const active = SIDEBAR_NAV.filter((item) =>
      isSidebarNavigationActive(pathname, item.href),
    ).map((item) => item.name);
    expect(active).toEqual(["Inteligência Patrimonial"]);
  });

  it("maps the legacy route to the canonical Goals tab while the redirect resolves", () => {
    const active = wealthHrefs.filter((href) => isNavigationTabActive("/goals", href, wealthHrefs));
    expect(active).toEqual(["/wealth-intelligence/goals"]);
  });

  it("preserves the current query only between Wealth Home and Health", () => {
    const params = new URLSearchParams("month=2026-09&view=compact");
    expect(
      buildPeriodAwareTabHref(
        "/wealth-intelligence",
        "/wealth-intelligence/health",
        params,
      ),
    ).toBe("/wealth-intelligence/health?month=2026-09&view=compact");
    expect(
      buildPeriodAwareTabHref(
        "/wealth-intelligence/health",
        "/wealth-intelligence",
        params,
      ),
    ).toBe("/wealth-intelligence?month=2026-09&view=compact");
    expect(
      buildPeriodAwareTabHref(
        "/wealth-intelligence",
        "/wealth-intelligence/goals",
        params,
      ),
    ).toBe("/wealth-intelligence/goals");
  });
});
