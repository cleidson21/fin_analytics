import { describe, expect, it } from "vitest";

import {
  THEME_BOOTSTRAP_SCRIPT,
  THEME_STORAGE_KEY,
  isThemePreference,
  resolveTheme,
} from "./theme";

describe("theme contract", () => {
  it("accepts only the three approved visual preferences", () => {
    expect(isThemePreference("system")).toBe(true);
    expect(isThemePreference("light")).toBe(true);
    expect(isThemePreference("dark")).toBe(true);
    expect(isThemePreference("auto")).toBe(false);
    expect(isThemePreference(null)).toBe(false);
  });

  it("resolves System without changing explicit choices", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
  });

  it("bootstraps only the approved appearance key", () => {
    expect(THEME_STORAGE_KEY).toBe("fin_theme");
    expect(THEME_BOOTSTRAP_SCRIPT).toContain("fin_theme");
    expect(THEME_BOOTSTRAP_SCRIPT).not.toMatch(/scenario|wealth|result|amount|goal/i);
  });
});
