"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  SYSTEM_DARK_QUERY,
  THEME_STORAGE_KEY,
  isThemePreference,
  resolveTheme,
  type ResolvedTheme,
  type ThemePreference,
} from "@/lib/theme";

type ThemeContextValue = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  hydrated: boolean;
  setPreference: (preference: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function applyTheme(preference: ThemePreference, systemPrefersDark: boolean) {
  const resolved = resolveTheme(preference, systemPrefersDark);
  const root = document.documentElement;
  root.classList.toggle("dark", resolved === "dark");
  root.dataset.theme = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
  return resolved;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>("system");
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("light");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    const initialPreference = isThemePreference(stored) ? stored : "system";
    const media = window.matchMedia(SYSTEM_DARK_QUERY);

    setPreferenceState(initialPreference);
    setResolvedTheme(applyTheme(initialPreference, media.matches));
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    const media = window.matchMedia(SYSTEM_DARK_QUERY);
    const syncSystemTheme = (event: MediaQueryListEvent) => {
      if (preference === "system") {
        setResolvedTheme(applyTheme("system", event.matches));
      }
    };

    setResolvedTheme(applyTheme(preference, media.matches));
    media.addEventListener("change", syncSystemTheme);
    return () => media.removeEventListener("change", syncSystemTheme);
  }, [hydrated, preference]);

  const setPreference = useCallback((nextPreference: ThemePreference) => {
    window.localStorage.setItem(THEME_STORAGE_KEY, nextPreference);
    setPreferenceState(nextPreference);
    setResolvedTheme(
      applyTheme(nextPreference, window.matchMedia(SYSTEM_DARK_QUERY).matches),
    );
  }, []);

  const value = useMemo(
    () => ({ preference, resolvedTheme, hydrated, setPreference }),
    [hydrated, preference, resolvedTheme, setPreference],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
