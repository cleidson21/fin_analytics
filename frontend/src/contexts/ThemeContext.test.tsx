// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";
import { THEME_STORAGE_KEY } from "@/lib/theme";

import { ThemeProvider, useTheme } from "./ThemeContext";

let systemDark = false;
const listeners = new Set<(event: MediaQueryListEvent) => void>();

function emitSystemTheme(matches: boolean) {
  systemDark = matches;
  listeners.forEach((listener) => listener({ matches } as MediaQueryListEvent));
}

function Probe() {
  const { preference, resolvedTheme, hydrated } = useTheme();
  return <output>{`${preference}:${resolvedTheme}:${hydrated}`}</output>;
}

beforeEach(() => {
  systemDark = false;
  listeners.clear();
  window.localStorage.clear();
  document.documentElement.className = "";
  delete document.documentElement.dataset.theme;
  delete document.documentElement.dataset.themePreference;
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn(() => ({
      matches: systemDark,
      media: "(prefers-color-scheme: dark)",
      onchange: null,
      addEventListener: (_type: string, listener: (event: MediaQueryListEvent) => void) => listeners.add(listener),
      removeEventListener: (_type: string, listener: (event: MediaQueryListEvent) => void) => listeners.delete(listener),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

afterEach(() => cleanup());

describe("ThemeProvider", () => {
  it("hydrates a stored dark preference without persisting any other state", async () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");

    render(
      <ThemeProvider>
        <Probe />
        <ThemeSwitcher />
      </ThemeProvider>,
    );

    await waitFor(() => expect(screen.getByText("dark:dark:true")).toBeTruthy());
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage).toHaveLength(1);
  });

  it("changes Light, Dark and System explicitly and follows system changes", async () => {
    render(
      <ThemeProvider>
        <Probe />
        <ThemeSwitcher compact />
      </ThemeProvider>,
    );

    await waitFor(() => expect(screen.getByText("system:light:true")).toBeTruthy());
    fireEvent.click(screen.getByRole("radio", { name: "Usar tema escuro" }));
    expect(screen.getByText("dark:dark:true")).toBeTruthy();
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");

    fireEvent.click(screen.getByRole("radio", { name: "Usar tema claro" }));
    expect(screen.getByText("light:light:true")).toBeTruthy();
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    fireEvent.click(screen.getByRole("radio", { name: "Usar tema do sistema" }));
    emitSystemTheme(true);
    await waitFor(() => expect(screen.getByText("system:dark:true")).toBeTruthy());
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(window.localStorage).toHaveLength(1);
  });

  it("rejects an invalid stored value and safely returns to System", async () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "financial-scenario");
    systemDark = true;

    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );

    await waitFor(() => expect(screen.getByText("system:dark:true")).toBeTruthy());
    expect(document.documentElement.dataset.themePreference).toBe("system");
  });

  it("supports the radiogroup arrow-key interaction", async () => {
    render(
      <ThemeProvider>
        <Probe />
        <ThemeSwitcher />
      </ThemeProvider>,
    );

    const systemOption = await screen.findByRole("radio", { name: "Usar tema do sistema" });
    systemOption.focus();
    fireEvent.keyDown(systemOption, { key: "ArrowLeft" });

    expect(screen.getByText("dark:dark:true")).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Usar tema escuro" }).getAttribute("tabindex")).toBe("0");
    expect(document.activeElement).toBe(screen.getByRole("radio", { name: "Usar tema escuro" }));
  });
});
