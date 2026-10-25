export const THEME_STORAGE_KEY = "fin_theme";
export const SYSTEM_DARK_QUERY = "(prefers-color-scheme: dark)";

export const THEME_PREFERENCES = ["system", "light", "dark"] as const;

export type ThemePreference = (typeof THEME_PREFERENCES)[number];
export type ResolvedTheme = "light" | "dark";

export function isThemePreference(value: unknown): value is ThemePreference {
  return typeof value === "string"
    && THEME_PREFERENCES.includes(value as ThemePreference);
}

export function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean,
): ResolvedTheme {
  if (preference === "system") {
    return systemPrefersDark ? "dark" : "light";
  }
  return preference;
}

export const THEME_BOOTSTRAP_SCRIPT = `(() => {
  try {
    const stored = window.localStorage.getItem("${THEME_STORAGE_KEY}");
    const preference = stored === "light" || stored === "dark" || stored === "system"
      ? stored
      : "system";
    const resolved = preference === "system"
      ? (window.matchMedia("${SYSTEM_DARK_QUERY}").matches ? "dark" : "light")
      : preference;
    const root = document.documentElement;
    root.classList.toggle("dark", resolved === "dark");
    root.dataset.theme = resolved;
    root.dataset.themePreference = preference;
  } catch {}
})();`;
